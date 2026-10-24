"""Read-only NBS project statistics for the home page and creative tools."""

from dataclasses import dataclass
import math
from pathlib import Path

import pynbs


@dataclass(frozen=True)
class CustomInstrumentUsage:
    instrument_id: int
    name: str
    note_count: int


@dataclass(frozen=True)
class SongInsights:
    title: str
    author: str
    tempo: float
    duration_seconds: float
    length_ticks: int
    note_count: int
    used_layer_count: int
    out_of_range_count: int
    custom_note_count: int
    custom_instruments: tuple[CustomInstrumentUsage, ...]

    @property
    def duration_text(self):
        minutes, seconds = divmod(round(self.duration_seconds), 60)
        return f"{minutes}:{seconds:02d}"


def analyze_song(song, filename="") -> SongInsights:
    """Include the final occupied tick and header silence, excluding sound tails.

    Custom IDs start at NBS default_instruments. The exporter currently maps
    only keys 33–57 to its 25 pitches. Input notes and settings are unmodified.
    """
    tempo = float(song.header.tempo)
    if not math.isfinite(tempo) or tempo <= 0:
        raise ValueError("歌曲速度必须大于 0")
    notes = song.notes
    length_ticks = max(int(song.header.song_length), max((note.tick + 1 for note in notes), default=0), 0)
    first_custom = int(getattr(song.header, "default_instruments", 16))
    names = {first_custom + instrument.id: instrument.name for instrument in song.instruments}
    custom_counts = {}
    for note in notes:
        if note.instrument >= first_custom:
            custom_counts[note.instrument] = custom_counts.get(note.instrument, 0) + 1
    custom_usage = tuple(CustomInstrumentUsage(
        instrument_id, names.get(instrument_id) or f"自定义乐器 #{instrument_id}", count,
    ) for instrument_id, count in sorted(custom_counts.items()))
    return SongInsights(
        title=song.header.song_name.strip() or Path(filename).stem or "未命名歌曲",
        author=song.header.song_author.strip() or song.header.original_author.strip() or "未署名",
        tempo=tempo, duration_seconds=length_ticks / tempo, length_ticks=length_ticks,
        note_count=len(notes), used_layer_count=len({note.layer for note in notes}),
        out_of_range_count=sum(not 33 <= note.key <= 57 for note in notes),
        custom_note_count=sum(custom_counts.values()), custom_instruments=custom_usage,
    )


def read_song_insights(path) -> SongInsights:
    return analyze_song(pynbs.read(str(path)), str(path))
