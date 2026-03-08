from __future__ import annotations
import asyncio
import logging
from typing import Optional
from backend.engine.bdl import search_players, get_season_averages, get_roster, BDLNotFound
from backend.models.player import PlayerProfile, TeamProfile

logger = logging.getLogger(__name__)


async def find_player(name: str, season: int) -> Optional[PlayerProfile]:
    players = await search_players(name)
    if not players:
        return None

    name_lower = name.lower().replace("-", " ")
    matched = None
    for p in players:
        full = f"{p.get('first_name','')} {p.get('last_name','')}".lower().replace("-", " ")
        if all(part in full for part in name_lower.split()):
            matched = p
            break
    if not matched:
        matched = players[0]

    pid = matched["id"]
    raw_stats = await get_season_averages(pid, season)

    try:
        return PlayerProfile.build(player_data=matched, raw_stats=raw_stats, season=season)
    except Exception as e:
        logger.error("Profile build failed pid=%d: %s", pid, e)
        return None


async def find_team(abbreviation: str, season: int) -> Optional[TeamProfile]:
    try:
        roster_raw = await get_roster(abbreviation, season)
    except BDLNotFound as e:
        logger.error("Team not found: %s", e)
        return None

    if not roster_raw:
        return None

    async def _build(p: dict) -> Optional[PlayerProfile]:
        pid = p.get("id")
        if not pid:
            return None
        try:
            raw_stats = await get_season_averages(pid, season)
            return PlayerProfile.build(player_data=p, raw_stats=raw_stats, season=season)
        except Exception as e:
            logger.warning("Skipping pid=%s: %s", pid, e)
            return None

    results = await asyncio.gather(*[_build(p) for p in roster_raw])
    roster = [p for p in results if p is not None]
    if not roster:
        return None

    team_name = roster[0].identity.team
    return TeamProfile(team=team_name, abbreviation=abbreviation.upper(), season=season, roster=roster)