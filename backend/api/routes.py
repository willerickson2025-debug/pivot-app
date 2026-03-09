import os
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

# Project Logic Imports
from ..engine import bdl 
from ..ai import claude

app = FastAPI(title="PIVOT Pro Intelligence")

# 1. FIX "SLOPPY" UI ERRORS (CORS)
# This ensures your browser doesn't block the AI data
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. MOUNT FRONTEND ASSETS
# This makes your video, CSS, and JS available at /frontend/
app.mount("/frontend", StaticFiles(directory="frontend"), name="frontend")

# 3. LANDING PAGE (The Pitch View)
@app.get("/", response_class=HTMLResponse)
async def get_dashboard():
    """Serves the main PIVOT dashboard immediately."""
    index_path = os.path.join("frontend", "index.html")
    if os.path.exists(index_path):
        with open(index_path, "r") as f:
            return f.read()
    return "<h1>PIVOT: Dashboard file missing in /frontend/index.html</h1>"

# 4. DATA ENDPOINTS
@app.get("/api/search")
async def search(q: str):
    try:
        data = await bdl.search_players(q)
        return {"data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/intel/{player_id}")
async def player_intel(player_id: int):
    """Generates the AI Intelligence Report for the pitch."""
    try:
        stats = await bdl.get_recent_stats(player_id)
        avgs = await bdl.get_season_averages(player_id, 2023)
        report = await claude.generate_report(stats, avgs)
        return {
            "intelligence": report,
            "stats": stats,
            "averages": avgs
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI Engine Offline: {str(e)}")

# For Railway/Uvicorn entry
app = app