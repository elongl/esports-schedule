from tournaments_api import Tournament, TournamentTier
from tournaments_calendar import TournamentsCalendar

_TOURNAMENTS = [
    Tournament(
        title="Mock Tournament",
        date="Nov 30 - Dec 15, 2024",
        prize="Mock Prize",
        team_count_description="Mock Team Count",
        location="Mock Location",
        url="https://example.com",
        tier=TournamentTier.S,
    ),
    Tournament(
        title="Mock Tournament",
        date="Jun 05 - 09, 2024",
        prize="Mock Prize",
        team_count_description="Mock Team Count",
        location="Mock Location",
        url="https://example.com",
        tier=TournamentTier.S,
    ),
    Tournament(
        title="Mock Tournament",
        date="May 27 - Jun 02, 2024",
        prize="Mock Prize",
        team_count_description="Mock Team Count",
        location="Mock Location",
        url="https://example.com",
        tier=TournamentTier.S,
    ),
]


def test_tournaments_calendar():
    TournamentsCalendar(_TOURNAMENTS).get_ical()
