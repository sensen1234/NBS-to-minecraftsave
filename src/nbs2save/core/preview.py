"""Build a bounded, final block scene using the actual export strategies.

The inclusive tick range selects a world X interval for every group. Their
union is rendered as it appears after the complete export, including writes
from other ticks that overlap these regions. Coordinates stay in world space.
No schematic or command file is created.
"""

from __future__ import annotations

from bisect import bisect_right
from dataclasses import dataclass
from typing import Any, Iterable, Mapping, NamedTuple

from pynbs import Note

from .core import GroupProcessor, OutputFormatStrategy
from .mcfunction import McFunctionOutputStrategy


class PreviewBlock(NamedTuple):
    position: tuple[int, int, int]
    blockstate: str
    group_id: Any

    @property
    def state(self) -> str:
        """Convenient alias for renderers."""
        return self.blockstate


@dataclass(frozen=True)
class PreviewData:
    blocks: tuple[PreviewBlock, ...]
    bounds: tuple[tuple[int, int, int], tuple[int, int, int]] | None
    start_tick: int
    end_tick: int
    global_max_tick: int
    total_notes: int
    visible_notes: int
    group_count: int
    written_blocks: int
    overwritten_blocks: int
    has_song: bool


def _normalize_blockstate(blockstate: str) -> str:
    return blockstate if ":" in blockstate.split("[", 1)[0] else "minecraft:" + blockstate


def _merge_intervals(intervals):
    merged = []
    for first, last in sorted(intervals):
        if first > last:
            continue
        if merged and first <= merged[-1][1] + 1:
            merged[-1] = (merged[-1][0], max(last, merged[-1][1]))
        else:
            merged.append((first, last))
    return tuple(merged)


def _contains(intervals, starts, value):
    index = bisect_right(starts, value) - 1
    return index >= 0 and value <= intervals[index][1]


class _BlockSink:
    """Minimal MCSchematic-compatible sink; last write wins at each position."""

    def __init__(self, x_ranges=()):
        self.blocks: dict[tuple[int, int, int], PreviewBlock] = {}
        self.group_id = None
        self.written_blocks = 0
        self.overwritten_blocks = 0
        self.x_ranges = x_ranges
        self._x_starts = tuple(first for first, _ in x_ranges)

    def setBlock(self, position, blockstate):
        position = tuple(map(int, position))
        if not _contains(self.x_ranges, self._x_starts, position[0]):
            return
        blockstate = _normalize_blockstate(blockstate)
        self.written_blocks += 1
        if position in self.blocks:
            self.overwritten_blocks += 1
        if blockstate.split("[", 1)[0] in {
            "minecraft:air", "minecraft:cave_air", "minecraft:void_air"
        }:
            self.blocks.pop(position, None)
        else:
            self.blocks[position] = PreviewBlock(position, blockstate, self.group_id)

    def write_commands(self, processor, commands):
        """Interpret only the setblock/fill emitted by the real command strategy."""
        for command in commands:
            parts = command.split()
            if parts[0] == "setblock":
                self.setBlock(tuple(map(int, parts[1:4])), parts[4])
            elif parts[0] == "fill":
                first = tuple(map(int, parts[1:4]))
                last = tuple(map(int, parts[4:7]))
                for x in range(min(first[0], last[0]), max(first[0], last[0]) + 1):
                    for y in range(min(first[1], last[1]), max(first[1], last[1]) + 1):
                        for z in range(min(first[2], last[2]), max(first[2], last[2]) + 1):
                            self.setBlock((x, y, z), parts[7])
            else:
                raise ValueError(f"预览不支持此生成命令: {parts[0]}")


class _PreviewStrategy(OutputFormatStrategy):
    """Keep geometry methods intact while replacing all output side effects."""

    def __init__(self, delegate: OutputFormatStrategy, sink: _BlockSink):
        self.delegate = delegate
        if isinstance(delegate, McFunctionOutputStrategy):
            delegate._write_commands = sink.write_commands
        else:
            delegate.schem = sink

    def initialize(self, processor):
        pass

    def finalize(self, processor):
        pass

    def write_base_structures(self, processor, tick):
        self.delegate.write_base_structures(processor, tick)

    def write_pan_platform(self, processor, tick, direction):
        self.delegate.write_pan_platform(processor, tick, direction)

    def write_note(self, processor, note):
        self.delegate.write_note(processor, note)


