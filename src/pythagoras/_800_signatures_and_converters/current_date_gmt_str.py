from datetime import datetime, timezone


def current_date_gmt_string() -> str:
    """Get the current UTC date as a compact string.

    Produces a lowercase, underscore-delimited UTC date string suitable for
    stable file names and log records.

    The format is: "YYYY_MonAbbrev_dd_utc" (e.g., "2024_Dec_11_utc").

    Returns:
        str: The formatted UTC date string, for the current moment.
    """

    utc_now = datetime.now(timezone.utc)
    date_str = utc_now.strftime("%Y_%m%b_%d_utc")

    return date_str