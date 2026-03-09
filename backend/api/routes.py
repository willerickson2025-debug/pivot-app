import asyncio
import httpx
import os
from typing import Optional, Any
from ..engine.cache import cget, cset, make_key
from fastapi import FastAPI
app = FastAPI()
# --- CONFIG & ERRORS ---
BDL_API_BASE = "https://api.balldontlie.io/v1"
API_KEY = os.getenv("BDL_API_KEY")

class BDLNotFound(Exception):
    """Raised when data is missing from the BDL pipeline."""
    pass

async def _get(endpoint: str, params: Optional[dict] = None) -> dict:
    """Core HTTP handler for Balldontlie API calls."""
    headers = {"Authorization": API_KEY} if API_KEY else {}
    async with httpx.AsyncClient(timeout=20.0) as client:
        response = await client.get(f"{BDL_API_BASE}{endpoint}", params=params, headers=headers)
        if response.status_code == 404:
            raise BDLNotFound(f"Resource {endpoint} not found.")
        response.raise_for_status()
        return response.json()

# --- PLAYER DATA ---
async def search_players(query: str) -> list[dict]:
    """Search for players by name."""
    key = make_key("bdl:search", q=query)
    cached = cget(key)
    if cached is not None: return cached
    
    data = await _get("/players", {"search": query})
    result = data.get("data", [])
    cset(key, result, ttl=86400)
    return result

async def get_season_averages(player_id: int, season: int) -> dict:
    """Fetch seasonal stat averages for a specific player."""
    key = make_key("bdl:avg", pid=player_id, s=season)
    cached = cget(key)
    if cached is not None: return cached

    data = await _get("/season_averages", {"season": season, "player_ids[]": [player_id]})
    stats_list = data.get("data", [])
    result = stats_list[0] if stats_list else {}
    cset(key, result, ttl=3600)
    return result

# --- RECENT FORM TRACKING (THE FIX IS HERE) ---
async def get_recent_stats(player_id: int, limit: int = 10) -> list[dict]:
    """Fetches the last X game box scores for a specific player."""
    # Ensure this block is indented properly (4 spaces)
    key = make_key("bdl:recent", pid=player_id, limit=limit)
    cached = cget(key)
    if cached is not None:
        return cached

    # Fetch game logs for the current season
    data = await _get("/stats", {
        "player_ids[]": [player_id],
        "per_page": limit,
        "order_by": "date",
        "direction": "desc"
    })
    
    result = data.get("data", [])
    cset(key, result, ttl=3600) # Cache logs for 1 hour
    return result

# --- TEAM & ROSTER ---
async def get_roster(team_id: int) -> list[dict]:
    """Retrieves current roster for a team."""
    key = make_key("bdl:roster", tid=team_id)
    cached = cget(key)
    if cached is not None: return cached

    data = await _get("/players", {"team_ids[]": [team_id], "per_page": 50})
    result = data.get("data", [])
    cset(key, result, ttl=86400)
    return result