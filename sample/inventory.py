"""A tiny warehouse inventory — scan this folder to see codeatlas work."""

import csv

from models import Item


def restock_report(items: list[Item], low_first: bool = True) -> list[str]:
    """One line per item, lowest stock first."""
    lines = []
    for item in items:  # +1
        if item.needs_restock():  # +1
            lines.append(f"{item.sku}: LOW")
        elif item.qty == 0:  # +1
            lines.append(f"{item.sku}: OUT")
    lines.sort(reverse=low_first)
    return lines


def load_inventory(csv_path: str) -> list[Item]:
    """Load items from a sku,qty CSV file."""
    with open(csv_path, newline="") as fh:
        return [Item(row["sku"], int(row["qty"])) for row in csv.DictReader(fh)]
