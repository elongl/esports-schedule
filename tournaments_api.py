import re
from datetime import datetime
from typing import Any
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from pydantic import BaseModel, field_validator, model_validator


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
        # Examples:
        # Jun 05 - 09, 2024
        # May 27 - Jun 02, 2024
        date = values.pop("date")
        date_pattern_same_month = r"(\w+) (\d+) - (\d+), (\d+)"
        match = re.match(date_pattern_same_month, date)
        if match:
            month, start_day, end_day, year = match.groups()
            values["start_date"] = datetime.strptime(
                f"{month} {start_day}, {year}", "%b %d, %Y"
            )
            values["end_date"] = datetime.strptime(
                f"{month} {end_day}, {year}", "%b %d, %Y"
            )
            return values

        date_pattern_diff_month = r"(\w+) (\d+) - (\w+) (\d+), (\d+)"
        match = re.match(date_pattern_diff_month, date)
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
    _TOURNAMENTS_URL = urljoin(_DATASOURCE_URL, "/counterstrike/S-Tier_Tournaments")

    def get(self) -> list[Tournament]:
        resp = requests.get(TournamentsApi._TOURNAMENTS_URL)
        html = BeautifulSoup(resp.content, "html.parser")
        return self._parse_html(html)

    def _parse_html(self, html: BeautifulSoup) -> list[Tournament]:
        tournaments = []
        tournament_tables = html.find_all("div", class_=["gridTable", "tournamentCard"])
        if not tournament_tables:
            raise ValueError("No tournaments found.")

        for tournament_table in tournament_tables:
            tournament_rows = tournament_table.find_all("div", class_="gridRow")
            if not tournament_rows:
                raise ValueError("No tournament rows found.")

            for tournament_row in tournament_rows:
                tournaments.append(self._parse_row(tournament_row))

        return tournaments

    def _parse_row(self, tournament_row: BeautifulSoup) -> Tournament:
        title = (
            tournament_row.find("div", class_="gridCell Tournament Header")
            .find("b")
            .find("a")
        )
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
