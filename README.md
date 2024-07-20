# Esports Schedule

Esports tournaments and events in your calendar.

## Setup

```sh
pip install -r dev-requirements.txt -r requirements.txt
pre-commit install
```

## Running

### Server

```sh
fastapi dev main_server.py
```

### CLI

```sh
python main_cli.py <GAME>
```

## Testing

```sh
pytest -vvv
```
