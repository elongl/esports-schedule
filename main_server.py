import os
import time
from functools import lru_cache

from fastapi import FastAPI, Response

from game import GAME_VALUES, Game
from tournaments_api import TournamentsApi
from tournaments_calendar import TournamentsCalendar

SENTRY_DSN = os.getenv("SENTRY_DSN")

if SENTRY_DSN:
    import sentry_sdk

    sentry_sdk.init(
        dsn=SENTRY_DSN,
        traces_sample_rate=1.0,
        profiles_sample_rate=1.0,
    )

app = FastAPI()


def get_ttl_hash(seconds=3600):
    # Returns a unique hash based on current time, updated every 'seconds'.
    return round(time.time() / seconds)


@lru_cache
def get_calendar(game: Game, ttl_hash=None):
    tournaments = TournamentsApi(game).get()
    calendar = TournamentsCalendar(tournaments)
    return calendar.get_ical()


@app.get("/calendar/{game}")
async def calendar(game: Game):
    return Response(
        content=get_calendar(game, ttl_hash=get_ttl_hash()),
        media_type="text/calendar",
    )


@app.get("/")
async def root():
    return f"Use /calendar/{{game}} where 'game' is one of: {GAME_VALUES}."


@app.get("/error-debug")
async def trigger_error():
    return 1 / 0
