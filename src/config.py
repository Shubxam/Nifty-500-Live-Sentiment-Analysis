# convert this Literals into enums

from typing import Literal

IndexType = Literal["nifty_50", "nifty_100", "nifty_200", "nifty_500"]

UNIVERSE_NAMES_DICT: dict[str, str] = {
    "nifty_50": "NIFTY 50",
    "nifty_100": "NIFTY 100",
    "nifty_200": "NIFTY 200",
    "nifty_500": "NIFTY 500",
}

DatePickerOptions = Literal[
    "Past 24 Hours",
    "Past 7 days",
    "Past 1 Month",
    "Past 2 Months",
    "Full",
]

TREEMAP_COLOR_SCALE = ["#FF0000", "#000000", "#00FF00"]