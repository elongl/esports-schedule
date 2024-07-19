import re
from datetime import datetime
from typing import Any
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from pydantic import BaseModel, field_validator, model_validator

from game import Game

# Feb 10, 2024
_DATE_PATTERN_SAME_DAY = r"(\w+) (\d+), (\d+)"
# Jun 05 - 09, 2024
_DATE_PATTERN_SAME_MONTH = r"(\w+) (\d+) - (\d+), (\d+)"
# May 27 - Jun 02, 2024
_DATE_PATTERN_DIFF_MONTH = r"(\w+) (\d+) - (\w+) (\d+), (\d+)"


class Tournament(BaseModel):
    title: str
    start_date: datetime
    end_date: datetime
    prize: str
    team_count_description: str
    location: str
    url: str

    @field_validator("*")
    def _clean_str(cls, value: Any) -> Any:
        if isinstance(value, str):
            return value.strip()
        return value

    @model_validator(mode="before")
    def _parse_dates(cls, values: dict) -> dict:
        date = values.pop("date")

        match = re.match(_DATE_PATTERN_SAME_DAY, date)
        if match:
            month, day, year = match.groups()
            values["start_date"] = datetime.strptime(
                f"{month} {day}, {year}", "%b %d, %Y"
            )
            values["end_date"] = values["start_date"]
            return values

        match = re.match(_DATE_PATTERN_SAME_MONTH, date)
        if match:
            month, start_day, end_day, year = match.groups()
            values["start_date"] = datetime.strptime(
                f"{month} {start_day}, {year}", "%b %d, %Y"
            )
            values["end_date"] = datetime.strptime(
                f"{month} {end_day}, {year}", "%b %d, %Y"
            )
            return values

        match = re.match(_DATE_PATTERN_DIFF_MONTH, date)
        if match:
            start_month, start_day, end_month, end_day, year = match.groups()
            values["start_date"] = datetime.strptime(
                f"{start_month} {start_day}, {year}", "%b %d, %Y"
            )
            values["end_date"] = datetime.strptime(
                f"{end_month} {end_day}, {year}", "%b %d, %Y"
            )
            return values

        raise ValueError(f"Invalid date format: {date}")


class TournamentsApi:
    _DATASOURCE_URL = "https://liquipedia.net"
    _TOURNAMENTS_URL_MAP = {
        Game.COUNTER_STRIKE: "/counterstrike/S-Tier_Tournaments",
        Game.ROCKET_LEAGUE: "/rocketleague/S-Tier_Tournaments",
        Game.LEAGUE_OF_LEGENDS: "/leagueoflegends/S-Tier_Tournaments",
        Game.VALORANT: "/valorant/S-Tier_Tournaments",
        Game.DOTA2: "/dota2/Tier_1_Tournaments",
        Game.APEX_LEGENDS: "/apexlegends/S-Tier_Tournaments",
    }

    def __init__(self, game: Game) -> None:
        self.game = game

    def get(self) -> list[Tournament]:
        resp = requests.get(
            urljoin(
                self._DATASOURCE_URL,
                self._TOURNAMENTS_URL_MAP[self.game],
            )
        )
        resp.raise_for_status()
        html = BeautifulSoup(resp.content, "html.parser")
        return self._parse_html(html)

    def _parse_html(self, html: BeautifulSoup) -> list[Tournament]:
        tournaments = []
        tournament_tables = html.find_all(
            "div", class_=["tournamentCard", "tournament-card"]
        )
        if not tournament_tables:
            raise ValueError("No tournaments found.")

        for tournament_table in tournament_tables:
            tournament_rows = tournament_table.find_all(
                "div", class_=["gridRow", "divRow"]
            )
            if not tournament_rows:
                raise ValueError("No tournament rows found.")

            for tournament_row in tournament_rows:
                tournaments.append(self._parse_row(tournament_row))

        return tournaments

    def _parse_row(self, tournament_row: BeautifulSoup) -> Tournament:
        title = self._locate_title(tournament_row)
        date = tournament_row.find("div", class_="gridCell EventDetails Date Header")
        prize = tournament_row.find("div", class_="gridCell EventDetails Prize Header")
        team_count = tournament_row.find(
            "div", class_="gridCell EventDetails PlayerNumber Header"
        )
        location = tournament_row.find(
            "div", class_="gridCell EventDetails Location Header"
        )
        url = urljoin(self._DATASOURCE_URL, title["href"])

        return Tournament(
            title=title.text,
            date=date.text,
            prize=prize.text if prize else "TBA",
            team_count_description=team_count.text,
            location=location.text,
            url=url,
        )

    @staticmethod
    def _locate_title(tournament_row: BeautifulSoup) -> BeautifulSoup:
        potential_titles = tournament_row.find(
            "div", class_="gridCell Tournament Header"
        ).find_all("a")

        for potential_title in potential_titles:
            if potential_title.parent.name == "span":
                continue
            return potential_title
