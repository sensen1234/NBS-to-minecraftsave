"""Custom NBS instruments and an installable NoteBetter Fabric resource bundle.

The mapping format comes from chsbuffer/NoteBetter's SoundConfig and
NoteBlockMixin, rather than a resource-pack-only replacement of vanilla sounds.
See the source links written into each bundle's README.
"""

from __future__ import annotations

import io
import json
import math
import os
import re
import struct
import tempfile
import zipfile
from collections.abc import Mapping, Sequence
from functools import lru_cache
from pathlib import Path

from .constants import INSTRUMENT_BLOCK_MAPPING, INSTRUMENT_MAPPING, NOTEPITCH_MAPPING

_FIELDS = ("nbs_id", "name", "base_block", "sound_file", "sound_id", "root_key")
_IDENTIFIER = re.compile(r"^[a-z0-9_.-]+:[a-z0-9_./-]+$")
NOTEBETTER_REPOSITORY = "https://github.com/chsbuffer/NoteBetter"
NOTEBETTER_CONFIG_PATH = "config/notebetterfabric.json"
RESOURCE_PACK_PATH = "resourcepacks/nbs2save-custom-instruments.zip"

# Resource pack versions, independently of schematic/data pack versions.
# Source: https://github.com/misode/mcmeta/blob/summary/versions/data.json
_PACK_FORMATS = {
    "1.16.5": 6,
    "1.17": 7, "1.17.1": 7,
    "1.18": 8, "1.18.1": 8, "1.18.2": 8,
    "1.19": 9, "1.19.1": 9, "1.19.2": 9, "1.19.3": 12, "1.19.4": 13,
    "1.20": 15, "1.20.1": 15, "1.20.2": 18, "1.20.3": 22,
    "1.20.4": 22, "1.20.5": 32, "1.20.6": 32,
    "1.21": 34, "1.21.1": 34, "1.21.2": 42, "1.21.3": 42,
    "1.21.4": 46, "1.21.5": 55,
}


def _entries(config_or_list):
    if config_or_list is None:
        return ()
    if isinstance(config_or_list, Mapping):
        config_or_list = config_or_list.get("custom_instruments", ())
    if not isinstance(config_or_list, Sequence) or isinstance(config_or_list, (str, bytes)):
        raise ValueError("custom_instruments 必须是音色列表。")
    signature = []
    for item in config_or_list:
        if not isinstance(item, Mapping):
            raise ValueError("每个自定义音色必须是配置对象。")
        values = tuple(item.get(key) for key in _FIELDS)
        if any(isinstance(value, (dict, list, set)) for value in values):
            raise ValueError("自定义音色字段格式不正确。")
        signature.append(values)
    return tuple(signature)


def _identifier(value, label):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label}不能为空。")
    value = value.strip()
    if ":" not in value:
        value = "minecraft:" + value
    if not _IDENTIFIER.fullmatch(value):
        raise ValueError(f"{label}必须是合法方块/声音 ID，例如 minecraft:diamond_block。")
    path = value.split(":", 1)[1]
    if any(part in ("", ".", "..") for part in path.split("/")):
        raise ValueError(f"{label}包含不安全的路径。")
    return value


@lru_cache(maxsize=64)
def _normalize(signature):
    normalized = []
    ids, blocks, sounds = set(), set(), set()
    for nbs_id, name, base_block, sound_file, sound_id, root_key in signature:
        if type(nbs_id) is not int or not 0 <= nbs_id <= 255:
            raise ValueError("NBS 乐器 ID 必须是 0–255 的整数。")
        if nbs_id in ids:
            raise ValueError(f"NBS 乐器 ID {nbs_id} 重复。")
        name = name if name is not None else f"自定义音色 {nbs_id}"
        if not isinstance(name, str) or not name.strip():
            raise ValueError(f"音色 {nbs_id} 的名称不能为空。")
        base_block = _identifier(base_block, "底座方块")
        if base_block in blocks:
            raise ValueError(f"底座方块 {base_block} 重复；NoteBetter 会同时播放重复映射。")
        sound_id = _identifier(sound_id or f"nbs2save:instrument_{nbs_id}", "声音 ID")
        if sound_id in sounds:
            raise ValueError(f"声音 ID {sound_id} 重复。")
        root_key = 45 if root_key is None else root_key
        if type(root_key) is not int or not 0 <= root_key <= 87:
            raise ValueError("样本基准音高 root_key 必须是 0–87 的 NBS 音高。")
        if sound_file is None:
            sound_file = ""
        if not isinstance(sound_file, (str, os.PathLike)):
            raise ValueError(f"音色 {nbs_id} 的样本路径格式不正确。")
        sound_file = str(Path(sound_file).expanduser()) if sound_file else ""
        normalized.append((nbs_id, name.strip(), base_block, sound_file, sound_id, root_key))
        ids.add(nbs_id)
        blocks.add(base_block)
        sounds.add(sound_id)
    return tuple(normalized)


