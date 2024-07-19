from tournaments_api import TournamentsApi
from tournaments_calendar import TournamentsCalendar


def main():
    tournaments = TournamentsApi().get()
    calendar = TournamentsCalendar(tournaments)
    calendar.write_ical("tournaments.ics")


if __name__ == "__main__":
    main()
