import os

html = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>PIVOT - NBA Intelligence</title>
<link href="https://fonts.googleapis.com/css2?family=Bebas+Neue&family=DM+Mono:wght@400;500&family=Inter:wght@300;400;500;600&display=swap" rel="stylesheet">
<style>
:root{--bg:#080808;--surface:#111;--surface2:#181818;--border:#1e1e1e;--border2:#2a2a2a;--accent:#c8ff00;--accent-dim:rgba(200,255,0,0.08);--red:#ff4444;--green:#00e676;--text:#f0f0f0;--text2:#888;--text3:#444;--mono:'DM Mono',monospace;--sans:'Inter',sans-serif;--display:'Bebas Neue',sans-serif;}
*{margin:0;padding:0;box-sizing:border-box;}
body{background:var(--bg);color:var(--text);font-family:var(--sans);min-height:100vh;overflow-x:hidden;}
.app{display:flex;height:100vh;overflow:hidden;}
.sidebar{width:220px;min-width:220px;background:var(--surface);border-right:1px solid var(--border);display:flex;flex-direction:column;}
.logo-wrap{padding:28px 24px 20px;border-bottom:1px solid var(--border);}
.logo{font-family:var(--display);font-size:38px;letter-spacing:6px;color:var(--accent);line-height:1;}
.logo-sub{font-family:var(--mono);font-size:9px;letter-spacing:3px;color:var(--text3);margin-top:4px;}
.nav{flex:1;padding:16px 0;overflow-y:auto;}
.nav-section{font-family:var(--mono);font-size:9px;letter-spacing:3px;color:var(--text3);text-transform:uppercase;padding:16px 24px 8px;}
.nav-item{display:flex;align-items:center;gap:10px;padding:10px 24px;cursor:pointer;font-size:13px;color:var(--text2);transition:all 0.15s;border-left:2px solid transparent;user-select:none;}
.nav-item:hover{color:var(--text);background:var(--surface2);}
.nav-item.active{color:var(--accent);border-left-color:var(--accent);background:var(--accent-dim);}
.sidebar-bottom{padding:16px 24px;border-top:1px solid var(--border);}
.season-label{font-family:var(--mono);font-size:9px;letter-spacing:2px;color:var(--text3);margin-bottom:6px;}
.season-selector{background:var(--surface2);border:1px solid var(--border2);color:var(--text);font-family:var(--mono);font-size:11px;padding:8px 12px;width:100%;cursor:pointer;outline:none;}
.main{flex:1;overflow-y:auto;background:var(--bg);}
.main::-webkit-scrollbar{width:4px;}
.main::-webkit-scrollbar-thumb{background:var(--border2);}
.topbar{position:sticky;top:0;z-index:5;background:rgba(8,8,8,0.96);backdrop-filter:blur(10px);border-bottom:1px solid var(--border);padding:16px 40px;display:flex;align-items:center;justify-content:space-between;}
.page-title{font-family:var(--display);font-size:22px;letter-spacing:3px;}
.live-badge{display:flex;align-items:center;gap:6px;font-family:var(--mono);font-size:10px;letter-spacing:2px;color:var(--green);border:1px solid var(--green);padding:4px 10px;}
.live-dot{width:6px;height:6px;background:var(--green);border-radius:50%;animation:pulse 1.5s infinite;}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:0.3}}
.page{display:none;padding:40px;}
.page.active{display:block;}
.field-label{font-family:var(--mono);font-size:9px;letter-spacing:2px;color:var(--text3);text-transform:uppercase;margin-bottom:6px;}
.search-wrap{display:flex;gap:12px;margin-bottom:32px;align-items:flex-end;}
.search-field{flex:1;}
input[type=text]{width:100%;background:var(--surface);border:1px solid var(--border2);color:var(--text);padding:14px 18px;font-family:var(--sans);font-size:14px;outline:none;transition:border-color 0.2s;}
input[type=text]:focus{border-color:var(--accent);}
input[type=text]::placeholder{color:var(--text3);}
.btn{font-family:var(--display);font-size:16px;letter-spacing:3px;padding:14px 32px;background:var(--accent);color:#000;border:none;cursor:pointer;transition:all 0.15s;white-space:nowrap;}
.btn:hover{filter:brightness(1.1);}
.btn:disabled{background:var(--border2);color:var(--text3);cursor:not-allowed;filter:none;}
.btn-sm{font-family:var(--mono);font-size:11px;letter-spacing:2px;padding:10px 20px;background:transparent;color:var(--text2);border:1px solid var(--border2);cursor:pointer;transition:all 0.15s;white-space:nowrap;}
.btn-sm:hover{border-color:var(--accent);color:var(--accent);}
.stat-row{display:grid;grid-template-columns:repeat(6,1fr);gap:1px;background:var(--border);border:1px solid var(--border);margin-bottom:32px;}
.stat-card{background:var(--surface);padding:20px;text-align:center;}
.stat-val{font-family:var(--display);font-size:36px;color:var(--accent);line-height:1;margin-bottom:4px;}
.stat-lbl{font-family:var(--mono);font-size:9px;letter-spacing:2px;color:var(--text3);text-transform:uppercase;}
.output-wrap{background:var(--surface);border:1px solid var(--border);display:none;}
.output-wrap.visible{display:block;}
.output-header{padding:28px 32px;border-bottom:1px solid var(--border);display:flex;align-items:flex-start;justify-content:space-between;gap:24px;}
.player-name{font-family:var(--display);font-size:48px;letter-spacing:4px;line-height:1;}
.player-meta{font-family:var(--mono);font-size:11px;color:var(--text2);letter-spacing:2px;margin-top:8px;}
.report-body{padding:32px;font-size:14px;line-height:1.85;color:#bbb;}
.report-body h2{font-family:var(--display);font-size:18px;letter-spacing:3px;color:var(--accent);margin:28px 0 12px;padding-bottom:8px;border-bottom:1px solid var(--border2);}
.report-body h2:first-child{margin-top:0;}
.report-body strong{color:var(--text);}
.report-body p{margin-bottom:12px;}
.loading{display:none;align-items:center;gap:16px;padding:32px;color:var(--text3);font-family:var(--mono);font-size:11px;letter-spacing:3px;}
.loading.visible{display:flex;}
.spinner{width:18px;height:18px;border:2px solid var(--border2);border-top-color:var(--accent);border-radius:50%;animation:spin 0.7s linear infinite;flex-shrink:0;}
@keyframes spin{to{transform:rotate(360deg)}}
.error-box{display:none;padding:14px 18px;border:1px solid var(--red);color:var(--red);font-family:var(--mono);font-size:11px;margin-bottom:20px;}
.error-box.visible{display:block;}
.two-col{display:grid;grid-template-columns:1fr 1fr;gap:24px;}
.trade-side{background:var(--surface);border:1px solid var(--border);padding:24px;}
.trade-title{font-family:var(--mono);font-size:10px;letter-spacing:3px;color:var(--text3);text-transform:uppercase;margin-bottom:16px;}
.tags-wrap{display:flex;flex-wrap:wrap;gap:8px;min-height:40px;margin-bottom:12px;}
.tag{background:var(--surface2);border:1px solid var(--border2);padding:6px 12px;font-family:var(--mono);font-size:11px;display:flex;align-items:center;gap:8px;}
.tag-x{cursor:pointer;color:var(--text3);}
.tag-x:hover{color:var(--red);}
.add-row{display:flex;gap:8px;}
.roster-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:12px;margin-top:24px;}
.roster-card{background:var(--surface);border:1px solid var(--border);padding:20px;cursor:pointer;transition:all 0.15s;}
.roster-card:hover{border-color:var(--accent);transform:translateY(-2px);}
.rc-name{font-family:var(--display);font-size:20px;letter-spacing:2px;margin-bottom:4px;}
.rc-meta{font-family:var(--mono);font-size:9px;color:var(--text3);letter-spacing:1px;margin-bottom:14px;}
.rc-stats{display:flex;gap:14px;}
.rc-val{font-family:var(--display);font-size:22px;color:var(--accent);line-height:1;}
.rc-lbl{font-family:var(--mono);font-size:9px;color:var(--text3);}
.chat-wrap{display:flex;flex-direction:column;height:calc(100vh - 260px);min-height:400px;}
.chat-msgs{flex:1;overflow-y:auto;background:var(--surface);border:1px solid var(--border);border-bottom:none;padding:24px;display:flex;flex-direction:column;gap:20px;}
.msg{max-width:80%;}
.msg-user{align-self:flex-end;}
.msg-ai{align-self:flex-start;}
.msg-label{font-family:var(--mono);font-size:9px;letter-spacing:2px;color:var(--text3);margin-bottom:6px;}
.msg-bubble{padding:14px 18px;font-size:13px;line-height:1.7;}
.msg-user .msg-bubble{background:var(--accent);color:#000;font-weight:500;}
.msg-ai .msg-bubble{background:var(--surface2);border:1px solid var(--border2);}
.chat-input-row{background:var(--surface);border:1px solid var(--border);padding:16px;display:flex;gap:12px;}
.chat-input-row input{flex:1;background:var(--surface2);border:1px solid var(--border2);color:var(--text);padding:12px 16px;font-family:var(--sans);font-size:14px;outline:none;}
.chat-input-row input:focus{border-color:var(--accent);}
.games-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(320px,1fr));gap:16px;margin-top:24px;}
.game-card{background:var(--surface);border:1px solid var(--border);padding:24px;cursor:pointer;transition:border-color 0.15s;}
.game-card:hover{border-color:var(--accent);}
.game-status{font-family:var(--mono);font-size:9px;letter-spacing:2px;color:var(--green);margin-bottom:16px;}
.game-status.final{color:var(--text3);}
.game-teams{display:flex;align-items:center;justify-content:space-between;}
.game-abbr{font-family:var(--display);font-size:28px;letter-spacing:2px;}
.game-score{font-family:var(--display);font-size:52px;line-height:1;}
.game-vs{font-family:var(--mono);font-size:12px;color:var(--text3);}
.cmp-table{width:100%;border-collapse:collapse;font-family:var(--mono);font-size:12px;margin-bottom:24px;}
.cmp-table th{padding:12px 16px;text-align:center;font-size:10px;letter-spacing:2px;color:var(--text3);border-bottom:1px solid var(--border);}
.cmp-table th:first-child{text-align:left;}
.cmp-table td{padding:10px 16px;text-align:center;border-bottom:1px solid var(--border);color:var(--text2);}
.cmp-table td:first-child{text-align:left;color:var(--text3);}
.cmp-table td.win{color:var(--accent);font-weight:500;}
.cmp-table tr:hover td{background:var(--surface2);}
.box-table{width:100%;border-collapse:collapse;font-family:var(--mono);font-size:11px;margin-bottom:32px;}
.box-table th{padding:8px 6px;text-align:center;font-size:9px;letter-spacing:1px;color:var(--text3);border-bottom:1px solid var(--border);}
.box-table th:first-child{text-align:left;}
.box-table td{padding:10px 6px;text-align:center;border-bottom:1px solid var(--border);color:var(--text2);}
.box-table td:first-child{text-align:left;color:var(--text);}
.box-table tr:hover td{background:var(--surface2);}
.modal-overlay{position:fixed;inset:0;background:rgba(0,0,0,0.88);backdrop-filter:blur(6px);z-index:1000;display:none;align-items:center;justify-content:center;padding:40px;}
.modal-overlay.open{display:flex;}
.modal-box{background:var(--surface);border:1px solid var(--border2);max-width:920px;width:100%;max-height:85vh;overflow-y:auto;position:relative;}
.modal-box::-webkit-scrollbar{width:3px;}
.modal-box::-webkit-scrollbar-thumb{background:var(--border2);}
.modal-head{padding:28px 32px;border-bottom:1px solid var(--border);position:sticky;top:0;background:var(--surface);display:flex;align-items:center;justify-content:space-between;z-index:2;}
.modal-title{font-family:var(--display);font-size:32px;letter-spacing:3px;}
.modal-sub{font-family:var(--mono);font-size:10px;color:var(--text3);letter-spacing:2px;margin-top:6px;}
.modal-close{background:none;border:none;color:var(--text3);font-size:24px;cursor:pointer;transition:color 0.15s;padding:4px;line-height:1;}
.modal-close:hover{color:var(--accent);}
.modal-content{padding:32px;}
.sec-title{font-family:var(--mono);font-size:10px;letter-spacing:3px;color:var(--text3);}
</style>
</head>
<body>
<div class="app">
  <div class="sidebar">
    <div class="logo-wrap">
      <div class="logo">PIVOT</div>
      <div class="logo-sub">NBA INTELLIGENCE</div>
    </div>
    <nav class="nav">
      <div class="nav-section">Analysis</div>
      <div class="nav-item active" id="nav-scout" onclick="goTo('scout')">&#9675; Scout Player</div>
      <div class="nav-item" id="nav-compare" onclick="goTo('compare')">&#8644; Compare</div>
      <div class="nav-item" id="nav-trade" onclick="goTo('trade')">&#8596; Trade Analyzer</div>
      <div class="nav-item" id="nav-team" onclick="goTo('team')">&#9672; Team Report</div>
      <div class="nav-item" id="nav-roster" onclick="goTo('roster')">&#9889; Roster Package</div>
      <div class="nav-section">Intelligence</div>
      <div class="nav-item" id="nav-chat" onclick="goTo('chat')">&#9671; AI Analyst</div>
      <div class="nav-item" id="nav-games" onclick="goTo('games')">&#9679; Live Games</div>
    </nav>
    <div class="sidebar-bottom">
      <div class="season-label">Season</div>
      <select class="season-selector" id="global-season">
        <option value="2025">2025 - 26</option>
        <option value="2024">2024 - 25</option>
        <option value="2023">2023 - 24</option>
      </select>
    </div>
  </div>
  <div class="main">
    <div class="topbar">
      <div class="page-title" id="page-title">SCOUT PLAYER</div>
      <div class="live-badge"><div class="live-dot"></div>LIVE</div>
    </div>

    <!-- SCOUT -->
    <div class="page active" id="page-scout">
      <div class="search-wrap">
        <div class="search-field"><div class="field-label">Player Name</div><input type="text" id="scout-name" placeholder="e.g. Shai Gilgeous-Alexander"></div>
        <div class="search-field" style="max-width:240px"><div class="field-label">Question (optional)</div><input type="text" id="scout-q" placeholder="e.g. Trade value?"></div>
        <button class="btn" id="scout-btn" onclick="runScout(false)">Generate</button>
      </div>
      <div class="error-box" id="scout-err"></div>
      <div class="loading" id="scout-load"><div class="spinner"></div>Generating scouting report...</div>
      <div class="output-wrap" id="scout-out">
        <div class="output-header">
          <div><div class="player-name" id="scout-pname"></div><div class="player-meta" id="scout-pmeta"></div></div>
          <button class="btn-sm" onclick="runScout(true)">Refresh</button>
        </div>
        <div class="stat-row" id="scout-stats"></div>
        <div class="report-body" id="scout-report"></div>
      </div>
    </div>

    <!-- COMPARE -->
    <div class="page" id="page-compare">
      <div class="two-col" style="margin-bottom:20px">
        <div><div class="field-label">Player A</div><input type="text" id="cmp-a" placeholder="e.g. Luka Doncic"></div>
        <div><div class="field-label">Player B</div><input type="text" id="cmp-b" placeholder="e.g. Jayson Tatum"></div>
      </div>
      <div class="search-wrap">
        <div class="search-field"><div class="field-label">Context (optional)</div><input type="text" id="cmp-ctx" placeholder="e.g. Trade value, playoff performance"></div>
        <button class="btn" id="cmp-btn" onclick="runCompare()">Compare</button>
      </div>
      <div class="error-box" id="cmp-err"></div>
      <div class="loading" id="cmp-load"><div class="spinner"></div>Running comparison...</div>
      <div class="output-wrap" id="cmp-out">
        <div class="output-header"><div class="player-name" id="cmp-title" style="font-size:32px"></div></div>
        <div style="padding:0 32px"><table class="cmp-table" id="cmp-table"></table></div>
        <div class="report-body" id="cmp-report"></div>
      </div>
    </div>

    <!-- TRADE -->
    <div class="page" id="page-trade">
      <div class="two-col" style="margin-bottom:20px">
        <div class="trade-side">
          <div class="trade-title">Sending Out</div>
          <div class="tags-wrap" id="out-tags"></div>
          <div class="add-row"><input type="text" id="out-input" placeholder="Add player..."><button class="btn-sm" onclick="addTag('out')" style="padding:14px 20px">+</button></div>
        </div>
        <div class="trade-side">
          <div class="trade-title">Receiving</div>
          <div class="tags-wrap" id="in-tags"></div>
          <div class="add-row"><input type="text" id="in-input" placeholder="Add player..."><button class="btn-sm" onclick="addTag('in')" style="padding:14px 20px">+</button></div>
        </div>
      </div>
      <div class="search-wrap">
        <div class="search-field"><div class="field-label">Context (optional)</div><input type="text" id="trade-ctx" placeholder="e.g. We need rim protection"></div>
        <button class="btn" id="trade-btn" onclick="runTrade()">Evaluate Trade</button>
      </div>
      <div class="error-box" id="trade-err"></div>
      <div class="loading" id="trade-load"><div class="spinner"></div>Evaluating trade...</div>
      <div class="output-wrap" id="trade-out">
        <div class="output-header"><div class="player-name" id="trade-title" style="font-size:26px"></div></div>
        <div class="report-body" id="trade-report"></div>
      </div>
    </div>

    <!-- TEAM -->
    <div class="page" id="page-team">
      <div class="search-wrap">
        <div class="search-field" style="max-width:200px"><div class="field-label">Team Abbreviation</div><input type="text" id="team-abbr" placeholder="OKC, BOS, LAL..."></div>
        <div class="search-field"><div class="field-label">Question (optional)</div><input type="text" id="team-q" placeholder="e.g. Half court defense?"></div>
        <button class="btn" id="team-btn" onclick="runTeam()">Scout Team</button>
      </div>
      <div class="error-box" id="team-err"></div>
      <div class="loading" id="team-load"><div class="spinner"></div>Loading team...</div>
      <div class="output-wrap" id="team-out">
        <div class="output-header"><div><div class="player-name" id="team-name"></div><div class="player-meta" id="team-meta"></div></div></div>
        <div class="stat-row" id="team-leaders"></div>
        <div class="report-body" id="team-report"></div>
      </div>
    </div>

    <!-- ROSTER -->
    <div class="page" id="page-roster">
      <div class="search-wrap">
        <div class="search-field" style="max-width:200px"><div class="field-label">Team Abbreviation</div><input type="text" id="roster-abbr" placeholder="OKC, BOS, LAL..."></div>
        <button class="btn" id="roster-btn" onclick="runRoster()">Generate All Reports</button>
      </div>
      <p style="font-size:13px;color:var(--text3);margin-bottom:24px">All players generated concurrently. <span style="color:var(--accent)">~10 seconds.</span></p>
      <div class="error-box" id="roster-err"></div>
      <div class="loading" id="roster-load"><div class="spinner"></div>Running pipeline...</div>
      <div id="roster-results" style="display:none">
        <div class="sec-title" id="roster-title" style="margin-bottom:16px"></div>
        <div class="roster-grid" id="roster-grid"></div>
      </div>
    </div>

    <!-- CHAT -->
    <div class="page" id="page-chat">
      <div class="search-wrap" style="margin-bottom:20px">
        <div class="search-field"><div class="field-label">Load Player</div><input type="text" id="chat-player" placeholder="Enter player name..."></div>
        <button class="btn" id="chat-load-btn" onclick="loadChat()">Load Player</button>
      </div>
      <div class="error-box" id="chat-err"></div>
      <div class="loading" id="chat-load"><div class="spinner"></div>Loading player...</div>
      <div id="chat-ui" style="display:none">
        <div style="margin-bottom:16px;display:flex;align-items:center;justify-content:space-between">
          <div>
            <div style="font-family:var(--display);font-size:28px;letter-spacing:3px" id="chat-pname"></div>
            <div style="font-family:var(--mono);font-size:10px;color:var(--text3);letter-spacing:2px;margin-top:4px" id="chat-pmeta"></div>
          </div>
          <button class="btn-sm" onclick="clearChat()">New Session</button>
        </div>
        <div class="chat-wrap">
          <div class="chat-msgs" id="chat-msgs"></div>
          <div class="chat-input-row">
            <input type="text" id="chat-input" placeholder="Ask anything about this player...">
            <button class="btn" id="chat-send" onclick="sendChat()">Send</button>
          </div>
        </div>
      </div>
    </div>

    <!-- GAMES -->
    <div class="page" id="page-games">
      <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:24px">
        <div class="sec-title">Today's Games</div>
        <button class="btn-sm" onclick="loadGames()">Refresh</button>
      </div>
      <div class="loading" id="games-load"><div class="spinner"></div>Loading games...</div>
      <div class="error-box" id="games-err"></div>
      <div class="games-grid" id="games-grid"></div>
      <div id="games-empty" style="display:none;padding:60px;text-align:center;color:var(--text3);font-family:var(--mono);font-size:12px;letter-spacing:2px">NO GAMES TODAY</div>
    </div>

  </div>