def validate_custom_instruments(config_or_list, require_files=False):
    """Return independent normalized dictionaries; optionally verify mono Vorbis files.

    With ``require_files=False`` an edited configuration can be previewed even
    when its sample has not been selected yet. No caller's configuration mutates.
    """
    try:
        entries = _normalize(_entries(config_or_list))
    except TypeError as error:
        raise ValueError("自定义音色字段格式不正确。") from error
    result = [dict(zip(_FIELDS, item)) for item in entries]
    if require_files:
        for item in result:
            _load_ogg(item["sound_file"])
    return result


def resolve_custom_instrument(instrument_id, config=None):
    """Return the configured sample metadata for an NBS instrument, if any."""
    try:
        entries = _normalize(_entries(config))
    except TypeError as error:
        raise ValueError("自定义音色字段格式不正确。") from error
    for item in entries:
        if item[0] == instrument_id:
            return dict(zip(_FIELDS, item))
    return None


def get_note_block_info(note, config=None):
    """Resolve all exporters identically, preserving vanilla fallback behavior."""
    custom = resolve_custom_instrument(note.instrument, config)
    if custom is not None:
        # NoteBetter selects by the block underneath, never by an invented
        # instrument property. "harp" is valid across every supported version.
        instrument, base_block = "harp", custom["base_block"]
    else:
        instrument = INSTRUMENT_MAPPING.get(note.instrument, "harp")
        base_block = INSTRUMENT_BLOCK_MAPPING.get(note.instrument, "minecraft:stone")
    return instrument, base_block, NOTEPITCH_MAPPING.get(note.key, "0")


@lru_cache(maxsize=1)
def _crc_table():
    table = []
    for value in range(256):
        value <<= 24
        for _ in range(8):
            value = ((value << 1) ^ (0x04C11DB7 if value & 0x80000000 else 0)) & 0xFFFFFFFF
        table.append(value)
    return table


def _ogg_checksum(data):
    checksum = 0
    table = _crc_table()
    for value in data:
        checksum = ((checksum << 8) & 0xFFFFFFFF) ^ table[((checksum >> 24) ^ value) & 0xFF]
    return checksum


