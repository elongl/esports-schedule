import re
from datetime import date, datetime, timedelta
from enum import Enum
from typing import Any
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from pydantic import BaseModel, ValidationError, field_validator, model_validator

import monitoring
from game import Game

# Feb 10, 2024
_DATE_PATTERN_SAME_DAY = r"(\w+) (\d+), (\d+)"
# Jun 05 - 09, 2024
_DATE_PATTERN_SAME_MONTH = r"(\w+) (\d+) - (\d+), (\d+)"
# May 27 - Jun 02, 2024
_DATE_PATTERN_DIFF_MONTH = r"(\w+) (\d+) - (\w+) (\d+), (\d+)"


class TournamentTier(Enum):
    S = "S-Tier"
    A = "A-Tier"


class Tournament(BaseModel):
    title: str
    start_date: date
    end_date: date
    prize: str
    team_count_description: str
    location: str
    url: str
    tier: TournamentTier

    @field_validator("*")
    def _clean_str(cls, value: Any) -> Any:
        if isinstance(value, str):
            return value.strip()
        return value

    @field_validator("prize", "location", "team_count_description")
    def _default_TBA(cls, value: str) -> str:
        return value or "TBA"

    @model_validator(mode="before")
    def _parse_dates(cls, values: dict) -> dict:
        date = values.pop("date")

        match = re.match(_DATE_PATTERN_SAME_DAY, date)
        if match:
            month, day, year = match.groups()
            values["start_date"] = datetime.strptime(
                f"{month} {day}, {year}", "%b %d, %Y"
            ).date()
            values["end_date"] = values["start_date"] + timedelta(days=1)
            return values

        match = re.match(_DATE_PATTERN_SAME_MONTH, date)
        if match:
            month, start_day, end_day, year = match.groups()
            values["start_date"] = datetime.strptime(
                f"{month} {start_day}, {year}", "%b %d, %Y"
            ).date()
            values["end_date"] = (
                datetime.strptime(f"{month} {end_day}, {year}", "%b %d, %Y")
                + timedelta(days=1)
            ).date()
            return values

        match = re.match(_DATE_PATTERN_DIFF_MONTH, date)
        if match:
            start_month, start_day, end_month, end_day, year = match.groups()
            values["start_date"] = datetime.strptime(
                f"{start_month} {start_day}, {year}", "%b %d, %Y"
            ).date()
            values["end_date"] = (
                datetime.strptime(f"{end_month} {end_day}, {year}", "%b %d, %Y")
                + timedelta(days=1)
            ).date()
            return values

        raise ValueError(f"Invalid date format: {date}")


class TournamentDivClassSelectors(BaseModel):
    table: list[str]
    row: list[str]
    row_title: list[str]
    row_date: list[str]
    row_prize: list[str]
    row_team_count: list[str]
    row_location: list[str]


_DIV_CLASS_IDS_PRESET1 = TournamentDivClassSelectors(
    table=["gridTable", "tournamentCard"],
    row=["gridRow"],
    row_title=["gridCell", "Tournament", "Header"],
    row_date=["gridCell", "EventDetails", "Date", "Header"],
    row_prize=["gridCell", "EventDetails", "Prize", "Header"],
    row_team_count=["gridCell", "EventDetails", "PlayerNumber", "Header"],
    row_location=["gridCell", "EventDetails", "Location", "Header"],
)
_DIV_CLASS_IDS_PRESET2 = TournamentDivClassSelectors(
    table=["divTable"],
    row=["divRow"],
    row_title=["divCell", "Tournament"],
    row_date=["divCell", "EventDetails-Left-55"],
    row_prize=["divCell", "EventDetails-Right-45"],
    row_team_count=["divCell", "EventDetails-Right-40"],
    row_location=["divCell", "EventDetails-Left-60"],
)


