from pythagoras._110_supporting_utilities.current_date_gmt_str import (
    current_date_gmt_string, _MONTH_ABBREVIATIONS)

from datetime import datetime, timezone
import re
from unittest.mock import patch


def test_current_date_gmt_string_format():
    """Test that the output matches the expected format exactly."""
    result = current_date_gmt_string()
    
    # Format should be: YYYY_MMMonAbbrev_dd_utc (e.g., "2024_12Dec_11_utc")
    pattern = r'^\d{4}_\d{2}[A-Z][a-z]{2}_\d{2}_utc$'
    assert re.match(pattern, result), f"Format mismatch: {result}"
    
    # Verify it ends with _utc
    assert result.endswith("_utc"), f"Should end with '_utc': {result}"
    
    # Verify underscores are in correct positions
    parts = result.split("_")
    assert len(parts) == 4, f"Should have 4 parts separated by underscores: {result}"
    assert parts[3] == "utc", f"Last part should be 'utc': {result}"


def test_current_date_gmt_string_current_values():
    """Test that the output contains correct current date values."""
    result = current_date_gmt_string()
    utc_now = datetime.now(timezone.utc)
    
    # Extract components
    year = str(utc_now.year)
    month_num = f"{utc_now.month:02d}"
    month_abbrev = _MONTH_ABBREVIATIONS[utc_now.month - 1]
    day = f"{utc_now.day:02d}"
    
    # Verify each component is present
    assert result.startswith(year), f"Should start with year {year}: {result}"
    assert month_num in result, f"Should contain month number {month_num}: {result}"
    assert month_abbrev in result, f"Should contain month abbreviation {month_abbrev}: {result}"
    assert day in result, f"Should contain day {day}: {result}"
    
    # Verify exact format
    expected_format = f"{year}_{month_num}{month_abbrev}_{day}_utc"
    assert result == expected_format, f"Expected {expected_format}, got {result}"


def test_current_date_gmt_string_all_months():
    """Test that all 12 months produce valid output with correct abbreviations."""
    expected_abbrevs = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                        "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    
    for month in range(1, 13):
        # Mock a datetime for each month
        mock_date = datetime(2024, month, 15, 12, 30, 45, tzinfo=timezone.utc)
        
        with patch('pythagoras._110_supporting_utilities.current_date_gmt_str.datetime') as mock_datetime:
            mock_datetime.now.return_value = mock_date
            result = current_date_gmt_string()
            
            # Verify the month abbreviation is correct
            expected_abbrev = expected_abbrevs[month - 1]
            assert expected_abbrev in result, f"Month {month} should contain {expected_abbrev}: {result}"
            
            # Verify exact format
            expected = f"2024_{month:02d}{expected_abbrev}_15_utc"
            assert result == expected, f"Month {month}: expected {expected}, got {result}"


def test_current_date_gmt_string_edge_cases():
    """Test edge cases like first and last day of month, year boundaries."""
    test_cases = [
        (datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc), "2024_01Jan_01_utc"),
        (datetime(2024, 12, 31, 23, 59, 59, tzinfo=timezone.utc), "2024_12Dec_31_utc"),
        (datetime(2025, 2, 28, 12, 0, 0, tzinfo=timezone.utc), "2025_02Feb_28_utc"),
        (datetime(2024, 2, 29, 12, 0, 0, tzinfo=timezone.utc), "2024_02Feb_29_utc"),  # Leap year
        (datetime(2023, 6, 5, 8, 15, 30, tzinfo=timezone.utc), "2023_06Jun_05_utc"),
    ]
    
    for mock_date, expected in test_cases:
        with patch('pythagoras._110_supporting_utilities.current_date_gmt_str.datetime') as mock_datetime:
            mock_datetime.now.return_value = mock_date
            result = current_date_gmt_string()
            assert result == expected, f"For {mock_date}: expected {expected}, got {result}"


def test_current_date_gmt_string_consistency():
    """Test that multiple calls within a short time produce consistent results."""
    result_1 = current_date_gmt_string()
    result_2 = current_date_gmt_string()
    
    # Both should be valid format
    pattern = r'^\d{4}_\d{2}[A-Z][a-z]{2}_\d{2}_utc$'
    assert re.match(pattern, result_1), f"First call format mismatch: {result_1}"
    assert re.match(pattern, result_2), f"Second call format mismatch: {result_2}"
    
    # They should be the same or differ only if day changed (very unlikely in quick succession)
    # At minimum, they should both be valid strings
    assert isinstance(result_1, str) and len(result_1) > 0
    assert isinstance(result_2, str) and len(result_2) > 0


def test_month_abbreviations_constant():
    """Test that the month abbreviations constant is properly defined."""
    assert len(_MONTH_ABBREVIATIONS) == 12, "Should have exactly 12 month abbreviations"
    
    expected = ("Jan", "Feb", "Mar", "Apr", "May", "Jun",
                "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")
    assert _MONTH_ABBREVIATIONS == expected, "Month abbreviations mismatch"
    
    # Verify all are 3-letter strings with proper capitalization
    for abbrev in _MONTH_ABBREVIATIONS:
        assert len(abbrev) == 3, f"Abbreviation should be 3 letters: {abbrev}"
        assert abbrev[0].isupper(), f"First letter should be uppercase: {abbrev}"
        assert abbrev[1:].islower(), f"Remaining letters should be lowercase: {abbrev}"