def _load_ogg(filename):
    """Check framing, checksums and Vorbis headers without an external codec tool."""
    path = Path(filename) if filename else None
    if path is None or not path.is_file():
        raise ValueError(f"找不到音色样本：{filename or '未选择文件'}")
    if path.suffix.lower() != ".ogg":
        raise ValueError(f"音色样本必须为 .ogg 文件：{path.name}")
    data = path.read_bytes()
    offset, serial, sequence, packet = 0, None, 0, bytearray()
    headers, packet_count, ended = [], 0, False
    try:
        while offset < len(data):
            if ended or len(data) - offset < 27 or data[offset:offset + 4] != b"OggS":
                raise ValueError
            header = data[offset:offset + 27]
            if header[4] != 0 or header[5] & ~7:
                raise ValueError
            page_serial, page_sequence, expected_crc = struct.unpack_from("<III", header, 14)
            if serial is None:
                serial = page_serial
                if not header[5] & 2 or header[5] & 1:
                    raise ValueError
            if serial != page_serial or sequence != page_sequence:
                raise ValueError
            if bool(header[5] & 1) != bool(packet):
                raise ValueError
            sequence += 1
            count = header[26]
            segments = data[offset + 27:offset + 27 + count]
            size = 27 + count + sum(segments)
            if len(segments) != count or offset + size > len(data):
                raise ValueError
            page = bytearray(data[offset:offset + size])
            page[22:26] = b"\0" * 4
            if _ogg_checksum(page) != expected_crc:
                raise ValueError
            cursor = offset + 27 + count
            for length in segments:
                packet.extend(data[cursor:cursor + length])
                cursor += length
                if length < 255:
                    if packet_count < 3:
                        headers.append(bytes(packet))
                    packet_count += 1
                    packet.clear()
            offset += size
            ended = bool(header[5] & 4)
        if not ended or packet or packet_count < 4:
            raise ValueError
        if len(headers[0]) != 30 or headers[0][:7] != b"\x01vorbis":
            raise ValueError
        if headers[1][:7] != b"\x03vorbis" or headers[2][:7] != b"\x05vorbis":
            raise ValueError
        if struct.unpack_from("<I", headers[0], 7)[0] != 0 or not headers[0][29] & 1:
            raise ValueError
        channels, sample_rate = headers[0][11], struct.unpack_from("<I", headers[0], 12)[0]
        if not channels or not sample_rate:
            raise ValueError
    except (ValueError, IndexError, struct.error) as error:
        raise ValueError(f"样本不是完整有效的 OGG Vorbis 音频：{path.name}") from error
    if channels != 1:
        raise ValueError(f"空间音效需单声道 OGG Vorbis，请先转换为 mono：{path.name}")
    return data


def _version_string(value):
    value = getattr(value, "name", value)
    if not isinstance(value, str):
        raise ValueError("请指定目标 Minecraft 版本或资源包 pack_format。")
    return value.removeprefix("Version.").removeprefix("JE_").replace("_", ".")


