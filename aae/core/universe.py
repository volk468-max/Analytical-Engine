
import json
from pathlib import Path


UNIVERSE_FILE = (
    Path(__file__).resolve().parents[1]
    / "config"
    / "Universe.json"
)


def get_universe_symbols() -> list[str]:
    """Return the investment universe from Universe.json."""

    with UNIVERSE_FILE.open(
        "r",
        encoding="utf-8",
    ) as file:
        data = json.load(file)

    symbols = data.get("symbols")

    if not isinstance(symbols, list):
        raise ValueError(
            "Universe.json must contain a symbols list"
        )

    result = []

    for symbol in symbols:
        if not isinstance(symbol, str):
            raise ValueError(
                "Every universe symbol must be a string"
            )

        symbol = symbol.strip().upper()

        if not symbol:
            raise ValueError(
                "Universe contains an empty symbol"
            )

        if symbol in result:
            raise ValueError(
                f"Duplicate universe symbol: {symbol}"
            )

        result.append(symbol)

    if not result:
        raise ValueError(
            "Investment universe cannot be empty"
        )

    return result
