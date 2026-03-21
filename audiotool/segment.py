from dataclasses import dataclass


@dataclass
class Segment:
    start: float
    end: float
    text: str | None = None
    speaker: str | None = None
