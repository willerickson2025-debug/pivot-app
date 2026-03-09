from __future__ import annotations
import asyncio
import logging
import httpx
from typing import Optional
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

from backend.config import get_settings
from backend.engine.resolver import find_player, find_team
from backend.engine.bdl import get_live_games, get_player_game_log
from backend.ai.claude import ai_analyze, ai_compare, ai_trade, ai_team, ai_chat, ai_roster_package
from backend.engine.cache import cache_info, cdel_namespace

logger = logging.getLogger(__name__)

app = FastAPI(title="PIVOT NBA Intelligence API", version="3.0.0", docs_url="/api/docs")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=False,
)

class TradeRequest(BaseModel):
    outgoing: list[str]
    incoming: list[str]
    season: int = 2025
    context: str = ""
    force: bool = False

class ChatRequest(BaseModel):
    player: str
    season: int = 2025
    message: str
    history: list[dict] = []

# ── Health & Search ────────────────────────────────────────────────────────

@app.get("/api/health")
async def health():
    return {"status": "ok", "version": "3.0.0"}

@app.get("/api/players/search")
async def search_players(q: str = ""):
    if len(q) < 2:
        return {"players": []}
    try:
        s = get_settings()
        async with httpx.AsyncClient() as c:
            r = await c.get(
                f"{s.bdl_base_url}/players",
                headers={"Authorization": s.bdl_api_key},
                params={"search": q, "per_page": 10},
                timeout=10.0,
            )
            data = r.json()
        players = [p["first_name"] + " " + p["last_name"] for p in data.get("data", [])]
        return {"players": players}
    except Exception as e:
        return {"players": []}

# ── Player ─────────────────────────────────────────────────────────────────

@app.get("/api/player/{name}")
async def get_player(
    name: str,
    season: int = Query(default=2025),
    question: Optional[str] = Query(default=None),
    force: bool = Query(default=False),
):
    profile = await find_player(name, season)
    if not profile:
        raise HTTPException(404, f"Player '{name}' not found.")
    
    # PYTHON-LEVEL INTERCEPT: Kill the AI request if the player is inactive
    if profile.gp == 0:
        report = f"SYSTEM OVERRIDE: {profile.identity.name} has logged 0 minutes in the {season} season. The player is currently inactive, out of the rotation, or out of the league. Generative scouting report aborted to preserve data integrity."
    else:
        report = await ai_analyze(profile, question, force=force)
        
    return {
        "player": profile.identity.name,
        "team": profile.identity.team,
        "position": profile.identity.position,
        "season": season,
        "stats": {
            "ppg": profile.ppg, "rpg": profile.rpg, "apg": profile.apg,
            "spg": profile.spg, "bpg": profile.bpg, "tov": profile.tov,
            "fg_pct": profile.fg_pct, "three_pct": profile.three_pct,
            "ft_pct": profile.ft_pct, "ts_pct": profile.ts_pct,
            "mpg": profile.mpg, "gp": profile.gp,
        },
        "report": report,
    }

@app.get("/api/player/{name}/gamelog")
async def get_gamelog(name: str, season: int = Query(default=2025)):
    profile = await find_player(name, season)
    if not profile:
        raise HTTPException(404, f"Player '{name}' not found.")
    log = await get_player_game_log(profile.identity.player_id, season)
    return {"player": profile.identity.name, "season": season, "games": log}

# ── Compare ────────────────────────────────────────────────────────────────

@app.get("/api/compare")
async def compare(
    player_a: str = Query(...),
    player_b: str = Query(...),
    season: int = Query(default=2025),
    context: str = Query(default=""),
    force: bool = Query(default=False),
):
    pa, pb = await asyncio.gather(find_player(player_a, season), find_player(player_b, season))
    if not pa:
        raise HTTPException(404, f"'{player_a}' not found.")
    if not pb:
        raise HTTPException(404, f"'{player_b}' not found.")
        
    # PYTHON-LEVEL INTERCEPT: Prevent AI hallucination on mismatched data
    if pa.gp == 0 or pb.gp == 0:
        report = f"SYSTEM OVERRIDE: Invalid matchup. {pa.identity.name} has {pa.gp} GP and {pb.identity.name} has {pb.gp} GP. PIVOT requires active rotation data to run comparative analytics. Comparison aborted."
    else:
        report = await ai_compare(pa, pb, context, force=force)
        
    return {
        "player_a": pa.identity.name, "team_a": pa.identity.team,
        "player_b": pb.identity.name, "team_b": pb.identity.team,
        "season": season, "comparison": report,
        "stats_a": {"ppg": pa.ppg, "rpg": pa.rpg, "apg": pa.apg, "fg_pct": pa.fg_pct, "ts_pct": pa.ts_pct},
        "stats_b": {"ppg": pb.ppg, "rpg": pb.rpg, "apg": pb.apg, "fg_pct": pb.fg_pct, "ts_pct": pb.ts_pct},
    }

