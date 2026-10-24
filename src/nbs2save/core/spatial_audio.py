"""Binaural reference listening from the actual exported note-block positions.

This is a headphone reference, not a Minecraft engine recording or a measured
HRTF. It models the game's 48-block note sound radius, head shadow and geometric
interaural delay. Listener coordinates identify the listener's ears. Minecraft
yaw is used: 0 faces south (+Z), 90 faces west (-X).
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from collections import OrderedDict
from io import BytesIO
import math
from pathlib import Path
import threading
from typing import Callable
import wave

import numpy as np

from .core import GroupProcessor, OutputFormatStrategy
from .constants import INSTRUMENT_BLOCK_MAPPING, INSTRUMENT_MAPPING
from .custom_instruments import validate_custom_instruments
from .mcfunction import McFunctionOutputStrategy
from .preview import build_preview


class RenderCancelled(Exception):
    """A listening render was superseded or explicitly stopped."""


@dataclass(frozen=True)
class SpatialEvent:
    tick: int
    time: float
    group_id: object
    position: tuple[int, int, int]
    instrument: int
    note_pitch: int
    blockstate: str
    gain: float = 1.0
    pan: float = 0.0
    left_delay: float = 0.0
    right_delay: float = 0.0
    sample_source: str = ""
    custom_instrument: int | None = None

    @property
    def pitch_key(self) -> int:
        return self.note_pitch + 33


@dataclass(frozen=True)
class SpatialAudio:
    pcm: bytes
    sample_rate: int
    events: tuple[SpatialEvent, ...]
    duration: float
    warnings: tuple[str, ...]
    timing: str

    @property
    def channels(self) -> int:
        return 2

    def wav_bytes(self) -> bytes:
        stream = BytesIO()
        with wave.open(stream, "wb") as writer:
            writer.setnchannels(2)
            writer.setsampwidth(2)
            writer.setframerate(self.sample_rate)
            writer.writeframes(self.pcm)
        return stream.getvalue()


def _check_cancel(cancel):
    if cancel is not None and cancel.is_set():
        raise RenderCancelled("试听已取消")


class _EventSink:
    def __init__(self, start, tempo):
        self.events = []
        self.group_id = None
        self.note = None
        self.start = start
        self.tempo = tempo

    def setBlock(self, position, blockstate):
        if blockstate.split("[", 1)[0].removeprefix("minecraft:") != "note_block":
            return
        props = dict(part.split("=", 1) for part in blockstate.partition("[")[2].rstrip("]").split(",") if "=" in part)
        state = blockstate if blockstate.startswith("minecraft:") else "minecraft:" + blockstate
        self.events.append(SpatialEvent(
            self.note.tick, (self.note.tick - self.start) / self.tempo,
            self.group_id, tuple(map(int, position)), self.note.instrument,
            int(props.get("note", "0")), state,
        ))

    def commands(self, processor, commands):
        for command in commands:
            parts = command.split()
            if parts and parts[0] == "setblock":
                self.setBlock(tuple(map(int, parts[1:4])), parts[4])


class _EventStrategy(OutputFormatStrategy):
    def __init__(self, delegate, sink):
        self.delegate, self.sink = delegate, sink
        if isinstance(delegate, McFunctionOutputStrategy):
            delegate._write_commands = sink.commands
        else:
            delegate.schem = sink

    def initialize(self, processor):
        pass

    def finalize(self, processor):
        pass

    def write_base_structures(self, processor, tick):
        pass

    def write_pan_platform(self, processor, tick, direction):
        pass

    def write_note(self, processor, note):
        _check_cancel(getattr(processor, "_cancel", None))
        self.sink.note = note
        self.delegate.write_note(processor, note)


class _EventProcessor(GroupProcessor):
    def __init__(self, notes, maximum, config, groups, sink, start, end, cancel):
        super().__init__(notes, maximum, config, groups)
        self._sink, self._start, self._end, self._cancel = sink, start, end, cancel
        self._ids = iter(groups)
        self.set_progress_callback(lambda _: _check_cancel(cancel))
        self.set_output_strategy(_EventStrategy(super()._pick_strategy_for_group("default"), sink))

    def _pick_strategy_for_group(self, mode):
        _check_cancel(self._cancel)
        self._sink.group_id = next(self._ids)
        return _EventStrategy(super()._pick_strategy_for_group(mode), self._sink)

    def _switch_strategy(self, strategy):
        self.output_strategy = strategy

    def process_group(self):
        _check_cancel(self._cancel)
        super().process_group(self._start, self._end)


def collect_spatial_events(song, groups, config=None, *, start_tick=0, end_tick=None,
                           timing="nbs", cancel=None) -> tuple[SpatialEvent, ...]:
    """Capture real strategies' note placements and remove overwritten boxes.

    NBS speed uses ``song.header.tempo``; redstone speed uses 10 ticks/second.
    Tick ranges are inclusive and event times start at the chosen range's zero.
    NBS velocity affects placement in volume mode, just as in export; generated
    note boxes have the same source volume and do not apply velocity twice.
    """
    if song is None:
        raise ValueError("请先加载 NBS 文件")
    if timing not in {"nbs", "redstone"}:
        raise ValueError("试听时序应为 nbs 或 redstone")
    tempo = float(song.header.tempo) if timing == "nbs" else 10.0
    if not math.isfinite(tempo) or tempo <= 0:
        raise ValueError("NBS 速度必须大于 0")
    maximum = max(int(song.header.song_length), max((note.tick for note in song.notes), default=0))
    start = int(start_tick)
    end = maximum if end_tick is None else min(maximum, int(end_tick))
    if start < 0 or end < start:
        raise ValueError("试听 tick 范围无效")
    _check_cancel(cancel)
    notes = [note for note in song.notes if start <= note.tick <= end]
    sink = _EventSink(start, tempo)
    processor = _EventProcessor(notes, maximum, dict(config or {}), dict(groups), sink, start, end, cancel)
    processor.process()
    _check_cancel(cancel)
    # A later group's clock/platform can replace an earlier group's note box.
    # Only boxes which survive the final exported geometry can make sound.
    final = build_preview(song.notes, groups, config, start_tick=start, end_tick=end, global_max_tick=maximum)
    _check_cancel(cancel)
    occupied = {block.position: block for block in final.blocks}
    events = [event for event in sink.events if (
        (block := occupied.get(event.position)) is not None
        and block.group_id == event.group_id and block.blockstate == event.blockstate
    )]
    # NoteBetter chooses a sound by the final support block, including vanilla
    # notes sharing a custom mapping's support. An NBS ID alone is insufficient.
    custom_by_block = {item["base_block"]: item["nbs_id"]
                       for item in validate_custom_instruments(config)}
    vanilla_by_block = {block: instrument for instrument, block in INSTRUMENT_BLOCK_MAPPING.items()}
    vanilla_by_name = {name: instrument for instrument, name in INSTRUMENT_MAPPING.items()}
    resolved = []
    for event in events:
        x, y, z = event.position
        # The exported layouts use the ordinary pitched instruments. These
        # require air above the box, including after another group's writes.
        if (x, y + 1, z) in occupied:
            continue
        support = occupied.get((x, y - 1, z))
        support_id = support.blockstate.split("[", 1)[0] if support is not None else "minecraft:air"
        props = dict(part.split("=", 1) for part in event.blockstate.partition("[")[2].rstrip("]").split(",") if "=" in part)
        fallback = vanilla_by_name.get(props.get("instrument", "harp"), 0)
        custom_id = custom_by_block.get(support_id)
        instrument = custom_id if custom_id is not None else vanilla_by_block.get(support_id, fallback)
        event = replace(event, instrument=instrument, custom_instrument=custom_id)
        resolved.append(event)
    return tuple(sorted(resolved, key=lambda event: event.tick))


def _resample(samples, source_rate, target_rate):
    if source_rate == target_rate:
        return samples.astype(np.float32, copy=False)
    size = max(1, round(len(samples) * target_rate / source_rate))
    return np.interp(np.arange(size) * source_rate / target_rate, np.arange(len(samples)), samples).astype(np.float32)


def decode_audio_sample(path, sample_rate=44100, *, cancel=None) -> np.ndarray:
    """Decode mono PCM from WAV or Qt's FFmpeg-supported formats (including OGG).

    The Qt decoder runs its own event loop in the rendering worker. The GUI
    event loop remains free; a QCoreApplication must exist for non-WAV decoding.
    """
    source = Path(path).expanduser()
    if not source.is_file():
        raise ValueError(f"音色文件不存在：{source}")
    _check_cancel(cancel)
    if source.suffix.lower() == ".wav":
        try:
            with wave.open(str(source), "rb") as reader:
                channels, width, rate = reader.getnchannels(), reader.getsampwidth(), reader.getframerate()
                raw = reader.readframes(min(reader.getnframes(), rate * 10))
            if width == 1:
                values = (np.frombuffer(raw, np.uint8).astype(np.float32) - 128) / 128
            elif width in (2, 4):
                values = np.frombuffer(raw, "<i2" if width == 2 else "<i4").astype(np.float32) / (2 ** (8 * width - 1))
            elif width == 3:
                b = np.frombuffer(raw, np.uint8).reshape(-1, 3).astype(np.int32)
                values = ((b[:, 0] | b[:, 1] << 8 | b[:, 2] << 16) << 8 >> 8).astype(np.float32) / 8388608
            else:
                raise ValueError("不支持的 WAV 采样精度")
            if not len(values):
                raise ValueError("音色文件没有可用音频")
            return _resample(values.reshape(-1, channels).mean(axis=1), rate, sample_rate)
        except wave.Error:
            # Float WAV and other encodings are handled by FFmpeg below.
            pass
    from PyQt6.QtCore import QCoreApplication, QEventLoop, QTimer, QUrl
    from PyQt6.QtMultimedia import QAudioDecoder, QAudioFormat

    if QCoreApplication.instance() is None:
        raise ValueError("OGG 解码需要 Qt 应用环境")
    decoder = QAudioDecoder()
    loop = QEventLoop()
    chunks, errors = [], []
    requested = QAudioFormat()
    requested.setSampleRate(sample_rate)
    requested.setChannelCount(1)
    requested.setSampleFormat(QAudioFormat.SampleFormat.Float)
    decoder.setAudioFormat(requested)

    def consume():
        try:
            while decoder.bufferAvailable():
                buffer = decoder.read()
                fmt = buffer.format()
                raw = buffer.data().asstring(buffer.byteCount())
                kind = fmt.sampleFormat()
                if kind == QAudioFormat.SampleFormat.Float:
                    values = np.frombuffer(raw, "<f4")
                elif kind == QAudioFormat.SampleFormat.Int16:
                    values = np.frombuffer(raw, "<i2").astype(np.float32) / 32768
                elif kind == QAudioFormat.SampleFormat.Int32:
                    values = np.frombuffer(raw, "<i4").astype(np.float32) / 2147483648
                elif kind == QAudioFormat.SampleFormat.UInt8:
                    values = (np.frombuffer(raw, np.uint8).astype(np.float32) - 128) / 128
                else:
                    raise ValueError("Qt 返回了不支持的音频采样格式")
                mono = values.reshape(-1, fmt.channelCount()).mean(axis=1)
                chunks.append(_resample(mono, fmt.sampleRate(), sample_rate))
                if sum(len(chunk) for chunk in chunks) >= sample_rate * 10:
                    loop.quit()
                    break
        except Exception as exc:
            errors.append(str(exc))
            loop.quit()

    def fail(*_):
        errors.append(decoder.errorString() or "Qt 无法解码音色")
        loop.quit()

    poll = QTimer()
    poll.setInterval(30)
    poll.timeout.connect(lambda: loop.quit() if cancel is not None and cancel.is_set() else None)
    timeout = QTimer()
    timeout.setSingleShot(True)
    timeout.timeout.connect(lambda: (errors.append("音色解码超时"), loop.quit()))
    decoder.bufferReady.connect(consume)
    decoder.finished.connect(loop.quit)
    decoder.error.connect(fail)
    decoder.setSource(QUrl.fromLocalFile(str(source.resolve())))
    poll.start()
    timeout.start(15000)
    # Start once the worker-local loop runs, including synchronous error paths.
    QTimer.singleShot(0, decoder.start)
    loop.exec()
    poll.stop()
    timeout.stop()
    decoder.stop()
    _check_cancel(cancel)
    if errors:
        raise ValueError(f"音色解码失败：{source.name}：{errors[0]}")
    if not chunks:
        raise ValueError(f"音色文件没有可用音频：{source.name}")
    return np.concatenate(chunks)[:sample_rate * 10].astype(np.float32)


_SOUND_NAMES = (
    "harp", "bass", "bd", "snare", "hat", "guitar", "flute", "bell",
    "icechime", "xylobone", "iron_xylophone", "cow_bell", "didgeridoo", "bit", "banjo", "pling",
)


def _sample_path(instrument, config, *, custom=False):
    for custom in config.get("custom_instruments", ()) if custom else ():
        if int(custom.get("nbs_id", -1)) == instrument:
            path = custom.get("sound_file", "")
            if not path:
                raise ValueError(f"自定义乐器 {instrument} 尚未设置本地音色文件")
            return path, int(custom.get("root_key", 45)), "自定义音色"
    samples = config.get("instrument_samples", {})
    name = _SOUND_NAMES[instrument] if 0 <= instrument < len(_SOUND_NAMES) else "harp"
    path = samples.get(str(instrument), samples.get(instrument, samples.get(name)))
    if path:
        return path, 45, "导入音色"
    root = config.get("minecraft_assets_dir", "")
    if root:
        for directory in ("assets/minecraft/sounds/note", "sounds/note", "note", ""):
            for suffix in (".ogg", ".wav"):
                candidate = Path(root) / directory / (name + suffix)
                if candidate.is_file():
                    return str(candidate), 45, "本地 Minecraft 音色"
    return None, 45, "合成参考音色（非原版）"


def _synthetic_sample(instrument, sample_rate):
    """Small distinct reference timbres; never represented as original assets."""
    duration = 1.2 if instrument in (7, 8, 10, 11, 15) else .75
    t = np.arange(round(duration * sample_rate), dtype=np.float64) / sample_rate
    octave = {1: -24, 6: 12, 7: 24, 8: 24, 9: 24, 11: 12, 12: -24}.get(instrument, 0)
    f = 440 * 2 ** ((45 + 21 + octave - 69) / 12)  # Minecraft note=12.
    phase = 2 * np.pi * f * t
    if instrument in (2, 3, 4):
        noise = np.random.default_rng(2100 + instrument).standard_normal(len(t))
        if instrument == 2:
            value = np.sin(2 * np.pi * (70 * t - 35 * t * t)) * np.exp(-16 * t)
        elif instrument == 3:
            value = (.65 * noise + .35 * np.sin(phase * .48)) * np.exp(-18 * t)
        else:
            value = (noise - np.roll(noise, 1)) * .4 * np.exp(-30 * t)
    elif instrument in (7, 8, 10, 11):
        value = sum(np.sin(phase * ratio) * gain * np.exp(-decay * t)
                    for ratio, gain, decay in [(1, .55, 3), (2.76, .28, 7), (5.4, .14, 12)])
    elif instrument == 13:
        value = np.sign(np.sin(phase)) * np.exp(-7 * t) * .5
    elif instrument in (6, 12):
        value = (np.sin(phase) + .15 * np.sin(phase * 2)) * np.exp(-5 * t)
    else:
        harmonic = .18 if instrument == 1 else .3
        value = (np.sin(phase) + harmonic * np.sin(phase * 2) + .12 * np.sin(phase * 3)) * np.exp(-7 * t)
    value *= np.minimum(1, t * 1000)  # Avoid a discontinuous attack.
    return (value * .24).astype(np.float32)


def _lowpass(samples, cutoff, sample_rate):
    if cutoff >= sample_rate * .45:
        return samples
    n = np.arange(31) - 15
    kernel = np.sinc(2 * cutoff / sample_rate * n) * np.hamming(31)
    kernel /= kernel.sum()
    return np.convolve(samples, kernel, mode="full")[15:15 + len(samples)].astype(np.float32)


def render_spatial_audio(song, groups, config=None, listener=(0, 65.62, -6), yaw=0, *,
                         start_tick=0, end_tick=None, sample_rate=44100, timing="nbs",
                         cancel: threading.Event | None = None,
                         progress: Callable[[int], None] | None = None) -> SpatialAudio:
    """Mix signed 16-bit stereo PCM from actual blocks and positional samples.

    Local OGG/WAV samples are resampled for the exported ``note`` pitch. Missing
    built-in assets use labelled reference synthesis. Missing/invalid explicitly
    configured custom samples fail clearly. Rendering is limited to 120 seconds
    and 10 seconds per sample to keep interactive memory/work bounded.
    """
    config = dict(config or {})
    sample_rate = int(sample_rate)
    if not 8000 <= sample_rate <= 96000:
        raise ValueError("试听采样率必须为 8000–96000 Hz")
    listener = np.asarray(listener, dtype=float)
    if listener.shape != (3,) or not np.isfinite(listener).all() or not math.isfinite(float(yaw)):
        raise ValueError("监听位置和朝向必须是有效数值")
    tempo = float(song.header.tempo) if song is not None and timing == "nbs" else 10.0
    maximum = max(int(song.header.song_length), max((n.tick for n in song.notes), default=0)) if song is not None else 0
    end = maximum if end_tick is None else min(int(end_tick), maximum)
    if end - start_tick > 4095:
        raise ValueError("一次试听最多 4096 tick，请缩小 tick 范围")
    if tempo > 0 and (end - start_tick + 1) / tempo > 120:
        raise ValueError("一次试听最多 120 秒，请缩小 tick 范围")
    events = collect_spatial_events(song, groups, config, start_tick=start_tick, end_tick=end, timing=timing, cancel=cancel)
    if not events:
        raise ValueError("所选范围内没有可试听的音符盒")
    if progress:
        progress(5)
    angle = math.radians(float(yaw))
    right = np.array((-math.cos(angle), 0, -math.sin(angle)))
    forward = np.array((-math.sin(angle), 0, math.cos(angle)))
    source_cache, pitched_cache = OrderedDict(), OrderedDict()
    source_info, prepared, warnings = {}, [], set()
    duration = (end - start_tick + 1) / tempo

    def cache_audio(cache, key, samples, limit):
        # Limit waveform caches independently of polyphony and instrument count.
        while cache and sum(value.nbytes for value in cache.values()) + samples.nbytes > limit:
            cache.popitem(last=False)
        if samples.nbytes <= limit:
            cache[key] = samples
        return samples

    def source_audio(source_key):
        if source_key in source_cache:
            source_cache.move_to_end(source_key)
            return source_cache[source_key]
        instrument, is_custom = source_key
        if source_key in source_info:
            path, root, label, _ = source_info[source_key]
        else:
            path, root, label = _sample_path(instrument, config, custom=is_custom)
            if path:
                label += "：" + Path(path).name
            else:
                warnings.add("缺少部分本地音色，使用合成参考音色（非 Minecraft 原版）")
        samples = decode_audio_sample(path, sample_rate, cancel=cancel) if path else _synthetic_sample(instrument, sample_rate)
        if len(samples) == 0 or not np.isfinite(samples).all():
            raise ValueError(f"乐器 {instrument} 的音色为空或包含无效采样")
        source_info[source_key] = (path, root, label, len(samples))
        return cache_audio(source_cache, source_key, samples, 64 * 1024 * 1024)

    for index, event in enumerate(events):
        _check_cancel(cancel)
        source_key = (event.instrument, event.custom_instrument is not None)
        if source_key not in source_info:
            source_audio(source_key)
        _, root, label, source_length = source_info[source_key]
        rate = 2 ** ((event.pitch_key - root) / 12)
        if not math.isfinite(rate) or rate <= 0:
            raise ValueError("音色基准音高无效")
        length = max(1, math.ceil(source_length / rate))
        if event.time + length / sample_rate > 140:
            raise ValueError("音色变调后的尾音超过 140 秒，请使用较短样本或调整基准音高")
        relative = np.asarray(event.position, dtype=float) + .5 - listener
        distance = float(np.linalg.norm(relative))
        radius = 16.0 if event.custom_instrument is not None else 48.0
        gain = max(0.0, 1 - distance / radius)
        pan = float(np.clip(np.dot(relative, right) / max(distance, .001), -1, 1))
        back = max(0, -float(np.dot(relative, forward)) / max(distance, .001))
        ear_distances = [np.linalg.norm(relative + right * .09), np.linalg.norm(relative - right * .09)]
        delays = [(float(d) - min(ear_distances)) / 343.0 for d in ear_distances]
        gains = (math.cos((pan * .85 + 1) * math.pi / 4), math.sin((pan * .85 + 1) * math.pi / 4))
        cutoffs = []
        for channel in range(2):
            far = max(0, pan if channel == 0 else -pan)
            cutoff = max(1400, sample_rate * .47 / (1 + far * 8 + back * 3))
            cutoffs.append(cutoff)
        enriched = replace(event, gain=gain, pan=pan, left_delay=delays[0], right_delay=delays[1], sample_source=label)
        prepared.append((enriched, source_key, rate, length, gains, cutoffs))
        duration = max(duration, event.time + length / sample_rate + max(delays))
        if progress and index % max(1, len(events) // 50) == 0:
            progress(5 + int(30 * (index + 1) / len(events)))
    if duration > 140:
        raise ValueError("试听包含过长的音色尾音，请缩小范围")
    mixed = np.zeros((math.ceil(duration * sample_rate) + 1, 2), dtype=np.float32)
    for index, (event, source_key, rate, length, gains, cutoffs) in enumerate(prepared):
        _check_cancel(cancel)
        if event.gain == 0:
            continue
        cache_key = (source_key, event.pitch_key)
        if cache_key in pitched_cache:
            pitched_cache.move_to_end(cache_key)
            sample = pitched_cache[cache_key]
        else:
            source = source_audio(source_key)
            sample = np.interp(np.arange(length) * rate, np.arange(len(source)), source, right=0).astype(np.float32)
            cache_audio(pitched_cache, cache_key, sample, 32 * 1024 * 1024)
        for channel, delay in enumerate((event.left_delay, event.right_delay)):
            start = round((event.time + delay) * sample_rate)
            # Filter, mix, then discard each channel. Do not retain two full
            # waveforms per note: dense songs otherwise grow with polyphony.
            filtered = _lowpass(sample, cutoffs[channel], sample_rate)
            mixed[start:start + len(sample), channel] += filtered * event.gain * gains[channel]
        if progress and index % max(1, len(events) // 50) == 0:
            progress(35 + int(60 * (index + 1) / len(events)))
    peak = float(np.max(np.abs(mixed)))
    if peak > .98:
        mixed *= .98 / peak
        warnings.add("重叠声源峰值已统一降低以避免削波")
    if all(event.gain == 0 for event, *_ in prepared):
        warnings.add("全部音符盒都在听觉范围之外（原版 48 格、自定义 16 格）；请移动监听位置")
    _check_cancel(cancel)
    if progress:
        progress(100)
    return SpatialAudio((np.clip(mixed, -1, 1) * 32767).astype("<i2").tobytes(), sample_rate,
                        tuple(event for event, *_ in prepared), len(mixed) / sample_rate,
                        tuple(sorted(warnings)), timing)
