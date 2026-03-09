from __future__ import annotations
from backend.models.player import PlayerProfile, TeamProfile

SYSTEM = """You are PIVOT, the most advanced NBA analytics intelligence ever built. You are the brain powering a professional front office platform used by GMs, scouts, and coaching staffs.

You think like a fusion of:
- Daryl Morey (data-driven roster construction)
- Bob Myers (relationship and contract intelligence)  
- A veteran film coordinator (tactical detail)
- A Wall Street analyst (financial and market value)

YOUR ANALYSIS IS ALWAYS:
- Anchored in the exact statistics provided
- Contextually aware of age curves, contract windows, and team fit
- Tactically specific — not generic
- Financially literate — you understand cap implications
- Decisive — you make clear recommendations, not hedge everything
- Ruthlessly efficient — do not waste time analyzing ghost players or 0-stat lines.

NEVER produce generic summaries. Every output should feel like it could change a front office decision today."""

def analyze_prompt(p: PlayerProfile, question: str | None = None) -> str:
    s = p.stats
    i = p.identity
    
    base = f"""Generate a comprehensive professional scouting report for {i.name}.
    momentum_str = f"MOMENTUM: {p.momentum['status']} ({p.momentum['pts_delta']:+.1f} PPG vs Season Avg)"
    rank_str = f"EFFICIENCY RANK: {p.percentile} for {i.position} position"
    
    # Add these to the base string you send to Claude

IDENTITY
Name: {i.name} | Team: {i.team} | Position: {i.position}
Height: {i.height or "N/A"} | Weight: {i.weight_lbs or "N/A"} lbs | Country: {i.country}
Experience: {i.years_of_experience or "N/A"} years
Draft: {f"Round {i.draft_round}, Pick {i.draft_number} ({i.draft_year})" if i.draft_year else "Undrafted"}

{p.season} SEASON STATS ({p.gp} games)
Points: {p.ppg:.1f} | Rebounds: {p.rpg:.1f} | Assists: {p.apg:.1f}
Steals: {p.spg:.1f} | Blocks: {p.bpg:.1f} | Turnovers: {p.tov:.1f} | Minutes: {p.mpg:.1f}

SHOOTING EFFICIENCY
FG: {p.fg_pct:.1%} ({s.field_goals_made:.1f}/{s.field_goals_attempted:.1f} per game)
3PT: {p.three_pct:.1%} ({s.three_point_made:.1f}/{s.three_point_attempted:.1f} per game)
FT: {p.ft_pct:.1%} ({s.free_throws_made:.1f}/{s.free_throws_attempted:.1f} per game)
True Shooting: {f"{p.ts_pct:.1%}" if p.ts_pct else "N/A"}
AST/TOV Ratio: {f"{p.stats.assist_to_turnover:.2f}" if p.stats.assist_to_turnover else "N/A"}

{f"SPECIFIC QUESTION FROM STAFF:{chr(10)}{question}" if question else ""}"""

    # THE BYPASS FOR INACTIVE PLAYERS
    if p.gp == 0:
        return base + "\n\nCRITICAL INSTRUCTION: This player has 0 games played this season. DO NOT write the structured scouting report. Output EXACTLY ONE blunt, professional paragraph stating they are inactive, out of the rotation, or out of the league, rendering a full scouting report unnecessary."

    return base + """

DELIVER THIS EXACT STRUCTURE:

## Executive Summary
2-3 sentences. What is the single most important thing to know about this player right now?

## Offensive Profile
How does he score? Shot creation, efficiency by zone, tendencies, weaknesses.

## Defensive Profile  
On-ball, off-ball, switchability, rebounding, impact metrics.

## Playmaking & Basketball IQ
Vision, decision-making, pick-and-roll reads, clutch tendencies.

## Physical Profile & Athleticism
How his body affects his game. Age curve projection.

## Contract & Market Value
What would he cost on the open market? Is he overpaid/underpaid? Trade value tier.

## Fit Analysis
What team contexts maximize his value? What systems does he thrive/struggle in?

## Risk Factors
Injury history markers, age curve, efficiency concerns, character flags.

## Verdict
**BUY / HOLD / SELL** — one word, then 2-3 sentences explaining the decision."""


