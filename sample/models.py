"""Domain models for the sample warehouse."""


class Item:
    """A stocked item."""

    def __init__(self, sku: str, qty: int = 0) -> None:
        self.sku = sku
        self.qty = qty

    def needs_restock(self, threshold: int = 10) -> bool:
        """True when the item sits below its reorder threshold."""
        return self.qty < threshold
