from .config import DatePickerOptions
from whenever import (
    Instant,
    days,
    months,
    years,
)

def get_relative_date(delta: DatePickerOptions) -> str:
    if delta == "Past 24 Hours":
        time_delta = days(1)
    elif delta == "Past 7 days":
        time_delta = days(7)
    elif delta == "Past 1 Month":
        time_delta = months(1)
    elif delta == "Past 2 Months":
        time_delta = months(2)
    elif delta == "Full":
        time_delta = years(1)

    now = Instant.now().to_tz("Asia/Kolkata")
    cutoff_date = now - time_delta
    cutoff_date = cutoff_date.py_datetime().strftime("%Y-%m-%d")
    return cutoff_date


if __name__ == "__main__":
    # Test the function
    print(get_relative_date("Past 24 Hours"))
    print(get_relative_date("Past 7 days"))
    print(get_relative_date("Past 1 Month"))
    print(get_relative_date("Past 2 Months"))
    print(get_relative_date("Full"))