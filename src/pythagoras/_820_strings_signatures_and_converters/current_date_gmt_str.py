from datetime import datetime, timezone


def current_date_gmt_string():
    """ Return the current date and time in the format '2024_12Jan_22_utc'
    """

    utc_now = datetime.now(timezone.utc)
    date_str = utc_now.strftime("%Y_%m%b_%d_utc")

    return date_str