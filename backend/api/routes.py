import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
# Importing your existing engine logic
from ..engine import bdl 
from ..ai import claude

app = FastAPI(title="PIVOT Pro Intelligence")

# --- PITCH-READY SECURITY (CORS) ---
# Allows your frontend to talk to your backend without "Cross-Origin" errors
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/health")
async def health_check():
    """Confirms the system is live for the pitch."""
    return {
        "status": "online",
        "system": "PIVOT Core",
        "engine": "Active"
    }

@app.get("/api/search")
async def search_players(q: str):
    """Searches for players via the BallDontLie engine."""
    try:
        players = await bdl.search_players(q)
        return {"data": players}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/intel/{player_id}")
async def get_player_intel(player_id: int):
    """
    The Money Maker: Fetches stats and generates the 
    AI Intelligence report for the pitch.
    """
    try:
        # 1. Get raw data
        stats = await bdl.get_recent_stats(player_id)
        averages = await bdl.get_season_averages(player_id, 2023) # Update season as needed
        
        # 2. Generate AI Report
        report = await claude.generate_report(stats, averages)
        
        return {
            "player_id": player_id,
            "stats": stats,
            "averages": averages,
            "intelligence_report": report
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI Engine Error: {str(e)}")

# --- VERCEL REQUIREMENT ---
# This allows Vercel to see the app as a module
handler = app