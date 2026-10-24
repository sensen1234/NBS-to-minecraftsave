"""Coordinate-only layout operations and history, independent of Qt."""

from collections.abc import Mapping
from numbers import Integral


WORLD_LIMIT = 30_000_000
AXIS_LIMITS = ((-WORLD_LIMIT, WORLD_LIMIT), (-64, 320), (-WORLD_LIMIT, WORLD_LIMIT))


def _integer_triplet(values):
    values = tuple(values)
    if len(values) != 3 or any(isinstance(value, bool) or not isinstance(value, Integral) for value in values):
        raise ValueError("坐标必须包含三个整数")
    return tuple(int(value) for value in values)


def copy_layout(coords: Mapping):
    return {gid: _integer_triplet(xyz) for gid, xyz in coords.items()}


def validate_layout(coords: Mapping):
    result = copy_layout(coords)
    for gid, xyz in result.items():
        for axis, value, (low, high) in zip("XYZ", xyz, AXIS_LIMITS):
            if not low <= value <= high:
                raise ValueError(f"组 {gid} 的 {axis}={value:,} 超出范围 {low:,}～{high:,}")
    return result


def translate_all(coords: Mapping, delta):
    """Translate every origin by the same vector, rejecting the entire overflow."""
    delta = _integer_triplet(delta)
    source = copy_layout(coords)
    return validate_layout({gid: tuple(xyz[i] + delta[i] for i in range(3))
                            for gid, xyz in source.items()})


def arrange_along_z(coords: Mapping, start_z: int, spacing: int):
    """Keep X/Y and place group origins in the mapping's existing list order."""
    start_z, _, spacing = _integer_triplet((start_z, 0, spacing))
    if spacing < 1:
        raise ValueError("起点间隔至少为 1 格")
    return validate_layout({gid: (xyz[0], xyz[1], start_z + index * spacing)
                            for index, (gid, xyz) in enumerate(copy_layout(coords).items())})


class LayoutHistory:
    """Whole-layout history with explicit edit merging and branching."""

    def __init__(self, initial: Mapping, limit=100):
        self._initial = copy_layout(initial)
        self._states = [copy_layout(initial)]
        self._labels = ["最初布局"]
        self._index = 0
        self._merge_key = None
        self._limit = max(1, int(limit))

    @property
    def initial(self):
        return copy_layout(self._initial)

    @property
    def current(self):
        return copy_layout(self._states[self._index])

    @property
    def undo_count(self):
        return self._index

    @property
    def redo_count(self):
        return len(self._states) - self._index - 1

    @property
    def undo_label(self):
        return self._labels[self._index] if self.undo_count else ""

    @property
    def redo_label(self):
        return self._labels[self._index + 1] if self.redo_count else ""

    def break_merge(self):
        self._merge_key = None

    def record(self, coords: Mapping, description: str, merge_key=None):
        state = copy_layout(coords)
        if state.keys() != self._initial.keys():
            raise ValueError("布局必须包含全部轨道组")
        if state == self._states[self._index]:
            return False
        merge = (merge_key is not None and merge_key == self._merge_key
                 and self._index > 0 and not self.redo_count)
        if merge:
            if state == self._states[self._index - 1]:
                self._states.pop()
                self._labels.pop()
                self._index -= 1
                self._merge_key = None
                return True
            self._states[self._index] = state
            self._labels[self._index] = description
        else:
            del self._states[self._index + 1:]
            del self._labels[self._index + 1:]
            self._states.append(state)
            self._labels.append(description)
            self._index += 1
            if self._index > self._limit:
                self._states.pop(0)
                self._labels.pop(0)
                self._index -= 1
        self._merge_key = merge_key
        return True

    def undo(self):
        self.break_merge()
        if self.undo_count:
            self._index -= 1
        return self.current

    def redo(self):
        self.break_merge()
        if self.redo_count:
            self._index += 1
        return self.current
