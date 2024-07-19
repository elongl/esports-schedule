from bs4 import BeautifulSoup
from pydantic import BaseModel, field_validator
import requests


class Tournament(BaseModel):
    title: str
    date: str
    prize: str
    team_count_description: str
    location: str

    @field_validator("*")
    def _clean_str(cls, value: str) -> str:
        return value.strip()


class TournamentsApi:
    _TOURNAMENTS_URL = "https://liquipedia.net/counterstrike/S-Tier_Tournaments"

    def get(self) -> list[Tournament]:
        resp = requests.get(TournamentsApi._TOURNAMENTS_URL)
        html = BeautifulSoup(resp.content, "html.parser")
        return self._parse_html(html)

    def _parse_html(self, html: BeautifulSoup) -> list[Tournament]:
        tournaments = []
        tournament_tables = html.find_all("div", class_=["gridTable", "tournamentCard"])
        for tournament_table in tournament_tables:
            for tournament_row in tournament_table.find_all("div", class_="gridRow"):
                tournaments.append(self._parse_row(tournament_row))
        return tournaments

    def _parse_row(self, tournament_row: BeautifulSoup) -> Tournament:
        title = tournament_row.find("div", class_="gridCell Tournament Header")
        date = tournament_row.find("div", class_="gridCell EventDetails Date Header")
        prize = tournament_row.find("div", class_="gridCell EventDetails Prize Header")
        team_count = tournament_row.find(
            "div", class_="gridCell EventDetails PlayerNumber Header"
        )
        location = tournament_row.find(
            "div", class_="gridCell EventDetails Location Header"
        )
        return Tournament(
            title=title.text,
            date=date.text,
            prize=prize.text if prize else "TBA",
            team_count_description=team_count.text,
            location=location.text,
        )
