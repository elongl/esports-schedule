from datetime import datetime

from icalendar import Calendar, Event

from tournaments_api import Tournament

_EVENT_DESCRIPTION = """
Hello world
"""


class TournamentsCalendar:
    def __init__(self, tournaments: list[Tournament]):
        self.tournaments = tournaments

    def get_ical(self) -> str:
        cal = Calendar()
        for tournament in self.tournaments:
            event = Event()
            event.add("summary", tournament.title)
            event.add("dtstart", tournament.start_date)
            event.add("dtend", tournament.end_date)
            event.add("dtstamp", datetime.now())
            event.add("uid", id(tournament.title))
            event.add("location", tournament.location)
            event.add("url", tournament.url)
            event.add("description", _EVENT_DESCRIPTION)
            cal.add_component(event)
        return cal.to_ical()

    def write_ical(self, path: str) -> None:
        with open(path, "wb") as f:
            f.write(self.get_ical())
