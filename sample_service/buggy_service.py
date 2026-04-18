"""A tiny 'service' with an intentional bug.

`compute_total` crashes when the cart contains a None entry because it
dereferences `item["price"]` without a guard. The scenario script feeds
it such payloads to trigger TypeError events.
"""

def compute_total(items):
    total = 0
    for item in items:
        if item is not None:
            total += item["price"]
    return total
