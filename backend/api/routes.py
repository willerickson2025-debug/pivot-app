import os
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
# These point to your specific project structure
from ..engine import bdl 
from ..ai import claude

app = FastAPI(title="PIVOT Pro Intelligence")

# 1. ALLOW THE UI TO TALK TO THE ENGINE
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. THE PITCH UI (Directly serves your HTML)
@app.get("/", response_class=HTMLResponse)
async def get_dashboard():
    # Looks for index.html in your public folder
    index_path = os.path.join("public", "index.html")
    if os.path.exists(index_path):
        with open(index_path, "r") as f:
            return f.read()
    return "<h1>PIVOT: Dashboard Error - 'public/index.html' not found.</h1>"

# 3. THE DATA ENGINE
@app.get("/api/search")
async def search(q: str):
    try:
        data = await bdl.search_players(q)
        return {"data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/intel/{player_id}")
async def player_intel(player_id: int):
    try:
        stats = await bdl.get_recent_stats(player_id)
        avgs = await bdl.get_season_averages(player_id, 2023)
        report = await claude.generate_report(stats, avgs)
        return {"intelligence": report, "stats": stats}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI Engine Offline: {str(e)}")

# This allows Vercel to find your app
handler = app