def compare_prompt(a: PlayerProfile, b: PlayerProfile, context: str = "") -> str:
    def row(label, va, vb, pct=False):
        fa = f"{va:.1%}" if pct else f"{va:.1f}"
        fb = f"{vb:.1f}" if not pct else f"{vb:.1%}"
        edge = "← A" if va > vb else ("B →" if vb > va else "TIE")
        return f"| {label:20} | {fa:>10} | {fb:>10} | {edge} |"

    table = "\n".join([
        f"| {'STAT':20} | {''+a.identity.name[:10]:>10} | {''+b.identity.name[:10]:>10} | EDGE |",
        "|" + "-"*22 + "|" + "-"*12 + "|" + "-"*12 + "|" + "-"*8 + "|",
        row("Games Played", a.gp, b.gp),
        row("Points", a.ppg, b.ppg),
        row("Rebounds", a.rpg, b.rpg),
        row("Assists", a.apg, b.apg),
        row("Steals", a.spg, b.spg),
        row("Blocks", a.bpg, b.bpg),
        row("Turnovers", a.tov, b.tov),
        row("Minutes", a.mpg, b.mpg),
        row("FG%", a.fg_pct, b.fg_pct, pct=True),
        row("3PT%", a.three_pct, b.three_pct, pct=True),
        row("FT%", a.ft_pct, b.ft_pct, pct=True),
        row("TS%", a.ts_pct or 0, b.ts_pct or 0, pct=True),
    ])

    base = f"""Compare {a.identity.name} vs {b.identity.name} — {a.season} season.

{table}

{f"CONTEXT: {context}" if context else ""}"""

    # THE BYPASS FOR ABSURD MISMATCHES
    if a.gp == 0 or b.gp == 0:
        return base + "\n\nCRITICAL INSTRUCTION: One of these players has 0 games played this season. DO NOT write the structured multi-section comparison. Output EXACTLY ONE blunt paragraph stating the comparison is invalid due to an inactive player, and immediately declare the active player the default winner."

    return base + """

DELIVER THIS STRUCTURE:

## Statistical Edge
Who wins each category and why it matters contextually.

## Scoring Comparison
Style, efficiency, and volume differences.

## Two-Way Impact
Defensive value comparison — who makes their team better?

## Playmaking & IQ
Who is the better creator and decision-maker?

## Physical & Age Projection
Body, athleticism, and trajectory differences.

## Contract & Trade Value
Who gives more value for the dollar right now?

## Best Fit Contexts
When would you want Player A over B and vice versa?

## Verdict
If you could only have one, who and why? Be decisive."""


def trade_prompt(out: list[PlayerProfile], inc: list[PlayerProfile], context: str = "") -> str:
    def summarize(players):
        return "\n".join(
            f"• {p.identity.name} ({p.identity.position}, {p.identity.team}) — "
            f"{p.ppg:.1f}pts / {p.rpg:.1f}reb / {p.apg:.1f}ast | "
            f"FG: {p.fg_pct:.1%} | TS: {f'{p.ts_pct:.1%}' if p.ts_pct else 'N/A'} | "
            f"{p.mpg:.0f} mpg | {p.gp} GP"
            for p in players
        )

    return f"""Evaluate this NBA trade proposal:

SENDING OUT:
{summarize(out)}

RECEIVING:
{summarize(inc)}

{f"FRONT OFFICE CONTEXT: {context}" if context else ""}

CRITICAL INSTRUCTION: Take note of any player with 0 GP (Games Played). They hold zero immediate on-court value and should be treated purely as salary filler, dead money, or upcoming cuts.

DELIVER THIS STRUCTURE:

## Trade Summary
One sentence on what each side is trying to accomplish.

## Value Delta
Who wins on raw production? Quantify the gap.

## Role & Fit Analysis
Do the incoming players actually fill a need? Will they fit the system?

## Age & Timeline
Does this trade make sense for where each team is in their window?

## Contract Intelligence
Cap implications, trade exceptions, future flexibility impact.

## Risk Assessment
Injury history, fit concerns, locker room considerations.

## Verdict
**ACCEPT / REJECT / COUNTER**
Confidence level: High / Medium / Low
One paragraph explaining the decision."""


