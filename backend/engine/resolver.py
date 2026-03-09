from __future__ import annotations
import asyncio
import logging
from typing import Optional
from backend.engine.bdl import search_players, get_season_averages, get_roster, BDLNotFound
from backend.models.player import PlayerProfile, TeamProfile

logger = logging.getLogger(__name__)


async def find_player(name: str, season: int) -> Optional[PlayerProfile]:
    players = await search_players(name)
    # ... (keep your existing exact match logic here) ...
    
    if not matched: return None

    pid = matched["id"]
    # Fetch Season Avg and Recent Logs in parallel
    raw_stats, recent_logs = await asyncio.gather(
        get_season_averages(pid, season),
        get_recent_stats(pid, 10)
    )

    # Calculate L10 (Last 10) Averages
    if recent_logs:
        l10_pts = sum(g['pts'] for g in recent_logs) / len(recent_logs)
        l10_ast = sum(g['ast'] for g in recent_logs) / len(recent_logs)
        # Trend calculation: (Recent - Season)
        pts_trend = l10_pts - raw_stats.get('pts', 0)
    else:
        pts_trend = 0

    # Build the profile with the new trend data
    profile = PlayerProfile.build(player_data=matched, raw_stats=raw_stats, season=season)
    
    # Inject Trend and Position Rank into the object for the AI
    profile.momentum = {
        "pts_delta": round(pts_trend, 1),
        "status": "HEATING UP" if pts_trend > 2.5 else ("SLUMPING" if pts_trend < -2.5 else "STABLE")
    }
    
    # Static League Normalization logic (Position-based)
    pos = matched.get("position", "")
    fg = raw_stats.get("fg_pct", 0)
    if "G" in pos: # Guards: 45% is good
        profile.percentile = "ELITE" if fg > 0.48 else "ABOVE AVG" if fg > 0.44 else "BELOW AVG"
    else: # Bigs: 50% is the baseline
        profile.percentile = "ELITE" if fg > 0.58 else "ABOVE AVG" if fg > 0.52 else "BELOW AVG"

    return profile
    
    # 1. Try Exact Match
    for p in players:
        full = f"{p.get('first_name','')} {p.get('last_name','')}".lower().replace("-", " ")
        if name_lower == full:
            matched = p
            break
            
    # 2. Try Partial/Fuzzy Match
    if not matched:
        for p in players:
            full = f"{p.get('first_name','')} {p.get('last_name','')}".lower().replace("-", " ")
            if all(part in full for part in name_lower.split()):
                matched = p
                break
                
    # 3. STRICT REJECTION: No lazy fallbacks. If we didn't match, return None.
    if not matched:
        return None

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