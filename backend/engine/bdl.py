from __future__ import annotations
import asyncio
import logging
from typing import Any, Optional
import httpx
from tenacity import retry, retry_if_exception, stop_after_attempt, wait_exponential_jitter, before_sleep_log, RetryError
from backend.config import get_settings
from backend.engine.cache import cget, cset, make_key

logger = logging.getLogger(__name__)


class BDLError(Exception):
    def __init__(self, msg: str, status: Optional[int] = None):
        super().__init__(msg)
        self.status = status


class BDLNotFound(BDLError):
    pass


def _retryable(exc: BaseException) -> bool:
    if isinstance(exc, (httpx.TimeoutException, httpx.ConnectError)):
        return True
    if isinstance(exc, BDLError) and exc.status in (429, 500, 503, 529):
        return True
    return False


_sem: Optional[asyncio.Semaphore] = None


def _get_sem() -> asyncio.Semaphore:
    global _sem
    if _sem is None:
        _sem = asyncio.Semaphore(get_settings().max_concurrent_bdl_calls)
    return _sem


def _client() -> httpx.AsyncClient:
    s = get_settings()
    headers = {"Authorization": s.bdl_api_key} if s.bdl_api_key else {}
    return httpx.AsyncClient(base_url=s.bdl_base_url, headers=headers, timeout=s.bdl_request_timeout)


async def _get(path: str, params: Any) -> dict:
    s = get_settings()

    @retry(
        retry=retry_if_exception(_retryable),
        stop=stop_after_attempt(s.retry_max_attempts),
        wait=wait_exponential_jitter(initial=s.retry_min_wait_seconds, max=s.retry_max_wait_seconds),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        reraise=False,
    )
    async def _attempt() -> dict:
        async with _get_sem():
            async with _client() as c:
                r = await c.get(path, params=params)
                if r.status_code == 404:
                    raise BDLNotFound(f"404 {path}", status=404)
                if r.status_code == 429:
                    await asyncio.sleep(int(r.headers.get("Retry-After", "5")))
                    raise BDLError("429 rate limit", status=429)
                if r.status_code >= 500:
                    raise BDLError(f"{r.status_code} server error", status=r.status_code)
                if r.status_code >= 400:
                    raise BDLError(f"{r.status_code}: {r.text[:200]}", status=r.status_code)
                r.raise_for_status()
                return r.json()

    try:
        return await _attempt()
    except RetryError as e:
        raise BDLError(f"BDL {path} failed after retries") from e


# ── Public methods ──────────────────────────────────────────────────────────

async def search_players(name: str) -> list[dict]:
    key = make_key("bdl:players", name=name)
    cached = cget(key)
    if cached is not None:
        return cached
    data = await _get("/players", {"search": name.split()[0], "per_page": 25})
    result = data.get("data", [])
    cset(key, result, ttl=get_settings().cache_stats_ttl_seconds)
    return result


async def get_season_averages(player_id: int, season: int) -> dict:
    key = make_key("bdl:avg", player_id=player_id, season=season)
    cached = cget(key)
    if cached is not None:
        return cached
    try:
        data = await _get("/season_averages", {"player_id": player_id, "season": season})
        entries = data.get("data", [])
        result = entries[0] if entries else {}
        cset(key, result, ttl=get_settings().cache_stats_ttl_seconds)
        return result
    except (BDLError, httpx.HTTPStatusError) as e:
        logger.warning("Season averages unavailable for player_id=%d: %s", player_id, e)
        return {}


async def get_team_id_map() -> dict[str, int]:
    key = "bdl:team_map"
    cached = cget(key)
    if cached is not None:
        return cached
    data = await _get("/teams", {"per_page": 100})
    team_map = {t["abbreviation"].upper(): t["id"] for t in data.get("data", []) if t.get("abbreviation")}
    cset(key, team_map, ttl=86400)
    return team_map


async def get_roster(abbreviation: str, season: int) -> list[dict]:
    key = make_key("bdl:roster", team=abbreviation.upper(), season=season)
    cached = cget(key)
    if cached is not None:
        return cached

    team_map = await get_team_id_map()
    abbr = abbreviation.upper()
    if abbr not in team_map:
        raise BDLNotFound(f"Team '{abbr}' not found. Valid: {', '.join(sorted(team_map.keys()))}")

    team_id = team_map[abbr]
    players: list[dict] = []
    cursor = None

    while True:
        params: list = [("team_ids[]", team_id), ("per_page", 100)]
        if cursor:
            params.append(("cursor", cursor))
        data = await _get("/players", params)
        batch = data.get("data", [])
        players.extend(batch)
        cursor = data.get("meta", {}).get("next_cursor")
        if not cursor or not batch:
            break

    cset(key, players, ttl=get_settings().cache_stats_ttl_seconds)
    return players


async def get_games(date: str) -> list[dict]:
    """Get games for a specific date (YYYY-MM-DD)."""
    key = make_key("bdl:games", date=date)
    cached = cget(key)
    if cached is not None:
        return cached
    data = await _get("/games", {"dates[]": date, "per_page": 100})
    result = data.get("data", [])
    cset(key, result, ttl=300)  # 5 min TTL for live games
    return result


async def get_live_games() -> list[dict]:
    """Get today's live games, locked to US time."""
    from datetime import datetime, timedelta
    
    # Offset UTC by 6 hours so evening games don't roll over to 'tomorrow' at 7 PM EST
    today = (datetime.utcnow() - timedelta(hours=6)).date().isoformat()
    return await get_games(today)


async def get_player_game_log(player_id: int, season: int) -> list[dict]:
    """Get game-by-game stats for a player."""
    key = make_key("bdl:gamelog", player_id=player_id, season=season)
    cached = cget(key)
    if cached is not None:
        return cached
    try:
        data = await _get("/stats", {
            "player_ids[]": player_id,
            "seasons[]": season,
            "per_page": 100
        })
        result = data.get("data", [])
        cset(key, result, ttl=get_settings().cache_stats_ttl_seconds)
        return result
    except (BDLError, httpx.HTTPStatusError) as e:
        logger.warning("Game log unavailable: %s", e)
        return []