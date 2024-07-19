import sys

from game import Game
from tournaments_api import TournamentsApi
from tournaments_calendar import TournamentsCalendar


def main():
    if len(sys.argv) != 2:
        print("Usage: python main_cli.py <game>")
        return

    game = Game(sys.argv[1])
    tournaments = TournamentsApi(game).get()
    calendar = TournamentsCalendar(tournaments)
    calendar.write_ical(f"{game.value}_tournaments.ics")


if __name__ == "__main__":
    main()
