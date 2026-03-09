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

FORMATTING RULES — STRICTLY ENFORCED:
- Write in clean, professional prose only. No exceptions.
- Never use markdown symbols: no #, no *, no **, no bullet points, no dashes as list items.
- Section headers must be written in ALL CAPS followed by a colon, on their own line.
- Each section is one or more full paragraphs. No fragmented lists.
- Write like a professional front office memo, not a blog post.
- Every output should feel like it could be printed and handed to a GM."""


def analyze_prompt(p: PlayerProfile, question: str | None = None) -> str:
    s = p.stats
    i = p.identity
    return f"""Generate a comprehensive professional scouting report for {i.name}.

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

{f"SPECIFIC QUESTION FROM STAFF:{chr(10)}{question}" if question else ""}

Write the report using ONLY these section headers in ALL CAPS followed by a colon. Each section is prose paragraphs only — no bullets, no markdown.

EXECUTIVE SUMMARY:
Two to three sentences. The single most important thing to know about this player right now.

OFFENSIVE PROFILE:
How he scores. Shot creation, efficiency by zone, tendencies, and weaknesses in full sentences.

DEFENSIVE PROFILE:
On-ball and off-ball defense, switchability, rebounding, and floor impact written as a cohesive paragraph.

PLAYMAKING AND BASKETBALL IQ:
Vision, decision-making, pick-and-roll reads, and clutch tendencies in prose form.

PHYSICAL PROFILE AND ATHLETICISM:
How his body affects his game and his age curve projection.

CONTRACT AND MARKET VALUE:
What he would cost on the open market, whether he is overpaid or underpaid, and his trade value tier.

FIT ANALYSIS:
What team contexts maximize his value and what systems he thrives or struggles in.

RISK FACTORS:
Injury history, age curve concerns, efficiency flags, and any character considerations.

VERDICT:
State BUY, HOLD, or SELL clearly in the first sentence, then provide two to three sentences explaining the recommendation decisively."""


def compare_prompt(a: PlayerProfile, b: PlayerProfile, context: str = "") -> str:
    def row(label, va, vb, pct=False):
        fa = f"{va:.1%}" if pct else f"{va:.1f}"
        fb = f"{vb:.1f}" if not pct else f"{vb:.1%}"
        edge = "A" if va > vb else ("B" if vb > va else "TIE")
        return f"| {label:20} | {fa:>10} | {fb:>10} | {edge} |"

    table = "\n".join([
        f"| {'STAT':20} | {a.identity.name[:10]:>10} | {b.identity.name[:10]:>10} | EDGE |",
        "|" + "-"*22 + "|" + "-"*12 + "|" + "-"*12 + "|" + "-"*8 + "|",
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

    return f"""Compare {a.identity.name} vs {b.identity.name} for the {a.season} season.

{table}

{f"CONTEXT: {context}" if context else ""}

Write the comparison using ONLY these section headers in ALL CAPS followed by a colon. Prose paragraphs only — no bullets, no markdown, no asterisks.

STATISTICAL EDGE:
Who wins each key category and why it matters in the context of winning basketball.

SCORING COMPARISON:
Style, efficiency, and volume differences between the two players written as a cohesive analysis.

TWO-WAY IMPACT:
Defensive value comparison. Who makes their team meaningfully better on both ends?

PLAYMAKING AND IQ:
Who is the better creator and decision-maker, and how large is the gap?

PHYSICAL AND AGE PROJECTION:
Body, athleticism, and trajectory differences. Who has more runway?

CONTRACT AND TRADE VALUE:
Who provides more value for the dollar right now and who would command more on the trade market?

BEST FIT CONTEXTS:
When and why would you want Player A over Player B and vice versa?

VERDICT:
Name the player you would take unambiguously in the first sentence. Then deliver two to three sentences of decisive reasoning."""


def trade_prompt(out: list[PlayerProfile], inc: list[PlayerProfile], context: str = "") -> str:
    def summarize(players):
        return "\n".join(
            f"{p.identity.name} ({p.identity.position}, {p.identity.team}) — "
            f"{p.ppg:.1f}pts / {p.rpg:.1f}reb / {p.apg:.1f}ast | "
            f"FG: {p.fg_pct:.1%} | TS: {f'{p.ts_pct:.1%}' if p.ts_pct else 'N/A'} | "
            f"{p.mpg:.0f} mpg | {p.gp} GP"
            for p in players
        )

    return f"""Evaluate this NBA trade proposal.

