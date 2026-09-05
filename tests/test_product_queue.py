import pytest
from openfactory.product.queue import Proposed, whole_batches

def test_fifo_lifo_ordering_preserved():
    """Test that `whole_batches` processes items sequentially and retains their exact order."""
    items = [
        Proposed(ticket="1"),
        Proposed(ticket="2", batch="A"),
        Proposed(ticket="3", batch="A"),
        Proposed(ticket="4")
    ]
    kept, cut = whole_batches(items, limit=10)

    assert len(kept) == 4
    assert [p.ticket for p in kept] == ["1", "2", "3", "4"]
    assert len(cut) == 0

def test_priority_preemption_exceeds_limit():
    """Test that a large batch at the front bypasses the limit if it exceeds it immediately."""
    items = [
        Proposed(ticket="1", batch="Group1"),
        Proposed(ticket="2", batch="Group1"),
        Proposed(ticket="3", batch="Group1"),
        Proposed(ticket="4"),
        Proposed(ticket="5")
    ]
    # Limit is 2, but the first batch is length 3. It should be admitted fully.
    kept, cut = whole_batches(items, limit=2)

    assert len(kept) == 3
    assert [p.ticket for p in kept] == ["1", "2", "3"]

    assert len(cut) == 2
    assert [p.ticket for p in cut] == ["4", "5"]

def test_queue_capacity_bounds():
    """Test that after limit is reached, items are correctly moved to the cut list."""
    items = [
        Proposed(ticket="1"),
        Proposed(ticket="2"),
        Proposed(ticket="3"),
        Proposed(ticket="4")
    ]
    kept, cut = whole_batches(items, limit=2)

    assert len(kept) == 2
    assert [p.ticket for p in kept] == ["1", "2"]

    assert len(cut) == 2
    assert [p.ticket for p in cut] == ["3", "4"]

def test_queue_capacity_bounds_batch_cut():
    """Test that a batch straddling the limit is entirely cut."""
    items = [
        Proposed(ticket="1"),
        Proposed(ticket="2", batch="Batch A"),
        Proposed(ticket="3", batch="Batch A"),
        Proposed(ticket="4")
    ]
    # Limit is 2.
    # Item 1 is kept (size 1).
    # Batch A has size 2. Current kept size is 1. 1 + 2 > 2. Batch A is cut.
    # Item 4 has size 1. Current kept size is 1. 1 + 1 <= 2. Item 4 is kept!
    kept, cut = whole_batches(items, limit=2)

    assert len(kept) == 2
    assert [p.ticket for p in kept] == ["1", "4"]

    assert len(cut) == 2
    assert [p.ticket for p in cut] == ["2", "3"]

def test_ungrouped_items_are_separate():
    """Test that ungrouped items (empty batch string) are their own unit."""
    items = [
        Proposed(ticket="1", batch=""),
        Proposed(ticket="2", batch=""),
    ]
    kept, cut = whole_batches(items, limit=1)

    assert len(kept) == 1
    assert kept[0].ticket == "1"

    assert len(cut) == 1
    assert cut[0].ticket == "2"