</div>

<!-- MODAL -->
<div class="modal-overlay" id="modal-overlay">
  <div class="modal-box">
    <div class="modal-head">
      <div>
        <div class="modal-title" id="modal-title"></div>
        <div class="modal-sub" id="modal-sub"></div>
      </div>
      <button class="modal-close" id="modal-close-btn">&#x2715;</button>
    </div>
    <div class="modal-content">
      <div class="stat-row" id="modal-stats" style="display:none;margin-bottom:24px"></div>
      <div id="modal-body"></div>
    </div>
  </div>
</div>

<script>
var API = 'http://localhost:8000/api';
var tradeOut = [], tradeIn = [], chatHistory = [], chatPlayer = null;
var PAGES = ['scout','compare','trade','team','roster','chat','games'];
var TITLES = {scout:'SCOUT PLAYER',compare:'HEAD-TO-HEAD',trade:'TRADE ANALYZER',team:'TEAM REPORT',roster:'ROSTER PACKAGE',chat:'AI ANALYST',games:'LIVE GAMES'};

function goTo(page) {
  PAGES.forEach(function(p) {
    document.getElementById('page-'+p).classList.remove('active');
    document.getElementById('nav-'+p).classList.remove('active');
  });
  document.getElementById('page-'+page).classList.add('active');
  document.getElementById('nav-'+page).classList.add('active');
  document.getElementById('page-title').textContent = TITLES[page];
  if (page === 'games') loadGames();
}