SENDING OUT:
{summarize(out)}

RECEIVING:
{summarize(inc)}

{f"FRONT OFFICE CONTEXT: {context}" if context else ""}

Write the evaluation using ONLY these section headers in ALL CAPS followed by a colon. Prose paragraphs only — no bullets, no markdown, no asterisks.

TRADE SUMMARY:
One sentence on what each side is trying to accomplish with this deal.

VALUE DELTA:
Who wins on raw production? Quantify the gap in plain language.

ROLE AND FIT ANALYSIS:
Do the incoming players actually fill a need? Will they fit the system and culture?

AGE AND TIMELINE:
Does this trade make sense for where each franchise is in their competitive window?

CONTRACT INTELLIGENCE:
Cap implications, trade exceptions, and future flexibility impact written as a paragraph.

RISK ASSESSMENT:
Injury history, fit concerns, and locker room considerations for both sides.

VERDICT:
State ACCEPT, REJECT, or COUNTER clearly in the first sentence. Include a confidence level of High, Medium, or Low. Then deliver one decisive paragraph explaining the recommendation."""


def team_prompt(team: TeamProfile, question: str | None = None) -> str:
    leaders = team.leaders
    roster_lines = "\n".join(
        f"  {p.identity.name} ({p.identity.position}): "
        f"{p.ppg:.1f}pts / {p.rpg:.1f}reb / {p.apg:.1f}ast | "
        f"FG: {p.fg_pct:.1%} | TS: {f'{p.ts_pct:.1%}' if p.ts_pct else 'N/A'} | {p.mpg:.0f}mpg"
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

Write the report using ONLY these section headers in ALL CAPS followed by a colon. Prose paragraphs only — no bullets, no markdown, no asterisks.

TEAM IDENTITY:
The defining characteristic of how this team plays and what they are built around.

OFFENSIVE SYSTEM:
Pace, spacing, creation hierarchy, and half-court execution written as a cohesive paragraph.

DEFENSIVE PROFILE:
Scheme, personnel fit, rim protection, and perimeter defense analysis.

ROSTER CONSTRUCTION GRADE:
How well this roster fits together, what the ceiling is, and assign a letter grade with justification.

DEPTH CHART ANALYSIS:
Starter quality versus bench depth. Where are the meaningful weaknesses?

INJURY VULNERABILITY:
Which players are injury risks and what the team looks like if they go down.

ROSTER GAPS:
What positions and skills are missing and what type of player would elevate this team.

OFFSEASON BLUEPRINT:
Three specific, actionable moves to improve this roster written as a prioritized paragraph."""


def chat_system(p: PlayerProfile) -> str:
    return f"""{SYSTEM}

You are currently in a focused analysis session on {p.identity.name} ({p.identity.team}, {p.identity.position}).

LOADED STATS ({p.season} season, {p.gp} games):
Scoring: {p.ppg:.1f} PPG | Rebounds: {p.rpg:.1f} | Assists: {p.apg:.1f} | Steals: {p.spg:.1f} | Blocks: {p.bpg:.1f}
Efficiency: FG {p.fg_pct:.1%} | 3PT {p.three_pct:.1%} | FT {p.ft_pct:.1%} | TS {f"{p.ts_pct:.1%}" if p.ts_pct else "N/A"}
Usage: {p.mpg:.0f} minutes per game

Answer all questions using this data as your factual foundation. Write in clean professional prose. No markdown, no bullet points, no asterisks. When speculating beyond the stats, say so explicitly."""


def roster_card_prompt(p: PlayerProfile) -> str:
    return f"""Generate a concise scouting card for {p.identity.name}.

STATS ({p.season} season, {p.gp} GP):
{p.ppg:.1f}pts / {p.rpg:.1f}reb / {p.apg:.1f}ast / {p.spg:.1f}stl / {p.bpg:.1f}blk
FG: {p.fg_pct:.1%} | 3PT: {p.three_pct:.1%} | FT: {p.ft_pct:.1%} | TS: {f"{p.ts_pct:.1%}" if p.ts_pct else "N/A"} | {p.mpg:.0f}mpg

Write the scouting card using ONLY these section headers in ALL CAPS followed by a colon. Two sentences maximum per section. No bullets, no markdown, no asterisks.

ROLE AND VALUE:
OFFENSIVE SKILL:
DEFENSIVE IMPACT:
VERDICT:
State BUY, HOLD, or SELL in the first word, then one sentence of decisive reasoning."""