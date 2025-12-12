#!/usr/bin/env python3
"""
Alfred Workflow: Epoch timestamp generator
"""
import json
import re
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from decimal import Decimal


@dataclass
class DisplayItem:
    title: str
    subtitle: str
    arg: str = None

    def __post_init__(self):
        if self.arg is None:
            self.arg = self.title


@dataclass
class EpochData:
    timestamp: float

    def __post_init__(self):
        self.epoch_s = int(self.timestamp)

        d = Decimal(str(self.timestamp))
        self.epoch_ms = int(d * 1000)
        self.epoch_us = int(d * 1_000_000)
        self.epoch_ns = int(d * 1_000_000_000)

        self.dt_local = datetime.fromtimestamp(self.timestamp).astimezone()
        self.dt_utc = datetime.fromtimestamp(self.timestamp, tz=timezone.utc)

    def to_display_items_from_epoch(self, show_now=False):
        now_label = " (Now)" if show_now else ""

        return [
            DisplayItem(self.dt_local.strftime("%Y-%m-%d %H:%M:%S %Z"), f"Local time ({self.dt_local.strftime('%a')})"),
            DisplayItem(self.dt_utc.strftime("%Y-%m-%d %H:%M:%S UTC"), f"UTC time ({self.dt_utc.strftime('%a')})"),
            DisplayItem(self.dt_local.isoformat(), "ISO 8601 format"),
            DisplayItem(str(self.epoch_ms), f"Milliseconds{now_label}"),
            DisplayItem(str(self.epoch_s), f"Seconds{now_label}"),
            DisplayItem(str(self.epoch_us), f"Microseconds{now_label}"),
            DisplayItem(str(self.epoch_ns), f"Nanoseconds{now_label}"),
        ]

    def to_display_items_from_date(self):
        return [
            DisplayItem(str(self.epoch_ms), "Milliseconds"),
            DisplayItem(str(self.epoch_s), "Seconds"),
            DisplayItem(str(self.epoch_us), "Microseconds"),
            DisplayItem(str(self.epoch_ns), "Nanoseconds"),
            DisplayItem(self.dt_local.strftime("%Y-%m-%d %H:%M:%S %Z"), f"Local time ({self.dt_local.strftime('%a')})"),
            DisplayItem(self.dt_utc.strftime("%Y-%m-%d %H:%M:%S UTC"), f"UTC time ({self.dt_utc.strftime('%a')})"),
            DisplayItem(self.dt_local.isoformat(), "ISO 8601 format"),
        ]


def create_alfred_item(title, subtitle="", arg=""):
    """Create an Alfred result item"""
    return {
        "title": title,
        "subtitle": subtitle,
        "arg": arg,
        "valid": True
    }


def parse_datetime_string(date_str):
    """Try to parse various datetime formats"""
    formats_with_year = [
        "%Y-%m-%d %H:%M:%S.%f",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%Y-%m-%d",
        "%Y/%m/%d %H:%M:%S.%f",
        "%Y/%m/%d %H:%M:%S",
        "%Y/%m/%d %H:%M",
        "%Y/%m/%d",
        "%Y %m %d %H:%M:%S",
        "%Y %m %d",
    ]

    formats_without_year = [
        "%m/%d",
        "%m %d",
    ]

    for fmt in formats_with_year:
        try:
            dt = datetime.strptime(date_str, fmt)
            return dt.replace(tzinfo=None).astimezone()
        except ValueError:
            continue

    for fmt in formats_without_year:
        try:
            dt = datetime.strptime(date_str, fmt)
            dt = dt.replace(year=datetime.now().year)
            return dt.replace(tzinfo=None).astimezone()
        except ValueError:
            continue

    return None


def parse_time_operations(query):
    """Parse time operations like '+ 2 min - 1 hour' and return timedelta"""
    unit_map = {
        's': 'seconds', 'sec': 'seconds', 'second': 'seconds', 'seconds': 'seconds',
        'm': 'minutes', 'min': 'minutes', 'minute': 'minutes', 'minutes': 'minutes',
        'h': 'hours', 'hour': 'hours', 'hours': 'hours',
        'd': 'days', 'day': 'days', 'days': 'days',
        'w': 'weeks', 'week': 'weeks', 'weeks': 'weeks',
        'M': 'months', 'month': 'months', 'months': 'months',
        'y': 'years', 'year': 'years', 'years': 'years',
    }

    pattern = r'([+\-])\s*(\d+)\s*(\w+)'
    matches = re.findall(pattern, query, re.IGNORECASE)

    total_delta = timedelta()
    for sign, value, unit in matches:
        unit_lower = unit.lower()
        normalized_unit = unit_map.get(unit_lower)

        if not normalized_unit:
            continue

        amount = int(value) if sign == '+' else -int(value)

        if normalized_unit == 'seconds':
            total_delta += timedelta(seconds=amount)
        elif normalized_unit == 'minutes':
            total_delta += timedelta(minutes=amount)
        elif normalized_unit == 'hours':
            total_delta += timedelta(hours=amount)
        elif normalized_unit == 'days':
            total_delta += timedelta(days=amount)
        elif normalized_unit == 'weeks':
            total_delta += timedelta(weeks=amount)
        elif normalized_unit == 'months':
            total_delta += timedelta(days=amount * 30)
        elif normalized_unit == 'years':
            total_delta += timedelta(days=amount * 365)

    return total_delta


def parse_epoch_value(epoch_str):
    epoch_value = Decimal(epoch_str)
    digit_count = len(epoch_str)

    if digit_count <= 11:
        return float(epoch_value)
    elif digit_count <= 14:
        return float(epoch_value / 1000)
    elif digit_count <= 17:
        return float(epoch_value / 1_000_000)
    else:
        return float(epoch_value / 1_000_000_000)


def process_query(query):
    if not query:
        return time.time(), True, True

    operation_match = re.search(r'(^|[\s])[+\-]\s*\d+\s*\w+', query)

    if operation_match:
        operation_start = operation_match.start()
        base_part = query[:operation_start].strip()
        time_delta = parse_time_operations(query)
    else:
        base_part = query.strip()
        time_delta = timedelta()

    if not base_part:
        base_timestamp = time.time()
        is_epoch_input = True
        show_now = True
    elif base_part.isdigit():
        base_timestamp = parse_epoch_value(base_part)
        is_epoch_input = True
        show_now = False
    else:
        dt = parse_datetime_string(base_part)
        if not dt:
            return None, None, None
        base_timestamp = dt.timestamp()
        is_epoch_input = False
        show_now = False

    final_timestamp = base_timestamp + time_delta.total_seconds()

    return final_timestamp, is_epoch_input, show_now


def main():
    query = sys.argv[1] if len(sys.argv) > 1 else ""

    timestamp, is_epoch_input, show_now = process_query(query)

    if timestamp is None:
        items = []
    else:
        epoch_data = EpochData(timestamp)

        if is_epoch_input:
            display_items = epoch_data.to_display_items_from_epoch(show_now=show_now)
        else:
            display_items = epoch_data.to_display_items_from_date()

        items = [create_alfred_item(item.title, item.subtitle, item.arg) for item in display_items]

    result = {"items": items}
    print(json.dumps(result))


if __name__ == "__main__":
    main()