function getSeason() { return parseInt(document.getElementById('global-season').value); }

function showLoad(id) {
  var el = document.getElementById(id+'-load');
  if (el) el.classList.add('visible');
  var err = document.getElementById(id+'-err');
  if (err) err.classList.remove('visible');
  var btn = document.getElementById(id+'-btn');
  if (btn) btn.disabled = true;
}

function hideLoad(id) {
  var el = document.getElementById(id+'-load');
  if (el) el.classList.remove('visible');
  var btn = document.getElementById(id+'-btn');
  if (btn) btn.disabled = false;
}

function showErr(id, msg) {
  var el = document.getElementById(id+'-err');
  if (el) { el.textContent = 'Error: ' + msg; el.classList.add('visible'); }
}

function renderStats(containerId, stats) {
  var fields = [
    {k:'ppg',l:'PPG'},{k:'rpg',l:'RPG'},{k:'apg',l:'APG'},
    {k:'fg_pct',l:'FG%',pct:true},{k:'ts_pct',l:'TS%',pct:true},{k:'gp',l:'GP',int:true}
  ];
  var html = '';
  fields.forEach(function(f) {
    var v = stats[f.k];
    var d = (v == null) ? 'N/A' : f.pct ? (v*100).toFixed(1)+'%' : f.int ? parseInt(v) : Number(v).toFixed(1);
    html += '<div class="stat-card"><div class="stat-val">'+d+'</div><div class="stat-lbl">'+f.l+'</div></div>';
  });
  document.getElementById(containerId).innerHTML = html;
}

