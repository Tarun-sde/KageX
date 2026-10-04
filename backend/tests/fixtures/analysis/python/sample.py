"""Inert analyzer fixture: importing this file must fail."""

raise RuntimeError("Submitted Python was executed")


def choose(value, fallback=0):
    if value > 0:
        return value
    return fallback


class Worker:
    async def choose(self, value):
        def nested(item):
            return item + 1

        return nested(value)
