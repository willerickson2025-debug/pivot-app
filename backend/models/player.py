from __future__ import annotations
from typing import Optional
from pydantic import BaseModel, field_validator, model_validator


def _f(v) -> float:
    try:
        return float(v) if v is not None else 0.0
    except (TypeError, ValueError):
        return 0.0


class PlayerIdentity(BaseModel):
    player_id: int
    name: str
    first_name: str = ""
    last_name: str = ""
    position: str = "N/A"
    team: str = "N/A"
    team_id: Optional[int] = None
    country: str = "USA"
    height: Optional[str] = None
    weight_lbs: Optional[int] = None
    jersey_number: Optional[str] = None
    years_of_experience: Optional[int] = None
    draft_year: Optional[int] = None
    draft_round: Optional[int] = None
    draft_number: Optional[int] = None

    @field_validator("name", "position", "team", mode="before")
    @classmethod
    def clean_str(cls, v):
        return str(v).strip() if v else "N/A"


class SeasonStats(BaseModel):
    season: int = 2025
    games_played: int = 0
    minutes_per_game: float = 0.0
    points_per_game: float = 0.0
    rebounds_per_game: float = 0.0
    offensive_rebounds: float = 0.0
    defensive_rebounds: float = 0.0
    assists_per_game: float = 0.0
    steals_per_game: float = 0.0
    blocks_per_game: float = 0.0
    turnovers_per_game: float = 0.0
    personal_fouls: float = 0.0
    field_goals_made: float = 0.0
    field_goals_attempted: float = 0.0
    field_goal_pct: float = 0.0
    three_point_made: float = 0.0
    three_point_attempted: float = 0.0
    three_point_pct: float = 0.0
    free_throws_made: float = 0.0
    free_throws_attempted: float = 0.0
    free_throw_pct: float = 0.0
    true_shooting_pct: Optional[float] = None
    assist_to_turnover: Optional[float] = None

    @model_validator(mode="after")
    def derive(self) -> SeasonStats:
        if not self.true_shooting_pct:
            denom = 2 * (self.field_goals_attempted + 0.44 * self.free_throws_attempted)
            if denom > 0:
                self.true_shooting_pct = round(self.points_per_game / denom, 4)
        if not self.assist_to_turnover and self.turnovers_per_game > 0:
            self.assist_to_turnover = round(self.assists_per_game / self.turnovers_per_game, 2)
        return self


class PlayerProfile(BaseModel):
    identity: PlayerIdentity
    stats: SeasonStats
    season: int = 2025

    @property
    def ppg(self): return self.stats.points_per_game
    @property
    def rpg(self): return self.stats.rebounds_per_game
    @property
    def apg(self): return self.stats.assists_per_game
    @property
    def spg(self): return self.stats.steals_per_game
    @property
    def bpg(self): return self.stats.blocks_per_game
    @property
    def tov(self): return self.stats.turnovers_per_game
    @property
    def fg_pct(self): return self.stats.field_goal_pct
    @property
    def three_pct(self): return self.stats.three_point_pct
    @property
    def ft_pct(self): return self.stats.free_throw_pct
    @property
    def ts_pct(self): return self.stats.true_shooting_pct
    @property
    def mpg(self): return self.stats.minutes_per_game
    @property
    def gp(self): return self.stats.games_played

    @classmethod
    def build(cls, player_data: dict, raw_stats: dict, season: int) -> PlayerProfile:
        team_info = player_data.get("team") or {}
        team_name = (
            team_info.get("full_name")
            or team_info.get("name")
            or "N/A"
        )

        def parse_minutes(m) -> float:
            if not m:
                return 0.0
            if isinstance(m, str) and ":" in m:
                parts = m.split(":")
                return round(float(parts[0]) + float(parts[1]) / 60, 2)
            return _f(m)

        identity = PlayerIdentity(
            player_id=player_data["id"],
            name=f"{player_data.get('first_name','')} {player_data.get('last_name','')}".strip(),
            first_name=player_data.get("first_name", ""),
            last_name=player_data.get("last_name", ""),
            position=player_data.get("position") or "N/A",
            team=team_name,
            team_id=team_info.get("id"),
            country=player_data.get("country") or "USA",
            height=player_data.get("height"),
            weight_lbs=player_data.get("weight"),
            jersey_number=player_data.get("jersey_number"),
            years_of_experience=player_data.get("years_experience"),
            draft_year=player_data.get("draft_year"),
            draft_round=player_data.get("draft_round"),
            draft_number=player_data.get("draft_number"),
        )

        stats = SeasonStats(
            season=season,
            games_played=int(raw_stats.get("games_played", 0) or 0),
            minutes_per_game=parse_minutes(raw_stats.get("min")),
            points_per_game=_f(raw_stats.get("pts")),
            rebounds_per_game=_f(raw_stats.get("reb")),
            offensive_rebounds=_f(raw_stats.get("oreb")),
            defensive_rebounds=_f(raw_stats.get("dreb")),
            assists_per_game=_f(raw_stats.get("ast")),
            steals_per_game=_f(raw_stats.get("stl")),
            blocks_per_game=_f(raw_stats.get("blk")),
            turnovers_per_game=_f(raw_stats.get("turnover")),
            personal_fouls=_f(raw_stats.get("pf")),
            field_goals_made=_f(raw_stats.get("fgm")),
            field_goals_attempted=_f(raw_stats.get("fga")),
            field_goal_pct=_f(raw_stats.get("fg_pct")),
            three_point_made=_f(raw_stats.get("fg3m")),
            three_point_attempted=_f(raw_stats.get("fg3a")),
            three_point_pct=_f(raw_stats.get("fg3_pct")),
            free_throws_made=_f(raw_stats.get("ftm")),
            free_throws_attempted=_f(raw_stats.get("fta")),
            free_throw_pct=_f(raw_stats.get("ft_pct")),
        )

        return cls(identity=identity, stats=stats, season=season)


class TeamProfile(BaseModel):
    team: str
    abbreviation: str
    season: int
    roster: list[PlayerProfile]
    roster_size: int = 0

    @model_validator(mode="after")
    def set_size(self):
        self.roster_size = len(self.roster)
        return self

    @property
    def top_scorers(self):
        return sorted(self.roster, key=lambda p: p.ppg, reverse=True)[:5]

    @property
    def leaders(self):
        if not self.roster:
            return {}
        return {
            "scoring": max(self.roster, key=lambda p: p.ppg),
            "rebounding": max(self.roster, key=lambda p: p.rpg),
            "assists": max(self.roster, key=lambda p: p.apg),
            "defense": max(self.roster, key=lambda p: p.spg + p.bpg),
            "efficiency": max(self.roster, key=lambda p: p.ts_pct or 0),
        }