function renderReport(containerId, text) {
  if (!text) return;
  var html = text
    .replace(/^## (.+)$/gm, '<h2>$1</h2>')
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.+?)\*/g, '<em>$1</em>');
  var parts = html.split('\\n');
  var out = '';
  parts.forEach(function(line) {
    line = line.trim();
    if (!line) return;
    out += line.startsWith('<h2>') ? line : '<p>'+line+'</p>';
  });
  document.getElementById(containerId).innerHTML = out;
}

// SCOUT
function runScout(force) {
  var name = document.getElementById('scout-name').value.trim();
  var q = document.getElementById('scout-q').value.trim();
  if (!name) return;
  showLoad('scout');
  var url = API+'/player/'+encodeURIComponent(name)+'?season='+getSeason();
  if (force) url += '&force=true';
  if (q) url += '&question='+encodeURIComponent(q);
  fetch(url).then(function(r) {
    return r.json().then(function(d) { return {ok:r.ok, d:d}; });
  }).then(function(res) {
    if (!res.ok) throw new Error(res.d.detail || 'Player not found');
    var d = res.d;
    document.getElementById('scout-pname').textContent = d.player;
    document.getElementById('scout-pmeta').textContent = d.team + '  |  ' + d.position + '  |  ' + getSeason() + ' SEASON';
    renderStats('scout-stats', d.stats);
    renderReport('scout-report', d.report);
    document.getElementById('scout-out').classList.add('visible');
  }).catch(function(e) {
    showErr('scout', e.message);
  }).then(function() { hideLoad('scout'); });
}

