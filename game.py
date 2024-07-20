from enum import Enum


class Game(Enum):
    COUNTER_STRIKE = "counterstrike"
    ROCKET_LEAGUE = "rocketleague"
    LEAGUE_OF_LEGENDS = "leagueoflegends"
    VALORANT = "valorant"
    DOTA2 = "dota2"
    APEX_LEGENDS = "apexlegends"


GAME_VALUES = [game.value for game in Game]
