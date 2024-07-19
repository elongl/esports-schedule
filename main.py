from tournaments_api import TournamentsApi


def main():
    tournaments = TournamentsApi().get()


if __name__ == "__main__":
    main()
