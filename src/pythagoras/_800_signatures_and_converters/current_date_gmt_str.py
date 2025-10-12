from datetime import datetime, timezone
from typing import Final

_MONTH_ABBREVIATIONS: Final[tuple[str, ...]] = (
    "Jan", "Feb", "Mar", "Apr", "May", "Jun",
    "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")


def current_date_gmt_string() -> str:
    """Get the current UTC date as a compact string.

    Produces an underscore-delimited UTC date string suitable for
    stable file names and log records.

    The format is: "YYYY_MMMonAbbrev_dd_utc" (e.g., "2024_12Dec_11_utc").

    Returns:
        str: The formatted UTC date string, for the current moment.
    """

    utc_now = datetime.now(timezone.utc)
    month_abbrev = _MONTH_ABBREVIATIONS[utc_now.month - 1]
    # locale-dependent month abbreviation
    result =  (f"{utc_now.year}_{utc_now.month:02d}{month_abbrev}" +
              f"_{utc_now.day:02d}_utc")
    return result