def team_prompt(team: TeamProfile, question: str | None = None) -> str:
    leaders = team.leaders
    roster_lines = "\n".join(
        f"  {p.identity.name} ({p.identity.position}): "
        f"{p.ppg:.1f}pts / {p.rpg:.1f}reb / {p.apg:.1f}ast | "
        f"FG: {p.fg_pct:.1%} | TS: {f'{p.ts_pct:.1%}' if p.ts_pct else 'N/A'} | {p.mpg:.0f}mpg | {p.gp} GP"
        for p in team.top_scorers
    )

    return f"""Generate a complete team intelligence report for the {team.team} ({team.season} season).

TOP CONTRIBUTORS:
{roster_lines}

STATISTICAL LEADERS:
Scoring:    {leaders.get('scoring', type('', (), {'identity': type('', (), {'name': 'N/A'})()})()).identity.name}
Rebounding: {leaders.get('rebounding', type('', (), {'identity': type('', (), {'name': 'N/A'})()})()).identity.name}
Assists:    {leaders.get('assists', type('', (), {'identity': type('', (), {'name': 'N/A'})()})()).identity.name}
Defense:    {leaders.get('defense', type('', (), {'identity': type('', (), {'name': 'N/A'})()})()).identity.name}
Efficiency: {leaders.get('efficiency', type('', (), {'identity': type('', (), {'name': 'N/A'})()})()).identity.name}

{f"STAFF QUESTION: {question}" if question else ""}

DELIVER THIS STRUCTURE:

## Team Identity
What is the defining characteristic of how this team plays?

## Offensive System
Pace, spacing, creation hierarchy, half-court sets.

## Defensive Profile
Scheme, personnel fit, rim protection, perimeter defense.

## Roster Construction Grade
How well does this roster fit together? What's the ceiling?

## Depth Chart Analysis
Starter quality vs bench depth. Where are the weaknesses?

## Injury Vulnerability
Which players are injury risks? What happens if they go down?

## Roster Gaps
What positions/skills are missing? What type of player would elevate this team?

## Offseason Blueprint
3 specific, actionable moves to improve this roster."""


def chat_system(p: PlayerProfile) -> str:
    return f"""{SYSTEM}

You are currently in a focused analysis session on {p.identity.name} ({p.identity.team}, {p.identity.position}).

LOADED STATS ({p.season} season, {p.gp} games):
Scoring: {p.ppg:.1f} PPG | Rebounds: {p.rpg:.1f} | Assists: {p.apg:.1f} | Steals: {p.spg:.1f} | Blocks: {p.bpg:.1f}
Efficiency: FG {p.fg_pct:.1%} | 3PT {p.three_pct:.1%} | FT {p.ft_pct:.1%} | TS {f"{p.ts_pct:.1%}" if p.ts_pct else "N/A"}
Usage: {p.mpg:.0f} minutes per game

Answer all questions using this data as your factual foundation.
When speculating beyond the stats, say so explicitly."""


def roster_card_prompt(p: PlayerProfile) -> str:
    base = f"""Generate a concise scouting card for {p.identity.name}.

STATS ({p.season} season, {p.gp} GP):
{p.ppg:.1f}pts / {p.rpg:.1f}reb / {p.apg:.1f}ast / {p.spg:.1f}stl / {p.bpg:.1f}blk
FG: {p.fg_pct:.1%} | 3PT: {p.three_pct:.1%} | FT: {p.ft_pct:.1%} | TS: {f"{p.ts_pct:.1%}" if p.ts_pct else "N/A"} | {p.mpg:.0f}mpg"""

    if p.gp == 0:
        return base + "\n\nCRITICAL INSTRUCTION: This player has 0 games played. Output exactly ONE sentence stating they are out of the rotation or inactive."

    return base + """

Deliver EXACTLY this structure, keep each section to 2 sentences max:

## Role & Value
## Offensive Skill
## Defensive Impact
## Verdict
One sentence: BUY / HOLD / SELL and why."""