# ── Trade ──────────────────────────────────────────────────────────────────

@app.post("/api/trade")
async def trade(req: TradeRequest):
    all_names = req.outgoing + req.incoming
    resolved = await asyncio.gather(*[find_player(n, req.season) for n in all_names], return_exceptions=True)

    out_profiles, in_profiles, errors = [], [], []
    for i, result in enumerate(resolved):
        if isinstance(result, Exception) or result is None:
            errors.append(f"'{all_names[i]}' not found.")
            continue
        (out_profiles if i < len(req.outgoing) else in_profiles).append(result)

    if errors:
        raise HTTPException(422, "; ".join(errors))

    report = await ai_trade(out_profiles, in_profiles, req.context, force=req.force)
    return {
        "outgoing": [p.identity.name for p in out_profiles],
        "incoming": [p.identity.name for p in in_profiles],
        "season": req.season,
        "analysis": report,
    }

# ── Team ───────────────────────────────────────────────────────────────────

@app.get("/api/team/{abbreviation}")
async def get_team(
    abbreviation: str,
    season: int = Query(default=2025),
    question: Optional[str] = Query(default=None),
    force: bool = Query(default=False),
):
    team = await find_team(abbreviation, season)
    if not team:
        raise HTTPException(404, f"Team '{abbreviation}' not found.")
    report = await ai_team(team, question, force=force)
    return {
        "team": team.team,
        "abbreviation": abbreviation.upper(),
        "season": season,
        "roster_size": team.roster_size,
        "report": report,
        "leaders": {k: v.identity.name for k, v in team.leaders.items()},
    }

@app.get("/api/team/{abbreviation}/roster")
async def get_roster_package(
    abbreviation: str,
    season: int = Query(default=2025),
    force: bool = Query(default=False),
):
    team = await find_team(abbreviation, season)
    if not team:
        raise HTTPException(404, f"Team '{abbreviation}' not found.")
    reports = await ai_roster_package(team, force=force)
    return {
        "team": team.team,
        "abbreviation": abbreviation.upper(),
        "season": season,
        "roster_size": team.roster_size,
        "players_covered": len(reports),
        "reports": reports,
        "roster_stats": [
            {
                "name": p.identity.name,
                "position": p.identity.position,
                "ppg": p.ppg, "rpg": p.rpg, "apg": p.apg,
                "fg_pct": p.fg_pct, "ts_pct": p.ts_pct, "gp": p.gp,
            }
            for p in team.roster
        ],
    }

# ── Chat ───────────────────────────────────────────────────────────────────

@app.post("/api/chat")
async def chat(req: ChatRequest):
    profile = await find_player(req.player, req.season)
    if not profile:
        raise HTTPException(404, f"'{req.player}' not found.")
    reply, updated_history = await ai_chat(profile, req.history, req.message)
    return {
        "player": profile.identity.name,
        "reply": reply,
        "history": updated_history,
    }

# ── Live Games ─────────────────────────────────────────────────────────────

@app.get("/api/games/today")
async def today_games():
    games = await get_live_games()
    return {"games": games, "count": len(games)}

@app.get("/api/games/live")
async def live_box_scores():
    try:
        s = get_settings()
        async with httpx.AsyncClient() as c:
            r = await c.get(
                f"{s.bdl_base_url}/box_scores/live",
                headers={"Authorization": s.bdl_api_key},
                timeout=10.0,
            )
            data = r.json()
        return {"games": data.get("data", []), "count": len(data.get("data", []))}
    except Exception as e:
        raise HTTPException(500, str(e))

@app.get("/api/games/{game_id}/stats")
async def get_game_stats(game_id: int):
    """Fetch individual player box scores for a specific game."""
    try:
        s = get_settings()
        async with httpx.AsyncClient() as c:
            r = await c.get(
                f"{s.bdl_base_url}/stats",
                headers={"Authorization": s.bdl_api_key},
                params={"game_ids[]": game_id, "per_page": 100},
                timeout=10.0,
            )
            data = r.json()
        return {"stats": data.get("data", [])}
    except Exception as e:
        return {"stats": [], "error": str(e)}

# ── Cache ──────────────────────────────────────────────────────────────────

@app.get("/api/cache/stats")
async def cache_stats():
    return cache_info()

@app.post("/api/cache/clear")
async def clear_cache():
    deleted = cdel_namespace("llm:")
    return {"deleted": deleted}

# ── Serve frontend ─────────────────────────────────────────────────────────

app.mount("/static", StaticFiles(directory="frontend"), name="static")

@app.get("/")
async def serve_frontend():
    return FileResponse("frontend/index.html")