def _json_bytes(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def resource_pack_format(minecraft_version):
    """Return the known resource pack format for a Version enum or string."""
    version = _version_string(minecraft_version)
    if version not in _PACK_FORMATS:
        raise ValueError(f"尚无 Minecraft {version} 的 NoteBetter 资源包格式；支持 1.16.5–1.21.5。")
    return _PACK_FORMATS[version]


def export_notebetter_pack(destination, config_or_list, *, pack_format=None, minecraft_version=None):
    """Write an atomic ZIP bundle containing a real mod config and resource pack.

    ``minecraft_version`` accepts an mcschematic Version or a version string.
    If omitted, a config's data_version is used, otherwise Minecraft 1.21.4.
    This ZIP is an installation bundle; its nested resourcepacks ZIP is the
    actual pack to enable in Minecraft, and the config is installed separately.
    """
    entries = validate_custom_instruments(config_or_list)
    if not entries:
        raise ValueError("请先添加至少一种自定义音色。")
    if minecraft_version is None and isinstance(config_or_list, Mapping):
        minecraft_version = config_or_list.get("data_version")
    version = _version_string(minecraft_version) if minecraft_version is not None else "1.21.4"
    if pack_format is None:
        pack_format = resource_pack_format(version)
    if type(pack_format) is not int or pack_format <= 0:
        raise ValueError("pack_format 必须是正整数。")
    samples = [(item, _load_ogg(item["sound_file"])) for item in entries]
    mappings, sounds = [], {}
    pack_buffer = io.BytesIO()
    with zipfile.ZipFile(pack_buffer, "w", compression=zipfile.ZIP_DEFLATED) as pack:
        pack.writestr("pack.mcmeta", _json_bytes({"pack": {
            "pack_format": pack_format,
            "description": "NBS2Save 自定义音色 / NoteBetter Fabric",
        }}))
        for item, sample in samples:
            namespace, sound_path = item["sound_id"].split(":", 1)
            sounds.setdefault(namespace, {})[sound_path] = {
                "sounds": [{"name": item["sound_id"], "stream": False, "attenuation_distance": 16}]
            }
            pack.writestr(f"assets/{namespace}/sounds/{sound_path}.ogg", sample)
            mappings.append({"block": item["base_block"], "sound": {
                "sound": item["sound_id"], "volume": 1.0,
                "pitch": math.pow(2.0, (45 - item["root_key"]) / 12.0),
            }})
        for namespace, events in sounds.items():
            pack.writestr(f"assets/{namespace}/sounds.json", _json_bytes(events))
    readme = _installation_readme(version, pack_format)
    destination = Path(destination)
    if destination.suffix.lower() != ".zip":
        destination = destination.with_suffix(".zip")
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(dir=destination.parent, prefix=".notebetter-", suffix=".tmp", delete=False) as file:
            temporary = Path(file.name)
        with zipfile.ZipFile(temporary, "w", compression=zipfile.ZIP_DEFLATED) as bundle:
            bundle.writestr(NOTEBETTER_CONFIG_PATH, _json_bytes({"mappings": mappings}))
            bundle.writestr(RESOURCE_PACK_PATH, pack_buffer.getvalue())
            bundle.writestr("README.txt", readme.encode("utf-8"))
        temporary.replace(destination)
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()
    return destination


def _installation_readme(version, pack_format):
    return f"""NBS2Save 自定义音色安装包 / NoteBetter Fabric
目标 Minecraft Java：{version}；资源包 pack_format：{pack_format}

1. 本 ZIP 是安装包。每位听众的客户端均须安装 Fabric 及兼容目标游戏版本的
   NoteBetter Fabric 和该版本所需依赖。请遵循模组发布页，勿跨版本强行安装。
   维护版 README 列出的分支下载：
   Minecraft 1.16.5–1.19.2: {NOTEBETTER_REPOSITORY}/releases/tag/1.0-1.18.2
   Minecraft 1.19.3–1.20.6: {NOTEBETTER_REPOSITORY}/releases/tag/1.0-1.19.4
   Minecraft 1.21+: {NOTEBETTER_REPOSITORY}/releases/tag/1.0-1.21
   上述为作者声明的版本范围；生成正确资源包格式不保证模组适用于全部补丁版本。
2. 关闭游戏，将 config/notebetterfabric.json 放入客户端游戏目录的 config。
   已有配置时请备份，并合并 mappings；不要为同一底座方块保留重复映射。
3. 将 resourcepacks/nbs2save-custom-instruments.zip 放入同一客户端的
   resourcepacks 文件夹，并在游戏内启用资源包，然后重新启动游戏。
   模组也提供 /notebetter reload，但命令源码要求权限等级 2。
4. 在相同目标游戏版本导入本程序生成的结构。NoteBetter 依据音符盒正下方的
   方块 ID 选择音色；该底座下的所有音符盒都会受到映射影响。
   音符盒上方须留空，并由正常红石线路触发。此安装包不会替你安装模组。

音高：root_key 是样本原始音高（NBS key，默认 45）。映射 pitch =
2^((45-root_key)/12)，再乘游戏 note 属性产生的原版音高倍率。
原结构导出的音域仍为 NBS key 33–57；超出音域时沿用程序原有 note=0 行为。
样本使用单声道 OGG Vorbis，才能在 Minecraft 里产生空间定位。
自定义映射 volume=1，默认声源距离16格；原版音符盒 volume=3，距离48格。

格式依据（chsbuffer/NoteBetter，客户端 Gson 配置）：
{NOTEBETTER_REPOSITORY}/blob/main/README.md
{NOTEBETTER_REPOSITORY}/blob/main/src/client/java/com/gmail/gorayan3838/notebetterfabric/client/NoteBetterFabricClient.java
{NOTEBETTER_REPOSITORY}/blob/main/src/client/java/com/gmail/gorayan3838/notebetterfabric/config/SoundConfig.java
{NOTEBETTER_REPOSITORY}/blob/main/src/client/java/com/gmail/gorayan3838/notebetterfabric/mixin/NoteBlockMixin.java
资源包版本依据：https://github.com/misode/mcmeta/blob/summary/versions/data.json
"""
