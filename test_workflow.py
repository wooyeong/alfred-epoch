#!/usr/bin/env python3
import sys
import json
from datetime import datetime, timezone
from workflow import process_query, parse_datetime_string, parse_epoch_value

test_stats = {'passed': 0, 'failed': 0}

def test_case(description, query, should_succeed=True, expected_date=None,
              expected_type=None, approx_seconds=None):
    global test_stats

    print(f"\n{'='*60}")
    print(f"Test: {description}")
    print(f"Input: '{query}'")

    timestamp, is_epoch_input, show_now = process_query(query)

    if not should_succeed:
        if timestamp is None:
            print("✅ PASS: Correctly failed to parse")
            test_stats['passed'] += 1
            return
        else:
            print("❌ FAIL: Expected to fail but got result")
            test_stats['failed'] += 1
            return

    if timestamp is None:
        print("❌ FAIL: Expected success but got None")
        test_stats['failed'] += 1
        return

    dt_local = datetime.fromtimestamp(timestamp).astimezone()
    dt_utc = datetime.fromtimestamp(timestamp, tz=timezone.utc)

    failures = []

    if expected_date:
        actual_date = dt_local.strftime('%Y-%m-%d')
        if actual_date != expected_date:
            failures.append(f"Date mismatch: expected {expected_date}, got {actual_date}")

    if expected_type:
        actual_type = 'epoch' if is_epoch_input else 'date'
        if actual_type != expected_type:
            failures.append(f"Type mismatch: expected {expected_type}, got {actual_type}")

    if approx_seconds is not None:
        diff = abs(timestamp - approx_seconds)
        if diff > 1:
            failures.append(f"Timestamp mismatch: expected ~{approx_seconds}, got {int(timestamp)} (diff: {int(diff)}s)")

    if failures:
        print("❌ FAIL:")
        for failure in failures:
            print(f"   - {failure}")
        test_stats['failed'] += 1
    else:
        print("✅ PASS")
        test_stats['passed'] += 1

    print(f"   Local: {dt_local.strftime('%Y-%m-%d %H:%M:%S %Z')} ({dt_local.strftime('%a')})")
    print(f"   UTC:   {dt_utc.strftime('%Y-%m-%d %H:%M:%S UTC')} ({dt_utc.strftime('%a')})")
    print(f"   Epoch: {int(timestamp)} seconds")
    print(f"   Type:  {'Epoch input' if is_epoch_input else 'Date input'}")

if __name__ == "__main__":
    print("Workflow Test Cases")
    print("="*60)

    test_case(
        "Date with dashes",
        "2025-12-01",
        expected_date="2025-12-01",
        expected_type="date"
    )

    test_case(
        "Date with slashes",
        "2025/12/01",
        expected_date="2025-12-01",
        expected_type="date"
    )

    test_case(
        "Month/Day only",
        "12/25",
        expected_date="2025-12-25",
        expected_type="date"
    )

    test_case(
        "Epoch seconds",
        "1733900000",
        approx_seconds=1733900000,
        expected_type="epoch"
    )

    test_case(
        "Epoch milliseconds",
        "1733900000000",
        approx_seconds=1733900000,
        expected_type="epoch"
    )
    
    test_case(
        "Epoch microseconds",
        "1765760400822456",
        approx_seconds=1765760400.822456,
        expected_type="epoch"
    )
    
    test_case(
        "Epoch nanoseconds",
        "1765760400822456789",
        approx_seconds=1765760400.822456789,
        expected_type="epoch"
    )

    import time
    now = time.time()
    test_case(
        "Current time + 2 hours",
        "+ 2 hours",
        approx_seconds=now + 7200,
        expected_type="epoch"
    )

    test_case(
        "Date + 1 day",
        "2025-12-01 + 1 day",
        expected_date="2025-12-02",
        expected_type="date"
    )

    test_case(
        "Epoch - 3 days",
        "1733900000 - 3 days",
        approx_seconds=1733900000 - (3 * 86400),
        expected_type="epoch"
    )

    test_case(
        "Date - 2 weeks",
        "2025-12-01 - 2 weeks",
        expected_date="2025-11-17",
        expected_type="date"
    )

    test_case(
        "Complex operations: date with multiple ops",
        "2025-12-01 -1d +4d - 1y + 20w",
        expected_date="2025-04-23",
        expected_type="date"
    )

    test_case(
        "Complex operations: current time with multiple ops",
        "-1d -13min +40 seconds",
        approx_seconds=now - 86400 - 780 + 40,
        expected_type="epoch"
    )

    print(f"\n{'='*60}")
    print(f"Test Summary:")
    print(f"  ✅ Passed: {test_stats['passed']}")
    print(f"  ❌ Failed: {test_stats['failed']}")
    total = test_stats['passed'] + test_stats['failed']
    print(f"  Total:  {total}")

    if test_stats['failed'] == 0:
        print(f"\n🎉 All tests passed!")
        sys.exit(0)
    else:
        print(f"\n⚠️  Some tests failed")
        sys.exit(1)
