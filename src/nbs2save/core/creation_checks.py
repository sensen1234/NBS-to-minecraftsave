"""Actionable authoring checks, without changing a project or generating blocks."""

from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path

from .custom_instruments import validate_custom_instruments


@dataclass(frozen=True)
class CreationIssue:
    severity: str
    title: str
    detail: str


def check_creation(song, groups, config):
    issues = []
    assigned = defaultdict(list)
    origins = defaultdict(list)
    for gid, group in groups.items():
        try:
            origin = tuple(int(v) for v in group.get("base_coords", ()))
            if len(origin) != 3:
                raise ValueError
            origins[origin].append(gid)
        except (ValueError, TypeError):
            issues.append(CreationIssue("error", f"组 {gid} 的坐标无法使用", "XYZ 坐标需填写三个整数。"))
        for layer in set(group.get("layers", ())):
            assigned[layer].append(gid)
        if config.get("type") == "mcfunction" and group.get("generation_mode") in {"staircase", "staircase_up"}:
            issues.append(CreationIssue("error", f"组 {gid} 使用阶梯布局", "阶梯布局需要 Schematic 输出，请在项目页切换输出格式。"))
    if not groups:
        issues.append(CreationIssue("error", "尚无轨道组", "添加轨道组并分配 NBS 轨道后再生成结构。"))
    layer_counts = Counter(note.layer for note in song.notes)
    missing = sorted(set(layer_counts) - set(assigned))
    if missing:
        count = sum(layer_counts[layer] for layer in missing)
        issues.append(CreationIssue("warning", f"{count:,} 个音符尚未分组", "轨道 " + "、".join(map(str, missing)) + " 未分配给任何组，导出时会被跳过。"))
    duplicate = sorted(layer for layer, ids in assigned.items() if len(ids) > 1 and layer in layer_counts)
    if duplicate:
        issues.append(CreationIssue("info", "部分轨道在多组中重复使用", "轨道 " + "、".join(map(str, duplicate)) + " 会在多个位置生成；适合有意叠加，请确认布局。"))
    empty = [str(gid) for gid, group in groups.items() if not any(layer_counts[layer] for layer in group.get("layers", ()))]
    if empty:
        issues.append(CreationIssue("warning", "部分组没有可用音符", "组 " + "、".join(empty) + " 中的轨道没有音符，请核对轨道 ID（从 0 开始）。"))
    for origin, ids in origins.items():
        if len(ids) > 1:
            issues.append(CreationIssue("warning", "多个组共用同一起点", f"组 {'、'.join(map(str, ids))} 位于 {origin}，结构可能相互覆盖。请在工作台调整并查看实际结构。"))
    selected = [note for note in song.notes if note.layer in assigned]
    outside = sum(not 33 <= note.key <= 57 for note in selected)
    if outside:
        issues.append(CreationIssue("warning", f"{outside:,} 个音符超出当前音域", "当前结构支持 NBS key 33–57；超出范围的音符将使用 note=0。建议先在 NBS 中调整八度。"))
    try:
        instruments = validate_custom_instruments(config)
    except (ValueError, TypeError) as exc:
        issues.append(CreationIssue("error", "自定义音色配置有误", str(exc)))
        instruments = []
    configured = {item["nbs_id"] for item in instruments}
    used = {note.instrument for note in selected}
    default_count = getattr(song.header, "default_instruments", 16)
    undefined = sorted(i for i in used if i >= default_count and i not in configured)
    if undefined:
        issues.append(CreationIssue("warning", "自定义乐器尚未配置", "NBS ID " + "、".join(map(str, undefined)) + " 会回退到默认音色。请在音色页导入并关联 OGG。"))
    for item in instruments:
        if item["nbs_id"] in used and not Path(item["sound_file"]).is_file():
            issues.append(CreationIssue("error", f"找不到采样：{item['name']}", "重新选择对应的单声道 OGG 文件，才能生成空间试听和 NoteBetter 音效包。"))
    if not song.notes:
        issues.append(CreationIssue("warning", "NBS 文件中没有音符", "请在 Note Block Studio 中确认文件内容后重新保存。"))
    return issues
