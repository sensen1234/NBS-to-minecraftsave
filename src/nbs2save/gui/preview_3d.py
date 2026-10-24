"""Dependency-free, orthographic preview of the generated Minecraft block layout.

The renderer consumes the same block placements as export. Textures are small,
procedural material illustrations, not Minecraft resource-pack assets. The camera
uses one scale for all three axes; changing the view never changes world positions.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from functools import lru_cache

from PyQt6.QtCore import QPointF, QRectF, Qt, pyqtSignal
from PyQt6.QtGui import (
    QColor,
    QFont,
    QImage,
    QPainter,
    QPen,
    QPixmap,
    QPolygonF,
    QTransform,
)
from PyQt6.QtWidgets import QWidget
from qfluentwidgets import isDarkTheme


_Vec = tuple[float, float, float]
_MIN_SCALE = 1e-9
_NORMALS = ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1))
_AIR = {"air", "cave_air", "void_air", "structure_void"}
_TRANSPARENT = {"glass", "barrier", "ice", "frosted_ice", "slime_block", "honey_block"}
_NAMES = {
    "note_block": "音符盒", "repeater": "红石中继器", "redstone_wire": "红石粉",
    "iron_block": "铁块", "gold_block": "金块", "dirt": "泥土", "grass_block": "草方块",
    "stone": "石头", "sand": "沙子", "glass": "玻璃", "white_wool": "白色羊毛",
    "clay": "黏土", "packed_ice": "浮冰", "bone_block": "骨块", "soul_sand": "灵魂沙",
    "pumpkin": "南瓜", "emerald_block": "绿宝石块", "hay_block": "干草块",
    "glowstone": "荧石", "oak_planks": "橡木木板", "barrier": "屏障",
    "redstone_lamp": "红石灯", "redstone_torch": "红石火把",
}
_INSTRUMENTS = {
    "harp": "竖琴", "bass": "贝斯", "basedrum": "底鼓", "snare": "小军鼓",
    "hat": "踩镲", "guitar": "吉他", "flute": "长笛", "bell": "钟琴",
    "chime": "风铃", "xylophone": "木琴", "iron_xylophone": "铁木琴",
    "cow_bell": "牛铃", "didgeridoo": "迪吉里杜管", "bit": "比特",
    "banjo": "班卓琴", "pling": "电钢琴",
}
_COLORS = {
    "iron_block": "#c5c9ca", "gold_block": "#ecd346", "emerald_block": "#3dce80",
    "diamond_block": "#53cfd1", "copper_block": "#bb7353", "dirt": "#906347",
    "grass_block": "#8b6646", "stone": "#929494", "cobblestone": "#878b88",
    "sand": "#dfd29b", "red_sand": "#bf713d", "glass": "#a4d9e4",
    "white_wool": "#e7e5df", "clay": "#9fa9bc", "packed_ice": "#87b3e2",
    "blue_ice": "#668ed1", "ice": "#9ac7ec", "bone_block": "#d4d0b6",
    "soul_sand": "#635044", "pumpkin": "#c47c2c", "hay_block": "#baa241",
    "glowstone": "#c6a55f", "oak_planks": "#b8915d", "note_block": "#835b3d",
    "redstone_lamp": "#6e4b30", "barrier": "#ec5663", "obsidian": "#3d344a",
    "quartz_block": "#e2ddd1", "redstone_block": "#b42c25", "bedrock": "#505254",
    "repeater": "#aaa6a0", "redstone_wire": "#981e1b", "_torch_stem": "#9d7346",
    "_torch_head": "#b52a20", "_torch_lit": "#fb5b35",
}


@dataclass(slots=True)
class _Block:
    position: _Vec
    state: str
    name: str
    properties: dict[str, str]
    group_id: object
    full: bool
    opaque: bool


@dataclass(slots=True)
class _Face:
    vertices: tuple[_Vec, _Vec, _Vec, _Vec]
    normal: tuple[int, int, int]
    center: _Vec
    block: int
    material: str
    area: float


def _parse_state(state: str) -> tuple[str, dict[str, str]]:
    name, _, suffix = state.partition("[")
    return name.removeprefix("minecraft:"), dict(
        part.split("=", 1) for part in suffix.rstrip("]").split(",") if "=" in part
    )


def _is_full(name: str, props: dict[str, str]) -> bool:
    if name in {"redstone_wire", "repeater", "comparator", "redstone_torch", "torch"}:
        return False
    if name.endswith("_slab"):
        return props.get("type") == "double"
    return not name.endswith(("_stairs", "_carpet", "_pressure_plate", "_pane", "_fence"))


def _base_color(material: str, top: bool = False) -> QColor:
    if material == "grass_block" and top:
        return QColor("#6e9b3f")
    if material == "redstone_lamp_lit":
        return QColor("#e9b568")
    if material == "redstone_wire_powered":
        return QColor("#ee3e29")
    if material.endswith("_stained_glass"):
        prefix = material.removesuffix("_stained_glass")
        return QColor({"red": "#d85b69", "blue": "#668edb", "green": "#7bb24d",
                       "yellow": "#e6d15b", "black": "#596168", "white": "#dae4e6"}.get(prefix, "#b398ce"))
    if material.endswith("_planks"):
        return QColor(_COLORS.get(material, "#ac8455"))
    if material.endswith("_wool"):
        return QColor(_COLORS.get(material, "#b7aabb"))
    return QColor(_COLORS.get(material, "#a3a5a2"))


@lru_cache(maxsize=256)
def _texture(material: str, normal: tuple[int, int, int]) -> QImage:
    """A cached 16px illustration, with fixed world-space lighting."""
    shade = (0.82, 0.67, 1.0, 0.52, 0.75, 0.89)[_NORMALS.index(normal)]
    color = _base_color(material, normal[1] == 1)
    transparent = material in _TRANSPARENT or material.endswith("_stained_glass")
    color = QColor(int(color.red() * shade), int(color.green() * shade), int(color.blue() * shade),
                   52 if material == "barrier" else 82 if transparent else 255)
    image = QImage(16, 16, QImage.Format.Format_ARGB32_Premultiplied)
    image.fill(color)
    p = QPainter(image)
    light = QColor(255, 255, 255, 34)
    dark = QColor(0, 0, 0, 42)
    p.setPen(Qt.PenStyle.NoPen)
    if material == "note_block":
        p.fillRect(1, 1, 14, 14, QColor("#a37b51").darker(round(100 / shade)))
        p.fillRect(3, 3, 10, 10, QColor("#553b2b").darker(round(100 / shade)))
        for y in range(4, 13, 3):
            for x in range(4, 13, 3):
                p.fillRect(x, y, 1, 1, QColor("#c7955d"))
        p.fillRect(0, 0, 16, 1, light)
    elif transparent:
        p.setPen(QPen(QColor(color.red(), color.green(), color.blue(), 165), 1))
        p.drawRect(0, 0, 15, 15)
        p.setPen(QPen(QColor(245, 251, 255, 150), 1))
        p.drawLine(3, 3, 6, 6)
        p.drawLine(8, 8, 12, 12)
        if material == "barrier":
            p.setPen(QPen(QColor(235, 65, 80, 190), 2))
            p.drawEllipse(3, 3, 10, 10)
            p.drawLine(4, 12, 12, 4)
    elif material in {"iron_block", "gold_block", "emerald_block", "diamond_block", "quartz_block"}:
        p.fillRect(0, 0, 16, 1, light)
        p.fillRect(0, 0, 1, 16, light)
        p.fillRect(1, 14, 14, 1, dark)
        p.fillRect(14, 1, 1, 14, dark)
        p.fillRect(2, 3, 12, 1, light)
    elif material.endswith("_planks"):
        p.fillRect(0, 4, 16, 1, dark)
        p.fillRect(0, 10, 16, 1, dark)
        p.fillRect(5, 0, 1, 4, dark)
        p.fillRect(11, 5, 1, 5, dark)
        p.fillRect(2, 11, 1, 5, dark)
        p.fillRect(2, 7, 7, 1, light)
    elif material.startswith("redstone_lamp"):
        p.setPen(QPen(QColor("#523b2b"), 2))
        p.drawRect(1, 1, 14, 14)
        p.drawLine(1, 1, 14, 14)
        p.drawLine(1, 14, 14, 1)
        p.fillRect(5, 5, 6, 6, light)
    elif material in {"hay_block", "pumpkin", "bone_block"}:
        for x in (2, 5, 9, 13):
            p.fillRect(x, 0, 1, 16, dark)
        if material == "hay_block":
            p.fillRect(0, 3, 16, 1, QColor("#a36b36"))
            p.fillRect(0, 12, 16, 1, QColor("#a36b36"))
    elif material not in {"repeater", "redstone_wire", "redstone_wire_powered", "_torch_stem", "_torch_head", "_torch_lit"}:
        # Deterministic mottling keeps adjacent blocks readable without external assets.
        for i in range(17):
            x, y = (i * 7 + 3) % 16, (i * 11 + i // 3) % 16
            p.fillRect(x, y, 2, 1 if material != "glowstone" else 2, light if i % 2 else dark)
        if material == "grass_block" and normal[1] != 1:
            p.fillRect(0, 0, 16, 3, QColor("#6a943d").darker(round(100 / shade)))
    p.end()
    return image


class MinecraftPreviewWidget(QWidget):
    """An interactive actual-block preview; no OpenGL context is required."""

    hoverInfoChanged = pyqtSignal(str)
    groupSelected = pyqtSignal(object)
    groupMoved = pyqtSignal(object, object)
    groupDragStarted = pyqtSignal(object)
    groupDragFinished = pyqtSignal(object, bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(260, 230)
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setCursor(Qt.CursorShape.OpenHandCursor)
        self._blocks: list[_Block] = []
        self._faces: list[_Face] = []
        self._anchors: dict[object, _Vec] = {}
        self._target_id = None
        self._bounds: tuple[_Vec, _Vec] | None = None
        self._message = "选择 NBS 文件以预览实际方块结构"
        self._yaw = math.radians(42)
        self._elevation = math.radians(32)
        self._center: _Vec = (0.0, 0.0, 0.0)
        self._scale = 26.0
        self._pan = QPointF()
        self._drag_pos: QPointF | None = None
        self._drag_button = Qt.MouseButton.NoButton
        self._dirty = True
        self._cache: QPixmap | None = None
        self._dark = isDarkTheme()
        self._screen_faces: list[tuple[QPolygonF, QRectF, int]] = []
        self._hit_grid: dict[tuple[int, int], list[int]] = {}
        self._hover: int | None = None
        self._hover_text = ""
        self._group_offsets: dict[object, _Vec] = {}
        self._group_drag_id = None
        self._group_drag_start = QPointF()
        self._group_drag_origin: _Vec = (0, 0, 0)
        self._group_drag_base: _Vec = (0, 0, 0)
        self._group_drag_vertical = False
        self._group_drag_changed = False
        self._listener_position: _Vec | None = None
        self._listener_yaw = 0.0
        self._listener_forward: _Vec = (0.0, 0.0, 1.0)
        self._anchor_label_rects: list[QRectF] = []
        self._basis()

    def set_preview(self, data, anchors: dict, target_id, *, reset_camera=False):
        """Replace the preview with placements in absolute Minecraft coordinates."""
        first = not self._blocks and not self._anchors
        # Input events can arrive before the queued repaint. Old picking indices
        # must never address a replacement scene (including an empty scene).
        self._screen_faces = []
        self._hit_grid = {}
        self._group_offsets = {}
        self._anchors = {gid: tuple(float(v) for v in xyz) for gid, xyz in anchors.items()}
        self._target_id = target_id
        self._blocks = []
        placements = getattr(data, "blocks", ()) if data is not None else ()
        for block in placements:
            name, props = _parse_state(block.blockstate)
            if name in _AIR:
                continue
            full = _is_full(name, props)
            opaque = full and name not in _TRANSPARENT and not name.endswith("_stained_glass")
            self._blocks.append(_Block(tuple(block.position), block.blockstate, name, props,
                                       block.group_id, full, opaque))
        self._message = "" if self._blocks else "暂无方块；标记表示各轨道组的实际基准坐标"
        self._make_mesh()
        if self._blocks:
            self._bounds = (
                tuple(min(b.position[i] for b in self._blocks) for i in range(3)),
                tuple(max(b.position[i] + 1 for b in self._blocks) for i in range(3)),
            )
        else:
            self._bounds = None
        self._set_hover(None)
        if reset_camera or first:
            self.reset_view()
        else:
            self._invalidate()

    def set_message(self, message: str):
        self._message = message
        self.update()

    def set_selected_group(self, group_id):
        """Highlight an origin without replacing geometry or moving the camera."""
        if self._target_id != group_id:
            self._target_id = group_id
            self._invalidate()

    def set_listener(self, position, yaw=0.0):
        """Show the listening ear position; Minecraft yaw 0 faces +Z, 90 faces -X."""
        if position is None:
            self._listener_position = None
        else:
            xyz = tuple(float(value) for value in position)
            angle = float(yaw)
            if len(xyz) != 3 or not all(math.isfinite(value) for value in (*xyz, angle)):
                raise ValueError("监听坐标与朝向必须为有限数值")
            self._listener_position = xyz
            self._listener_yaw = angle % 360
            radians = math.radians(angle)
            self._listener_forward = (-math.sin(radians), 0.0, math.cos(radians))
        # The marker is an overlay, so moving it does not rerender every block.
        self.update()

    def fit_all(self):
        # A time-window preview can be thousands of blocks from the group's
        # original base coordinate. Fit the generated window in that case.
        points = [] if self._bounds else list(self._anchors.values())
        if self._bounds:
            low, high = self._bounds
            points.extend((x, y, z) for x in (low[0], high[0])
                          for y in (low[1], high[1]) for z in (low[2], high[2]))
        if self._listener_position is not None:
            points.append(self._listener_position)
        if not points:
            points = [(-3, 0, -3), (3, 3, 3)]
        low = tuple(min(p[i] for p in points) for i in range(3))
        high = tuple(max(p[i] for p in points) for i in range(3))
        self._center = tuple((low[i] + high[i]) / 2 for i in range(3))
        self._pan = QPointF()
        projected = [self._project_units(p) for p in points]
        sx = max(4.0, max(p[0] for p in projected) - min(p[0] for p in projected))
        sy = max(4.0, max(p[1] for p in projected) - min(p[1] for p in projected))
        self._scale = max(_MIN_SCALE, min(100.0, max(100, self.width() - 120) / sx,
                                   max(80, self.height() - 150) / sy))
        self._invalidate()

    def reset_view(self):
        self._yaw = math.radians(42)
        self._elevation = math.radians(32)
        self._basis()
        self.fit_all()

    def zoom(self, factor: float):
        if math.isfinite(factor) and factor > 0:
            self._scale = max(_MIN_SCALE, min(240.0, self._scale * factor))
            self._invalidate()

    def _basis(self):
        sy, cy = math.sin(self._yaw), math.cos(self._yaw)
        se, ce = math.sin(self._elevation), math.cos(self._elevation)
        self._right = (cy, 0.0, -sy)
        self._up = (-sy * se, ce, -cy * se)
        self._view = (sy * ce, se, cy * ce)

    def _project_units(self, point: _Vec) -> tuple[float, float, float]:
        x, y, z = point[0] - self._center[0], point[1] - self._center[1], point[2] - self._center[2]
        return (x * self._right[0] + z * self._right[2],
                -(x * self._up[0] + y * self._up[1] + z * self._up[2]),
                x * self._view[0] + y * self._view[1] + z * self._view[2])

    def _project(self, point: _Vec) -> QPointF:
        x, y, _ = self._project_units(point)
        return QPointF(self.width() / 2 + self._pan.x() + x * self._scale,
                       self.height() / 2 + self._pan.y() + y * self._scale)

    def _invalidate(self):
        self._dirty = True
        self.update()

    def _box(self, index: int, low: _Vec, high: _Vec, material: str,
             hidden: set[tuple[int, int, int]] | None = None):
        x, y, z = low
        X, Y, Z = high
        corners = (
            ((X, Y, Z), (X, Y, z), (X, y, z), (X, y, Z)),
            ((x, Y, z), (x, Y, Z), (x, y, Z), (x, y, z)),
            ((x, Y, z), (X, Y, z), (X, Y, Z), (x, Y, Z)),
            ((x, y, Z), (X, y, Z), (X, y, z), (x, y, z)),
            ((x, Y, Z), (X, Y, Z), (X, y, Z), (x, y, Z)),
            ((X, Y, z), (x, Y, z), (x, y, z), (X, y, z)),
        )
        bx, by, bz = self._blocks[index].position
        for normal, vertices in zip(_NORMALS, corners):
            if hidden and normal in hidden:
                continue
            world = tuple((vx + bx, vy + by, vz + bz) for vx, vy, vz in vertices)
            center = tuple(sum(v[i] for v in world) / 4 for i in range(3))
            area = ((Y - y) * (Z - z) if normal[0] else
                    (X - x) * (Z - z) if normal[1] else (X - x) * (Y - y))
            self._faces.append(_Face(world, normal, center, index, material, area))

    def _make_mesh(self):
        self._faces = []
        occupied = {b.position: b for b in self._blocks}
        for index, block in enumerate(self._blocks):
            name, props = block.name, block.properties
            material = "redstone_lamp_lit" if name == "redstone_lamp" and props.get("lit") == "true" else name
            if block.full:
                hidden = set()
                for normal in _NORMALS:
                    adjacent = occupied.get(tuple(block.position[i] + normal[i] for i in range(3)))
                    # A wire or repeater never hides a neighbouring full cube's face.
                    if adjacent and (adjacent.opaque or (adjacent.full and adjacent.name == name and not block.opaque)):
                        hidden.add(normal)
                self._box(index, (0, 0, 0), (1, 1, 1), material, hidden)
            elif name == "redstone_wire":
                material = "redstone_wire_powered" if int(props.get("power", "0")) else name
                self._box(index, (.35, .012, .35), (.65, .034, .65), material)
                connections = {d: props.get(d, "none") for d in ("north", "south", "west", "east")}
                if all(v == "none" for v in connections.values()) and not any(d in props for d in connections):
                    connections = dict.fromkeys(connections, "side")
                for direction, mode in connections.items():
                    if mode == "none":
                        continue
                    low, high = {
                        "north": ((.42, .012, 0), (.58, .034, .5)),
                        "south": ((.42, .012, .5), (.58, .034, 1)),
                        "west": ((0, .012, .42), (.5, .034, .58)),
                        "east": ((.5, .012, .42), (1, .034, .58)),
                    }[direction]
                    self._box(index, low, high, material)
                    if mode == "up":
                        low, high = {
                            "north": ((.42, .03, 0), (.58, 1, .025)),
                            "south": ((.42, .03, .975), (.58, 1, 1)),
                            "west": ((0, .03, .42), (.025, 1, .58)),
                            "east": ((.975, .03, .42), (1, 1, .58)),
                        }[direction]
                        self._box(index, low, high, material)
            elif name in {"repeater", "comparator"}:
                self._box(index, (0, 0, 0), (1, .125, 1), "repeater")
                dx, dz = {"north": (0, -1), "south": (0, 1), "east": (1, 0), "west": (-1, 0)}.get(props.get("facing", "north"), (0, -1))
                powered = props.get("powered") == "true"
                head = "_torch_lit" if powered else "_torch_head"
                # Output points along facing. Delay moves the input torch along this axis.
                delay = max(1, min(4, int(props.get("delay", "1"))))
                for offset in (.3, -.1 - (delay - 1) * .075):
                    cx, cz = .5 + dx * offset, .5 + dz * offset
                    self._box(index, (cx - .055, .125, cz - .055), (cx + .055, .36, cz + .055), "_torch_stem")
                    self._box(index, (cx - .09, .29, cz - .09), (cx + .09, .48, cz + .09), head)
                if dx:
                    self._box(index, (.12, .126, .455), (.88, .145, .545), "redstone_wire_powered" if powered else "redstone_wire")
                else:
                    self._box(index, (.455, .126, .12), (.545, .145, .88), "redstone_wire_powered" if powered else "redstone_wire")
            elif name in {"torch", "redstone_torch"}:
                self._box(index, (.43, 0, .43), (.57, .55, .57), "_torch_stem")
                self._box(index, (.39, .4, .39), (.61, .65, .61), "_torch_head" if props.get("lit") == "false" else "_torch_lit")
            elif name.endswith("_slab"):
                top = props.get("type") == "top"
                self._box(index, (0, .5 if top else 0, 0), (1, 1 if top else .5, 1), name.removesuffix("_slab"))
            elif name.endswith(("_carpet", "_pressure_plate")):
                self._box(index, (0, 0, 0), (1, .0625, 1), material)
            elif name.endswith("_stairs"):
                upside = props.get("half") == "top"
                self._box(index, (0, .5 if upside else 0, 0), (1, 1 if upside else .5, 1), material)
                low, high = {"north": ((0, 0, 0), (1, 1, .5)), "south": ((0, 0, .5), (1, 1, 1)),
                             "east": ((.5, 0, 0), (1, 1, 1)), "west": ((0, 0, 0), (.5, 1, 1))}.get(props.get("facing"), ((0, 0, 0), (1, 1, .5)))
                self._box(index, (low[0], 0 if upside else .5, low[2]), (high[0], .5 if upside else 1, high[2]), material)
            elif name.endswith("_pane"):
                self._box(index, (.4375, 0, 0), (.5625, 1, 1), "glass")
            elif name.endswith("_fence"):
                self._box(index, (.375, 0, .375), (.625, 1.5, .625), material)

    def _draw_grid(self, painter: QPainter):
        floor = self._bounds[0][1] - .045 if self._bounds else min((p[1] for p in self._anchors.values()), default=0) - .045
        step = max(1, 10 ** math.floor(math.log10(max(1, 36 / self._scale))))
        if step * self._scale < 18:
            step *= 5
        radius = min(100000, max(self.width(), self.height()) / max(.001, self._scale) * 1.2)
        cx, _, cz = self._center
        x0, x1 = math.floor((cx - radius) / step) * step, math.ceil((cx + radius) / step) * step
        z0, z1 = math.floor((cz - radius) / step) * step, math.ceil((cz + radius) / step) * step
        color = QColor(130, 145, 161, 33 if self._dark else 42)
        painter.setPen(QPen(color, 1))
        for x in range(int(x0), int(x1) + 1, int(step)):
            painter.drawLine(self._project((x, floor, z0)), self._project((x, floor, z1)))
        for z in range(int(z0), int(z1) + 1, int(step)):
            painter.drawLine(self._project((x0, floor, z)), self._project((x1, floor, z)))

    def _render_scene(self):
        self._dark = isDarkTheme()
        ratio = self.devicePixelRatioF()
        self._cache = QPixmap(round(self.width() * ratio), round(self.height() * ratio))
        self._cache.setDevicePixelRatio(ratio)
        self._cache.fill(QColor("#1c232c" if self._dark else "#eef3f7"))
        painter = QPainter(self._cache)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        self._draw_grid(painter)
        projected = []
        viewport = QRectF(self.rect()).adjusted(-2, -2, 2, 2)
        view = self._view
        scale = self._scale
        scale_squared = scale * scale
        minimum_area = .6 if self._drag_pos is not None else .13
        rx, rz = self._right[0] * scale, self._right[2] * scale
        ux, uy, uz = (-axis * scale for axis in self._up)
        ox = self.width() / 2 + self._pan.x() - self._center[0] * rx - self._center[2] * rz
        oy = (self.height() / 2 + self._pan.y() - self._center[0] * ux
              - self._center[1] * uy - self._center[2] * uz)
        width, height = self.width(), self.height()
        face_margins = scale * 1.8
        for face in self._faces:
            dot = face.normal[0] * view[0] + face.normal[1] * view[1] + face.normal[2] * view[2]
            if dot <= .0001 or face.area * dot * scale_squared < minimum_area:
                continue
            offset = self._group_offsets.get(self._blocks[face.block].group_id)
            cx, cy, cz = face.center
            if offset:
                cx, cy, cz = cx + offset[0], cy + offset[1], cz + offset[2]
            px, py = cx * rx + cz * rz + ox, cx * ux + cy * uy + cz * uz + oy
            if not (-face_margins <= px <= width + face_margins and
                    -face_margins <= py <= height + face_margins):
                continue
            depth = cx * view[0] + cy * view[1] + cz * view[2]
            face_ox = ox + (offset[0] * rx + offset[2] * rz if offset else 0)
            face_oy = oy + (offset[0] * ux + offset[1] * uy + offset[2] * uz if offset else 0)
            polygon = QPolygonF([QPointF(vx * rx + vz * rz + face_ox, vx * ux + vy * uy + vz * uz + face_oy)
                                 for vx, vy, vz in face.vertices])
            rect = polygon.boundingRect()
            if rect.intersects(viewport):
                projected.append((depth, face, polygon, rect))
        projected.sort(key=lambda item: item[0])
        self._screen_faces = []
        self._hit_grid = {}
        detailed = self._scale >= 9 and self._drag_pos is None
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, self._scale >= 4)
        for _, face, polygon, rect in projected:
            texture = _texture(face.material, face.normal)
            # Each face is an affine parallelogram in orthographic projection.
            if detailed:
                a, b, d = polygon[0], polygon[1], polygon[3]
                painter.setTransform(QTransform((b.x() - a.x()) / 16, (b.y() - a.y()) / 16,
                                                (d.x() - a.x()) / 16, (d.y() - a.y()) / 16,
                                                a.x(), a.y()))
                painter.drawImage(QPointF(0, 0), texture)
                painter.resetTransform()
            else:
                painter.setBrush(texture.pixelColor(8, 8))
                painter.setPen(Qt.PenStyle.NoPen)
                painter.drawPolygon(polygon)
            if self._scale >= 5:
                painter.setBrush(Qt.BrushStyle.NoBrush)
                painter.setPen(QPen(QColor(10, 18, 24, 50), .65))
                painter.drawPolygon(polygon)
            fi = len(self._screen_faces)
            self._screen_faces.append((polygon, rect, face.block))
            left, right = max(0, int(rect.left()) // 48), min(self.width() // 48, int(rect.right()) // 48)
            top, bottom = max(0, int(rect.top()) // 48), min(self.height() // 48, int(rect.bottom()) // 48)
            for gx in range(left, right + 1):
                for gy in range(top, bottom + 1):
                    self._hit_grid.setdefault((gx, gy), []).append(fi)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        self._draw_anchors(painter)
        painter.end()
        self._dirty = False

    def _draw_anchors(self, painter: QPainter):
        painter.setFont(QFont("Microsoft YaHei UI", 8))
        labels: list[QRectF] = []
        self._anchor_label_rects = labels
        # Draw the active origin last so it remains readable when origins coincide.
        ordered = sorted(self._anchors, key=lambda gid: gid == self._target_id)
        for gid in ordered:
            xyz = self._anchors[gid]
            point = self._project(xyz)
            if not QRectF(self.rect()).adjusted(-80, -60, 80, 60).contains(point):
                continue
            active = gid == self._target_id
            color = QColor("#ffbe4f") if active else QColor("#65b7e6" if self._dark else "#347daa")
            painter.setPen(QPen(color, 2 if active else 1.3))
            painter.setBrush(QColor(color.red(), color.green(), color.blue(), 35))
            painter.drawEllipse(point, 6 if active else 4, 6 if active else 4)
            painter.drawLine(point + QPointF(-9, 0), point + QPointF(9, 0))
            painter.drawLine(point + QPointF(0, -9), point + QPointF(0, 9))
            coords = ", ".join(f"{value:g}" for value in xyz)
            text = f"组 {gid} 起点 ({coords})"
            metrics = painter.fontMetrics()
            label = QRectF(point.x() + 12, point.y() - 26, metrics.horizontalAdvance(text) + 14, 23)
            label.moveLeft(max(4, min(label.left(), self.width() - label.width() - 4)))
            for _ in range(8):
                if not any(label.intersects(other) for other in labels):
                    break
                label.translate(0, 25)
            labels.append(label)
            painter.setPen(QPen(QColor(color.red(), color.green(), color.blue(), 130), 1))
            painter.drawLine(point, label.bottomLeft() + QPointF(5, 0))
            painter.setBrush(QColor("#29333f" if self._dark else "#ffffff"))
            painter.drawRoundedRect(label, 4, 4)
            painter.setPen(color if self._dark else QColor("#63460b") if active else QColor("#30647f"))
            painter.drawText(label, Qt.AlignmentFlag.AlignCenter, text)

    def _draw_axes(self, painter: QPainter):
        center = QPointF(self.width() - 67, self.height() - 67)
        painter.setBrush(QColor(30, 38, 47, 210) if self._dark else QColor(255, 255, 255, 215))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(QRectF(self.width() - 125, self.height() - 124, 117, 115), 8, 8)
        painter.setFont(QFont("Microsoft YaHei UI", 7))
        axes = [(0, QColor("#e37370"), "+X 东"), (1, QColor("#67b97b"), "+Y 上"), (2, QColor("#639be0"), "+Z 南")]
        axes.sort(key=lambda item: self._view[item[0]])
        for index, color, label in axes:
            vector = QPointF(self._right[index] * 31, -self._up[index] * 31)
            end = center + vector
            painter.setPen(QPen(color, 2))
            painter.drawLine(center, end)
            painter.setBrush(color)
            painter.drawEllipse(end, 2.5, 2.5)
            painter.drawText(QRectF(end.x() - 24, end.y() - 16 if vector.y() <= 0 else end.y() + 4, 50, 14),
                             Qt.AlignmentFlag.AlignCenter, label)
        painter.setPen(QColor("#a0acb8" if self._dark else "#6d7c8c"))
        painter.drawText(QRectF(self.width() - 125, self.height() - 25, 117, 14),
                         Qt.AlignmentFlag.AlignCenter, "−X 西 · −Z 北")

    def _draw_listener(self, painter: QPainter):
        if self._listener_position is None:
            return
        xyz = self._listener_position
        point = self._project(xyz)
        color = QColor("#d5a2ff" if self._dark else "#8e3bc2")
        painter.setFont(QFont("Microsoft YaHei UI", 8))
        painter.setPen(color)
        coords = ", ".join(f"{value:g}" for value in xyz)
        if not QRectF(self.rect()).adjusted(12, 12, -12, -12).contains(point):
            painter.drawText(QRectF(13, 12, self.width() - 26, 38),
                             Qt.TextFlag.TextWordWrap,
                             f"监听点 ({coords}) 在视野外 · 按 F 适应全部")
            return
        floor = self._bounds[0][1] - .045 if self._bounds else xyz[1] - 1.62
        painter.setPen(QPen(QColor(color.red(), color.green(), color.blue(), 130),
                            1, Qt.PenStyle.DashLine))
        ground = self._project((xyz[0], floor, xyz[2]))
        painter.drawLine(point, ground)
        painter.drawEllipse(ground, 3, 3)
        direction = self._project(tuple(xyz[i] + self._listener_forward[i] for i in range(3))) - point
        length = math.hypot(direction.x(), direction.y())
        if length > .001:
            direction *= 28 / length
            end = point + direction
            side = QPointF(-direction.y(), direction.x()) * .16
            painter.setPen(QPen(color, 2))
            painter.drawLine(point, end)
            painter.setBrush(color)
            painter.drawPolygon(QPolygonF([end, end - direction * .28 + side,
                                           end - direction * .28 - side]))
        painter.setPen(QPen(color, 2))
        painter.setBrush(QColor("#242331" if self._dark else "#ffffff"))
        painter.drawEllipse(point, 7, 7)
        # A small headset distinguishes the ear position from group origins.
        painter.drawArc(QRectF(point.x() - 10, point.y() - 10, 20, 20), 0, 180 * 16)
        painter.drawLine(point + QPointF(-10, -1), point + QPointF(-10, 5))
        painter.drawLine(point + QPointF(10, -1), point + QPointF(10, 5))
        text = f"监听双耳 ({coords}) · 朝向 {self._listener_yaw:g}°"
        width = painter.fontMetrics().horizontalAdvance(text) + 14
        for dx, dy in ((16, -42), (16, 12), (-width - 16, -42), (-width - 16, 12)):
            label = QRectF(point.x() + dx, point.y() + dy, width, 24)
            label.moveLeft(max(4, min(label.left(), self.width() - width - 4)))
            label.moveTop(max(4, min(label.top(), self.height() - 51)))
            if not any(label.intersects(other) for other in self._anchor_label_rects):
                break
        painter.setBrush(QColor("#292435" if self._dark else "#ffffff"))
        painter.setPen(QPen(color, 1))
        painter.drawRoundedRect(label, 4, 4)
        painter.drawText(label, Qt.AlignmentFlag.AlignCenter, text)

    def paintEvent(self, event):
        if self._dirty or self._cache is None or isDarkTheme() != self._dark:
            self._render_scene()
        painter = QPainter(self)
        painter.drawPixmap(0, 0, self._cache)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        if self._hover is not None and self._drag_pos is None:
            painter.setBrush(QColor(255, 200, 84, 65))
            painter.setPen(QPen(QColor("#ffca58"), 2))
            for polygon, _, index in self._screen_faces:
                if index == self._hover:
                    painter.drawPolygon(polygon)
        self._draw_listener(painter)
        self._draw_axes(painter)
        painter.setFont(QFont("Microsoft YaHei UI", 8))
        painter.setPen(QColor("#b8c4cf" if self._dark else "#596b7a"))
        painter.drawText(QRectF(13, self.height() - 26, max(10, self.width() - 145), 18),
                         Qt.AlignmentFlag.AlignLeft, "等比例 · 1 格 = 1 方块 · 材质示意")
        if self._message:
            rect = QRectF(18, 18, max(20, self.width() - 36), 64)
            painter.setPen(QColor("#cdd8e1" if self._dark else "#52677a"))
            painter.drawText(rect, Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop | Qt.TextFlag.TextWordWrap,
                             self._message)
        painter.end()

    def _describe(self, index: int) -> str:
        block = self._blocks[index]
        offset = self._group_offsets.get(block.group_id, (0, 0, 0))
        x, y, z = (block.position[i] + offset[i] for i in range(3))
        name = _NAMES.get(block.name, block.name)
        text = f"({x:g}, {y:g}, {z:g}) · {name} · 组 {block.group_id}"
        if block.name == "note_block":
            note = int(block.properties.get("note", "0"))
            semitone = (note + 6) % 12
            pitch = ("C", "C♯", "D", "D♯", "E", "F", "F♯", "G", "G♯", "A", "A♯", "B")[semitone]
            octave = (note + 6) // 12 + 3
            instrument = block.properties.get("instrument", "harp")
            text += f" · {_INSTRUMENTS.get(instrument, instrument)} · {pitch}{octave} / note={note}"
        return text + "\n" + block.state

    def _set_hover(self, index: int | None, text: str = ""):
        text = self._describe(index) if index is not None else text
        changed = index != self._hover
        self._hover = index
        if text != self._hover_text:
            self._hover_text = text
            self.hoverInfoChanged.emit(text)
            self.setToolTip(text)
        if changed:
            self.update()

    def mousePressEvent(self, event):
        if event.button() in (Qt.MouseButton.LeftButton, Qt.MouseButton.MiddleButton, Qt.MouseButton.RightButton):
            self.setFocus()
            if event.button() == Qt.MouseButton.LeftButton:
                anchor_id = self._anchor_at(event.position())
                block_id = self._block_at(event.position())
                group_id = anchor_id if anchor_id is not None else (
                    self._blocks[block_id].group_id if block_id is not None else None)
                if group_id is not None:
                    self.set_selected_group(group_id)
                    self.groupSelected.emit(group_id)
                if anchor_id is not None or event.modifiers() & Qt.KeyboardModifier.AltModifier:
                    drag_id = group_id if group_id is not None else self._target_id
                    if drag_id in self._anchors:
                        self._group_drag_id = drag_id
                        self._group_drag_start = event.position()
                        self._group_drag_origin = self._anchors[drag_id]
                        self._group_drag_base = self._group_offsets.get(drag_id, (0, 0, 0))
                        self._group_drag_vertical = bool(event.modifiers() & Qt.KeyboardModifier.ShiftModifier)
                        self._group_drag_changed = False
                        self._set_hover(None)
                        self.setCursor(Qt.CursorShape.SizeVerCursor if self._group_drag_vertical else Qt.CursorShape.SizeAllCursor)
                        self.groupDragStarted.emit(drag_id)
                        event.accept()
                        return
            self._drag_pos = event.position()
            self._drag_button = event.button()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
            self._set_hover(None)
            event.accept()

    def mouseMoveEvent(self, event):
        point = event.position()
        if self._group_drag_id is not None:
            delta = point - self._group_drag_start
            origin = self._group_drag_origin
            if self._group_drag_vertical:
                dy = round(-delta.y() / (self._scale * max(.08, math.cos(self._elevation))))
                coords = (origin[0], max(-64, min(320, origin[1] + dy)), origin[2])
            else:
                sine = math.sin(self._elevation)
                # Near a horizontal view, use a bounded plane intersection.
                sine = math.copysign(max(.08, abs(sine)), sine)
                horizontal = delta.x() / self._scale
                forward = delta.y() / (self._scale * sine)
                dx = round(math.cos(self._yaw) * horizontal + math.sin(self._yaw) * forward)
                dz = round(-math.sin(self._yaw) * horizontal + math.cos(self._yaw) * forward)
                coords = (max(-30000000, min(30000000, origin[0] + dx)), origin[1],
                          max(-30000000, min(30000000, origin[2] + dz)))
            gid = self._group_drag_id
            if coords != self._anchors[gid]:
                self._anchors[gid] = coords
                self._group_offsets[gid] = tuple(self._group_drag_base[i] + coords[i] - origin[i] for i in range(3))
                self._group_drag_changed = True
                self.groupMoved.emit(gid, tuple(int(v) for v in coords))
                self._invalidate()
            event.accept()
            return
        if self._drag_pos is not None:
            delta = point - self._drag_pos
            self._drag_pos = point
            if self._drag_button == Qt.MouseButton.LeftButton and not event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
                self._yaw += delta.x() * .009
                self._elevation = max(math.radians(-80), min(math.radians(85), self._elevation + delta.y() * .007))
                self._basis()
            else:
                self._pan += delta
            self._invalidate()
            event.accept()
            return
        anchor = self._anchor_at(point)
        if anchor is not None:
            xyz = self._anchors[anchor]
            self._set_hover(None, f"组 {anchor} 基准坐标 ({', '.join(f'{v:g}' for v in xyz)}) · 拖动调整 XZ，Shift+拖动调整 Y")
            return
        self._set_hover(self._block_at(point))

    def _anchor_at(self, point):
        # Active origin has precedence when two groups share a base coordinate.
        for gid in sorted(self._anchors, key=lambda value: value != self._target_id):
            marker = self._project(self._anchors[gid])
            if (marker - point).manhattanLength() < 14:
                return gid
        return None

    def _block_at(self, point):
        for fi in reversed(self._hit_grid.get((int(point.x()) // 48, int(point.y()) // 48), [])):
            polygon, rect, index = self._screen_faces[fi]
            if rect.contains(point) and polygon.containsPoint(point, Qt.FillRule.OddEvenFill):
                return index
        return None

    def mouseReleaseEvent(self, event):
        if self._group_drag_id is not None:
            gid, changed = self._group_drag_id, self._group_drag_changed
            self._group_drag_id = None
            self.setCursor(Qt.CursorShape.OpenHandCursor)
            self.groupDragFinished.emit(gid, changed)
            self._invalidate()
            event.accept()
            return
        if self._drag_pos is not None:
            self._drag_pos = None
            self._drag_button = Qt.MouseButton.NoButton
            self.setCursor(Qt.CursorShape.OpenHandCursor)
            self._invalidate()
            event.accept()

    def wheelEvent(self, event):
        delta = event.angleDelta().y() or event.pixelDelta().y()
        if not delta:
            return
        # Keep the world point beneath the cursor fixed during wheel zoom.
        origin = QPointF(self.width() / 2, self.height() / 2)
        before = event.position() - origin - self._pan
        previous = self._scale
        self.zoom(math.exp(max(-3, min(3, delta / 600))))
        self._pan += before * (1 - self._scale / previous)
        self._invalidate()
        event.accept()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_R:
            self.reset_view()
        elif event.key() == Qt.Key.Key_F:
            self.fit_all()
        elif event.key() in (Qt.Key.Key_Plus, Qt.Key.Key_Equal):
            self.zoom(1.25)
        elif event.key() == Qt.Key.Key_Minus:
            self.zoom(.8)
        else:
            super().keyPressEvent(event)

    def leaveEvent(self, event):
        self._set_hover(None)
        super().leaveEvent(event)

    def resizeEvent(self, event):
        self._invalidate()
        super().resizeEvent(event)
