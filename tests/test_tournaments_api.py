import pytest

from game import Game
from tournaments_api import TournamentsApi


@pytest.mark.parametrize("game", Game)
def test_tournaments_api(game: Game):
    TournamentsApi(game).get()