// COMPARE
function runCompare() {
  var a = document.getElementById('cmp-a').value.trim();
  var b = document.getElementById('cmp-b').value.trim();
  var ctx = document.getElementById('cmp-ctx').value.trim();
  if (!a || !b) return;
  showLoad('cmp');
  var url = API+'/compare?player_a='+encodeURIComponent(a)+'&player_b='+encodeURIComponent(b)+'&season='+getSeason();
  if (ctx) url += '&context='+encodeURIComponent(ctx);
  fetch(url).then(function(r) {
    return r.json().then(function(d) { return {ok:r.ok, d:d}; });
  }).then(function(res) {
    if (!res.ok) throw new Error(res.d.detail || 'Error');
    var d = res.d;
    document.getElementById('cmp-title').textContent = d.player_a + '  vs  ' + d.player_b;
    var sa = d.stats_a, sb = d.stats_b;
    var rows = [['Points',sa.ppg,sb.ppg,false],['Rebounds',sa.rpg,sb.rpg,false],['Assists',sa.apg,sb.apg,false],['FG%',sa.fg_pct,sb.fg_pct,true],['TS%',sa.ts_pct,sb.ts_pct,true]];
    var fmt = function(v,pct) { return v==null?'N/A':pct?(v*100).toFixed(1)+'%':Number(v).toFixed(1); };
    var nameA = d.player_a.split(' ').pop(), nameB = d.player_b.split(' ').pop();
    var tbl = '<tr><th>STAT</th><th>'+nameA+'</th><th>'+nameB+'</th><th>EDGE</th></tr>';
    rows.forEach(function(row) {
      var l=row[0],va=row[1],vb=row[2],pct=row[3],aw=va>vb,bw=vb>va;
      tbl += '<tr><td>'+l+'</td><td class="'+(aw?'win':'')+'">'+fmt(va,pct)+'</td><td class="'+(bw?'win':'')+'">'+fmt(vb,pct)+'</td><td style="color:var(--accent);font-size:10px">'+(aw?'A wins':bw?'B wins':'TIE')+'</td></tr>';
    });
    document.getElementById('cmp-table').innerHTML = tbl;
    renderReport('cmp-report', d.comparison);
    document.getElementById('cmp-out').classList.add('visible');
  }).catch(function(e) {
    showErr('cmp', e.message);
  }).then(function() { hideLoad('cmp'); });
}

