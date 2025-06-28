from pythagoras._800_signatures_and_converters.current_date_gmt_str import (
    current_date_gmt_string)

from datetime import datetime, timezone

def test_current_date_gmt_string():
    # Call the function to get the current date and time
    result_1 = current_date_gmt_string()
    day = datetime.now(timezone.utc).strftime("%d")
    month_number = datetime.now(timezone.utc).strftime("%m")
    month_str = datetime.now(timezone.utc).strftime("%b")
    year = datetime.now(timezone.utc).strftime("%Y")

    result_2 = current_date_gmt_string()

    assert "utc" in result_1 and "utc" in result_2
    assert day in result_1 or day in result_2
    assert month_number in result_1 or month_number in result_2
    assert month_str in result_1 or month_str in result_2

