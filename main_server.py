import time
from functools import lru_cache

from fastapi import FastAPI, Response

from tournaments_api import TournamentsApi
from tournaments_calendar import TournamentsCalendar

app = FastAPI()


def get_ttl_hash(seconds=3600):
    # Returns a unique hash based on current time, updated every 'seconds'.
    return round(time.time() / seconds)


@lru_cache(maxsize=1)
def get_calendar(ttl_hash=None):
    tournaments = TournamentsApi().get()
    calendar = TournamentsCalendar(tournaments)
    return calendar.get_ical()


@app.get("/")
async def root():
    return Response(
        content=get_calendar(ttl_hash=get_ttl_hash()),
        media_type="text/calendar",
    )