// TRADE
function addTag(side) {
  var input = document.getElementById(side+'-input');
  var name = input.value.trim();
  if (!name) return;
  if (side === 'out') tradeOut.push(name); else tradeIn.push(name);
  input.value = '';
  renderTags();
}
function removeTag(side, name) {
  if (side === 'out') tradeOut = tradeOut.filter(function(n){return n!==name;});
  else tradeIn = tradeIn.filter(function(n){return n!==name;});
  renderTags();
}
function renderTags() {
  ['out','in'].forEach(function(side) {
    var list = side==='out'?tradeOut:tradeIn;
    document.getElementById(side+'-tags').innerHTML = list.map(function(n) {
      return '<div class="tag">'+n+'<span class="tag-x" onclick="removeTag(\''+side+'\',\''+n+'\')">x</span></div>';
    }).join('');
  });
}
function runTrade() {
  if (!tradeOut.length || !tradeIn.length) { showErr('trade','Add players on both sides.'); return; }
  var ctx = document.getElementById('trade-ctx').value.trim();
  showLoad('trade');
  fetch(API+'/trade', {
    method:'POST', headers:{'Content-Type':'application/json'},
    body: JSON.stringify({outgoing:tradeOut, incoming:tradeIn, season:getSeason(), context:ctx})
  }).then(function(r) {
    return r.json().then(function(d) { return {ok:r.ok, d:d}; });
  }).then(function(res) {
    if (!res.ok) throw new Error(res.d.detail || 'Error');
    var d = res.d;
    document.getElementById('trade-title').textContent = d.outgoing.join(', ') + '  \u2192  ' + d.incoming.join(', ');
    renderReport('trade-report', d.analysis);
    document.getElementById('trade-out').classList.add('visible');
  }).catch(function(e) {
    showErr('trade', e.message);
  }).then(function() { hideLoad('trade'); });
}

// TEAM
function runTeam() {
  var abbr = document.getElementById('team-abbr').value.trim().toUpperCase();
  var q = document.getElementById('team-q').value.trim();
  if (!abbr) return;
  showLoad('team');
  var url = API+'/team/'+abbr+'?season='+getSeason();
  if (q) url += '&question='+encodeURIComponent(q);
  fetch(url).then(function(r) {
    return r.json().then(function(d) { return {ok:r.ok, d:d}; });
  }).then(function(res) {
    if (!res.ok) throw new Error(res.d.detail || 'Not found');
    var d = res.d;
    document.getElementById('team-name').textContent = d.team;
    document.getElementById('team-meta').textContent = abbr + '  |  ' + d.roster_size + ' PLAYERS  |  ' + getSeason() + ' SEASON';
    var leaders = d.leaders || {};
    var lf = [{k:'scoring',l:'SCORING'},{k:'rebounding',l:'REBOUNDS'},{k:'assists',l:'ASSISTS'},{k:'defense',l:'DEFENSE'},{k:'efficiency',l:'EFFICIENCY'}];
    document.getElementById('team-leaders').innerHTML = lf.map(function(f) {
      var name = leaders[f.k] || 'N/A';
      return '<div class="stat-card"><div class="stat-val" style="font-size:18px;letter-spacing:1px">'+name.split(' ').pop()+'</div><div class="stat-lbl">'+f.l+'</div></div>';
    }).join('');
    renderReport('team-report', d.report);
    document.getElementById('team-out').classList.add('visible');
  }).catch(function(e) {
    showErr('team', e.message);
  }).then(function() { hideLoad('team'); });
}

// ROSTER
function runRoster() {
  var abbr = document.getElementById('roster-abbr').value.trim().toUpperCase();
  if (!abbr) return;
  document.getElementById('roster-results').style.display = 'none';
  showLoad('roster');
  fetch(API+'/team/'+abbr+'/roster?season='+getSeason()).then(function(r) {
    return r.json().then(function(d) { return {ok:r.ok, d:d}; });
  }).then(function(res) {
    if (!res.ok) throw new Error(res.d.detail || 'Not found');
    var d = res.d;
    document.getElementById('roster-title').textContent = d.team + ' - ' + d.players_covered + ' reports generated';
    var grid = document.getElementById('roster-grid');
    grid.innerHTML = '';
    var rs = d.roster_stats || [];
    var reports = d.reports || {};
    var i = 0;
    Object.keys(reports).forEach(function(name) {
      var report = reports[name];
      var stat = null;
      rs.forEach(function(r) { if (r.name === name) stat = r; });
      if (!stat) stat = {};
      var card = document.createElement('div');
      card.className = 'roster-card';
      card.style.animationDelay = (i * 0.04) + 's';
      card.innerHTML =
        '<div class="rc-name">'+name+'</div>'+
        '<div class="rc-meta">'+(stat.position||'')+'</div>'+
        '<div class="rc-stats">'+
          '<div><div class="rc-val">'+Number(stat.ppg||0).toFixed(1)+'</div><div class="rc-lbl">PPG</div></div>'+
          '<div><div class="rc-val">'+Number(stat.rpg||0).toFixed(1)+'</div><div class="rc-lbl">RPG</div></div>'+
          '<div><div class="rc-val">'+Number(stat.apg||0).toFixed(1)+'</div><div class="rc-lbl">APG</div></div>'+
          '<div><div class="rc-val">'+(stat.gp||0)+'</div><div class="rc-lbl">GP</div></div>'+
        '</div>';
      (function(n, s, r) {
        card.onclick = function() { openPlayerModal(n, s, r); };
      })(name, stat, report);
      grid.appendChild(card);
      i++;
    });
    document.getElementById('roster-results').style.display = 'block';
  }).catch(function(e) {
    showErr('roster', e.message);
  }).then(function() { hideLoad('roster'); });
}

