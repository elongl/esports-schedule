from fastapi import FastAPI, Response

from tournaments_api import TournamentsApi
from tournaments_calendar import TournamentsCalendar

app = FastAPI()


@app.get("/")
async def root():
    tournaments = TournamentsApi().get()
    calendar = TournamentsCalendar(tournaments)
    return Response(content=calendar.get_ical(), media_type="text/calendar")