class _PreviewProcessor(GroupProcessor):
    def __init__(self, notes, max_tick, config, groups, sink):
        super().__init__(notes, max_tick, config, groups)
        self._sink = sink
        self._group_ids = iter(groups)
        self._tick_ranges = ()
        self._tick_starts = ()
        self.set_output_strategy(_PreviewStrategy(super()._pick_strategy_for_group("default"), sink))

    def _pick_strategy_for_group(self, generation_mode):
        self._sink.group_id = next(self._group_ids)
        # Every strategy writes only at tick_x or tick_x - 1. Invert those
        # positions to find every tick that could affect any selected region.
        # Disjoint windows stay disjoint, so distant group origins never cause
        # traversal of the potentially enormous gap between them.
        self._tick_ranges = _merge_intervals(
            (
                max(0, (first - self.base_x + 1) // 2),
                min(self.global_max_tick, (last + 1 - self.base_x) // 2),
            )
            for first, last in self._sink.x_ranges
        )
        self._tick_starts = tuple(first for first, _ in self._tick_ranges)
        return _PreviewStrategy(super()._pick_strategy_for_group(generation_mode), self._sink)

    def _switch_strategy(self, new_strategy):
        # Wrappers share a class, but their underlying generation modes differ.
        self.output_strategy = new_strategy

    def load_notes(self, all_notes):
        # Platform lookups scan self.notes; retaining only this tick window also
        # bounds that work for songs with hundreds of thousands of notes.
        super().load_notes(
            [note for note in all_notes if _contains(self._tick_ranges, self._tick_starts, note.tick)]
        )

    def process_group(self):
        for first, last in self._tick_ranges:
            super().process_group(first, last)


def build_preview(
    notes: Iterable[Note] | None,
    group_config: Mapping,
    config: Mapping | None = None,
    *,
    start_tick: int = 0,
    end_tick: int | None = None,
    global_max_tick: int | None = None,
) -> PreviewData:
    """Return the generated block scene without reading or writing any files.

    ``end_tick`` and ``global_max_tick`` are inclusive, matching export. Supply
    ``header.song_length`` as ``global_max_tick`` to include its trailing clock.
    The selected tick range determines each group's world X window; the scene
    is the complete export cropped to the union of those windows. Other ticks
    are included when their writes overlap a selected window. ``visible_notes``
    counts input notes in the selected time range, rather than surviving boxes.
    ``notes=None`` means no song is loaded and returns an empty scene; an empty
    iterable represents a loaded, empty song. Input notes/config are unmodified.
    Generation errors, including conflicting notes, propagate to the caller.
    Staircase layouts require schematic output; the existing mcfunction export
    lifecycle cannot produce their combined final scene in a single file.
    """
    start_tick = int(start_tick)
    if start_tick < 0:
        raise ValueError("预览起始 tick 不能小于 0")
    has_song = notes is not None
    all_notes = list(notes) if has_song else []
    maximum = max((note.tick for note in all_notes), default=0)
    if global_max_tick is not None:
        maximum = int(global_max_tick)
    if maximum < 0:
        raise ValueError("歌曲长度不能小于 0")
    last_tick = maximum if end_tick is None else min(int(end_tick), maximum)
    if end_tick is not None and int(end_tick) < start_tick:
        raise ValueError("预览结束 tick 不能早于起始 tick")

    groups = dict(group_config)
    preview_config = dict(config or {})
    if has_song and preview_config.get("type") == "mcfunction" and any(
        group.get("generation_mode", "default") in {"staircase", "staircase_up"}
        for group in groups.values()
    ):
        raise ValueError("阶梯模式暂仅支持 schematic 结构预览，请在基础设置中切换输出类型。")
    x_ranges = ()
    if has_song and start_tick <= last_tick:
        x_ranges = _merge_intervals(
            (int(group["base_coords"][0]) + 2 * start_tick - 1,
             int(group["base_coords"][0]) + 2 * last_tick)
            for group in groups.values()
        )
    sink = _BlockSink(x_ranges)
    layers = {layer for group in groups.values() for layer in group["layers"]}
    visible_notes = sum(
        start_tick <= note.tick <= last_tick and note.layer in layers
        for note in all_notes
    )
    if has_song and start_tick <= last_tick and groups:
        processor = _PreviewProcessor(
            all_notes, maximum, preview_config, groups, sink
        )
        processor.process()

    blocks = tuple(sink.blocks.values())
    bounds = None
    if blocks:
        positions = tuple(block.position for block in blocks)
        bounds = (
            tuple(min(position[axis] for position in positions) for axis in range(3)),
            tuple(max(position[axis] for position in positions) for axis in range(3)),
        )
    return PreviewData(
        blocks=blocks,
        bounds=bounds,
        start_tick=start_tick,
        end_tick=last_tick,
        global_max_tick=maximum,
        total_notes=len(all_notes),
        visible_notes=visible_notes,
        group_count=len(groups),
        written_blocks=sink.written_blocks,
        overwritten_blocks=sink.overwritten_blocks,
        has_song=has_song,
    )