// CHAT
function loadChat() {
  var name = document.getElementById('chat-player').value.trim();
  if (!name) return;
  var loadBtn = document.getElementById('chat-load-btn');
  loadBtn.disabled = true;
  document.getElementById('chat-load').classList.add('visible');
  document.getElementById('chat-err').classList.remove('visible');
  fetch(API+'/player/'+encodeURIComponent(name)+'?season='+getSeason()).then(function(r) {
    return r.json().then(function(d) { return {ok:r.ok, d:d}; });
  }).then(function(res) {
    if (!res.ok) throw new Error(res.d.detail || 'Not found');
    chatPlayer = res.d; chatHistory = [];
    document.getElementById('chat-pname').textContent = res.d.player;
    document.getElementById('chat-pmeta').textContent = res.d.team + '  |  ' + res.d.position + '  |  ' + getSeason() + ' SEASON';
    document.getElementById('chat-msgs').innerHTML = '';
    document.getElementById('chat-ui').style.display = 'block';
    appendMsg('ai', 'Scouting file loaded for ' + res.d.player + '. Ask me anything.');
  }).catch(function(e) {
    var err = document.getElementById('chat-err');
    err.textContent = 'Error: ' + e.message;
    err.classList.add('visible');
  }).then(function() {
    loadBtn.disabled = false;
    document.getElementById('chat-load').classList.remove('visible');
  });
}
function clearChat() {
  chatHistory = []; chatPlayer = null;
  document.getElementById('chat-msgs').innerHTML = '';
  document.getElementById('chat-ui').style.display = 'none';
  document.getElementById('chat-player').value = '';
}
function appendMsg(role, text) {
  var win = document.getElementById('chat-msgs');
  var div = document.createElement('div');
  div.className = 'msg msg-' + (role==='user' ? 'user' : 'ai');
  div.innerHTML = '<div class="msg-label">'+(role==='user'?'YOU':'PIVOT')+'</div><div class="msg-bubble">'+text+'</div>';
  win.appendChild(div);
  win.scrollTop = win.scrollHeight;
}
function sendChat() {
  var input = document.getElementById('chat-input');
  var msg = input.value.trim();
  if (!msg || !chatPlayer) return;
  input.value = '';
  appendMsg('user', msg);
  var sendBtn = document.getElementById('chat-send');
  sendBtn.disabled = true;
  fetch(API+'/chat', {
    method:'POST', headers:{'Content-Type':'application/json'},
    body: JSON.stringify({player:chatPlayer.player, season:getSeason(), message:msg, history:chatHistory})
  }).then(function(r) {
    return r.json().then(function(d) { return {ok:r.ok, d:d}; });
  }).then(function(res) {
    if (!res.ok) throw new Error(res.d.detail || 'Error');
    chatHistory = res.d.history;
    appendMsg('ai', res.d.reply);
  }).catch(function(e) {
    appendMsg('ai', 'Error: ' + e.message);
  }).then(function() { sendBtn.disabled = false; });
}

// GAMES
function loadGames() {
  document.getElementById('games-load').classList.add('visible');
  document.getElementById('games-err').classList.remove('visible');
  document.getElementById('games-empty').style.display = 'none';
  fetch(API+'/games/live').then(function(r) {
    return r.json();
  }).then(function(data) {
    var games = data.games || [];
    var grid = document.getElementById('games-grid');
    grid.innerHTML = '';
    if (!games.length) {
      document.getElementById('games-empty').style.display = 'block';
      return;
    }
    games.forEach(function(g) {
      var home = g.home_team || {}, away = g.visitor_team || {};
      var status = g.status || 'Scheduled';
      var isLive = status.indexOf('Qtr') >= 0 || status.indexOf('Half') >= 0;
      var isFinal = status === 'Final';
      var hLead = g.home_team_score > g.visitor_team_score;
      var aLead = g.visitor_team_score > g.home_team_score;
      var card = document.createElement('div');
      card.className = 'game-card';
      card.innerHTML =
        '<div class="game-status'+(isFinal?' final':'')+'">'+(isLive?'LIVE \u2014 ':'')+status+(g.time?' \u2014 '+g.time:'')+'</div>'+
        '<div class="game-teams">'+
          '<div style="text-align:center"><div class="game-abbr">'+(away.abbreviation||'AWY')+'</div><div class="game-score" style="color:'+(aLead?'var(--accent)':'var(--text2)');'">'+(g.visitor_team_score!=null?g.visitor_team_score:'--')+'</div></div>'+
          '<div class="game-vs">@</div>'+
          '<div style="text-align:center"><div class="game-abbr">'+(home.abbreviation||'HME')+'</div><div class="game-score" style="color:'+(hLead?'var(--accent)':'var(--text2)');'">'+(g.home_team_score!=null?g.home_team_score:'--')+'</div></div>'+
        '</div>'+
        '<div style="font-family:var(--mono);font-size:9px;color:var(--text3);letter-spacing:1px;margin-top:12px;text-align:center">TAP FOR BOX SCORE</div>';
      (function(game) {
        card.onclick = function() { openBoxScore(game); };
      })(g);
      grid.appendChild(card);
    });
  }).catch(function(e) {
    var err = document.getElementById('games-err');
    err.textContent = 'Error: ' + e.message;
    err.classList.add('visible');
  }).then(function() {
    document.getElementById('games-load').classList.remove('visible');
  });
}