class TournamentsApi:
    _DATASOURCE_URL = "https://liquipedia.net"
    _TOURNAMENTS_URL_MAP = {
        Game.COUNTER_STRIKE: {
            TournamentTier.S: "/counterstrike/S-Tier_Tournaments",
            TournamentTier.A: "/counterstrike/A-Tier_Tournaments",
        },
        Game.ROCKET_LEAGUE: {
            TournamentTier.S: "/rocketleague/S-Tier_Tournaments",
            TournamentTier.A: "/rocketleague/A-Tier_Tournaments",
        },
        Game.LEAGUE_OF_LEGENDS: {
            TournamentTier.S: "/leagueoflegends/S-Tier_Tournaments",
            TournamentTier.A: "/leagueoflegends/A-Tier_Tournaments",
        },
        Game.VALORANT: {
            TournamentTier.S: "/valorant/S-Tier_Tournaments",
            TournamentTier.A: "/valorant/A-Tier_Tournaments",
        },
        Game.DOTA2: {
            TournamentTier.S: "/dota2/Tier_1_Tournaments",
            TournamentTier.A: "/dota2/Tier_2_Tournaments",
        },
        Game.APEX_LEGENDS: {
            TournamentTier.S: "/apexlegends/S-Tier_Tournaments",
            TournamentTier.A: "/apexlegends/A-Tier_Tournaments",
        },
    }

    _GAME_DIV_CLASS_MAP = {
        Game.COUNTER_STRIKE: _DIV_CLASS_IDS_PRESET1,
        Game.VALORANT: _DIV_CLASS_IDS_PRESET1,
        Game.DOTA2: _DIV_CLASS_IDS_PRESET1,
        Game.ROCKET_LEAGUE: _DIV_CLASS_IDS_PRESET2,
        Game.LEAGUE_OF_LEGENDS: _DIV_CLASS_IDS_PRESET2,
        Game.APEX_LEGENDS: _DIV_CLASS_IDS_PRESET2,
    }

    def __init__(self, game: Game) -> None:
        self.game = game

    def get(self) -> list[Tournament]:
        tournaments = []
        for tier, url in self._TOURNAMENTS_URL_MAP[self.game].items():
            resp = requests.get(urljoin(self._DATASOURCE_URL, url))
            resp.raise_for_status()
            html = BeautifulSoup(resp.content, "html.parser")
            tournaments.extend(self._parse_html(html, tier))

        if not tournaments:
            raise ValueError("No tournaments found.")
        return tournaments

    def _parse_html(
        self,
        html: BeautifulSoup,
        tier: TournamentTier,
    ) -> list[Tournament]:
        tournaments = []
        tournament_tables = self._find_divs_with_classes(
            html,
            self._GAME_DIV_CLASS_MAP[self.game].table,
        )
        if not tournament_tables:
            raise ValueError("No tournaments found.")

        for tournament_table in tournament_tables:
            tournament_rows = self._find_divs_with_classes(
                tournament_table,
                self._GAME_DIV_CLASS_MAP[self.game].row,
            )
            for tournament_row in tournament_rows:
                try:
                    tournaments.append(self._parse_row(tournament_row, tier))
                except ValidationError:
                    monitoring.report_error()

        return tournaments

    def _parse_row(
        self,
        tournament_row: BeautifulSoup,
        tier: TournamentTier,
    ) -> Tournament:
        title = self._locate_title(tournament_row)
        date = self._find_div_with_classes(
            tournament_row,
            self._GAME_DIV_CLASS_MAP[self.game].row_date,
        )
        prize = self._find_div_with_classes(
            tournament_row,
            self._GAME_DIV_CLASS_MAP[self.game].row_prize,
        )
        team_count = self._find_div_with_classes(
            tournament_row,
            self._GAME_DIV_CLASS_MAP[self.game].row_team_count,
        )
        location = self._find_div_with_classes(
            tournament_row,
            self._GAME_DIV_CLASS_MAP[self.game].row_location,
        )
        url = urljoin(self._DATASOURCE_URL, title["href"])

        return Tournament(
            title=title.text,
            date=date.text,
            prize=prize.text if prize else None,
            team_count_description=team_count.text,
            location=location.text,
            url=url,
            tier=tier,
        )

    def _locate_title(self, tournament_row: BeautifulSoup) -> BeautifulSoup:
        title = self._find_div_with_classes(
            tournament_row,
            self._GAME_DIV_CLASS_MAP[self.game].row_title,
        )
        potential_titles = title.find_all("a")
        for potential_title in potential_titles:
            if potential_title.parent.name == "span":
                continue
            return potential_title

    def _find_divs_with_classes(
        self,
        element: BeautifulSoup,
        classes: list[str],
    ) -> list[BeautifulSoup]:
        """
        Finds div elements with *all* the given classes.
        """
        matching_divs = []
        divs_to_check = element.find_all("div", class_=classes)
        for potential_div in divs_to_check:
            if all(cls in potential_div["class"] for cls in classes):
                matching_divs.append(potential_div)
        return matching_divs

    def _find_div_with_classes(
        self,
        element: BeautifulSoup,
        classes: list[str],
    ) -> BeautifulSoup:
        matching_elements = self._find_divs_with_classes(element, classes)
        if len(matching_elements) != 1:
            raise ValueError("Failed to locate element.")
        return matching_elements[0]