function openBoxScore(game) {
  var home = game.home_team, away = game.visitor_team;
  function buildTable(team) {
    var active = team.players.filter(function(p){ return p.min && p.min !== '00'; });
    active.sort(function(a,b){ return b.pts - a.pts; });
    var html = '<div style="font-family:var(--display);font-size:20px;letter-spacing:3px;margin-bottom:12px;color:var(--accent)">'+team.full_name+'</div>';
    html += '<table class="box-table"><tr><th style="text-align:left">PLAYER</th><th>MIN</th><th>PTS</th><th>REB</th><th>AST</th><th>STL</th><th>BLK</th><th>TO</th><th>FG</th><th>3PT</th><th>+/-</th></tr>';
    active.forEach(function(p) {
      var pm = p.plus_minus;
      html += '<tr>'+
        '<td>'+p.player.first_name+' '+p.player.last_name+'</td>'+
        '<td>'+p.min+'</td>'+
        '<td style="color:'+(p.pts>=20?'var(--accent)':p.pts>=10?'var(--text)':'var(--text2)')+';font-weight:'+(p.pts>=10?600:400)+'">'+p.pts+'</td>'+
        '<td>'+p.reb+'</td>'+
        '<td>'+p.ast+'</td>'+
        '<td>'+p.stl+'</td>'+
        '<td>'+p.blk+'</td>'+
        '<td style="color:'+(p.turnover>=3?'var(--red)':'')+'">'+p.turnover+'</td>'+
        '<td>'+p.fgm+'-'+p.fga+'</td>'+
        '<td>'+p.fg3m+'-'+p.fg3a+'</td>'+
        '<td style="color:'+(pm>0?'var(--green)':pm<0?'var(--red)':'var(--text3)')+'">'+((pm>0?'+':'')+pm)+'</td>'+
        '</tr>';
    });
    html += '</table>';
    return html;
  }
  document.getElementById('modal-title').textContent = away.abbreviation+' '+game.visitor_team_score+'   '+home.abbreviation+' '+game.home_team_score;
  document.getElementById('modal-sub').textContent = (game.time||game.status) + '  |  ' + game.date;
  document.getElementById('modal-stats').style.display = 'none';
  document.getElementById('modal-body').innerHTML = buildTable(away) + buildTable(home);
  document.getElementById('modal-overlay').classList.add('open');
  document.body.style.overflow = 'hidden';
}

function openPlayerModal(name, stats, report) {
  document.getElementById('modal-title').textContent = name;
  document.getElementById('modal-sub').textContent = (stats.position||'') + '  |  FULL SCOUTING REPORT';
  var statsEl = document.getElementById('modal-stats');
  statsEl.style.display = 'grid';
  renderStats('modal-stats', stats);
  var bodyEl = document.getElementById('modal-body');
  bodyEl.innerHTML = '<div class="report-body" id="modal-report-inner"></div>';
  renderReport('modal-report-inner', report);
  document.getElementById('modal-overlay').classList.add('open');
  document.body.style.overflow = 'hidden';
}

function closeModal() {
  document.getElementById('modal-overlay').classList.remove('open');
  document.body.style.overflow = '';
}

// Event listeners - all attached after DOM is ready
document.getElementById('modal-overlay').onclick = function(e) { if (e.target === this) closeModal(); };
document.getElementById('modal-close-btn').onclick = closeModal;
document.addEventListener('keydown', function(e) { if (e.key === 'Escape') closeModal(); });

document.getElementById('scout-name').onkeydown = function(e) { if (e.key==='Enter') runScout(false); };
document.getElementById('scout-q').onkeydown = function(e) { if (e.key==='Enter') runScout(false); };
document.getElementById('cmp-a').onkeydown = function(e) { if (e.key==='Enter') runCompare(); };
document.getElementById('cmp-b').onkeydown = function(e) { if (e.key==='Enter') runCompare(); };
document.getElementById('out-input').onkeydown = function(e) { if (e.key==='Enter') addTag('out'); };
document.getElementById('in-input').onkeydown = function(e) { if (e.key==='Enter') addTag('in'); };
document.getElementById('team-abbr').onkeydown = function(e) { if (e.key==='Enter') runTeam(); };
document.getElementById('chat-player').onkeydown = function(e) { if (e.key==='Enter') loadChat(); };
document.getElementById('chat-input').onkeydown = function(e) { if (e.key==='Enter') sendChat(); };
</script>
</body>
</html>"""

os.makedirs("frontend", exist_ok=True)
with open("frontend/index.html", "w") as f:
    f.write(html)

print("Done -", len(html), "bytes written to frontend/index.html")
