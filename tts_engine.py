"""Piper TTS 引擎封装。

负责：
- 扫描语音目录，发现可用的 Piper 语音模型（.onnx + .onnx.json）
- 按需加载模型并缓存（onnxruntime 会话开销较大）
- 将文本合成为 WAV 文件

语音目录（优先级从高到低）：
- /opt/piper-voices  镜像内置模型
- /app/voices        用户挂载卷，可用于追加自定义语音
"""

from __future__ import annotations

import json
import logging
import threading
import wave
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Union

logger = logging.getLogger(__name__)

# 默认语音搜索目录
DEFAULT_VOICE_DIRS: Sequence[str] = ("/opt/piper-voices", "/app/voices")

# 质量等级中文标签
QUALITY_LABELS = {"x_low": "极低", "low": "低", "medium": "中", "high": "高"}

# 排序权重：中文优先，其次英文
LANGUAGE_ORDER = {"zh": 0, "en": 1}


@dataclass
class VoiceInfo:
    """单个 Piper 语音的元信息。"""

    id: str
    name: str
    language: str           # 例如 zh_CN
    language_family: str    # 例如 zh
    language_name: str      # 例如 简体中文
    quality: str            # x_low / low / medium / high
    sample_rate: int
    num_speakers: int
    size_bytes: int
    model_path: str
    config_path: str

    @property
    def quality_label(self) -> str:
        return QUALITY_LABELS.get(self.quality, self.quality)

    @property
    def display_name(self) -> str:
        """用于前端下拉框展示的名称。"""
        return (
            f"{self.language_name} · {self.name}"
            f"（{self.quality_label}，{self.language}）"
        )

    def to_dict(self) -> dict:
        data = asdict(self)
        # 不向前端暴露服务器内部路径
        data.pop("model_path", None)
        data.pop("config_path", None)
        data["display_name"] = self.display_name
        data["quality_label"] = self.quality_label
        return data


def _read_config(config_path: Path) -> dict:
    try:
        return json.loads(config_path.read_text(encoding="utf-8"))
    except Exception as exc:  # 配置文件损坏时跳过该语音
        logger.warning("读取语音配置失败 %s: %s", config_path, exc)
        return {}


def _parse_voice_id(voice_id: str) -> tuple[str, str]:
    """从语音 ID 解析出名称与质量，如 zh_CN-huayan-medium -> (huayan, medium)。"""
    parts = voice_id.split("-")
    if len(parts) >= 3:
        return "-".join(parts[1:-1]), parts[-1]
    if len(parts) == 2:
        return parts[1], "medium"
    return voice_id, "medium"


def _build_voice_info(model_path: Path) -> Optional[VoiceInfo]:
    config_path = Path(str(model_path) + ".json")
    if not config_path.exists():
        logger.warning("语音模型缺少配置文件，已跳过：%s", model_path)
        return None

    config = _read_config(config_path)
    voice_id = model_path.stem
    name, quality = _parse_voice_id(voice_id)

    language = config.get("language") or {}
    lang_code = language.get("code") or voice_id.split("-")[0]
    lang_family = language.get("family") or lang_code.split("_")[0]
    lang_name = language.get("name_native") or language.get("name_english") or lang_code

    try:
        size_bytes = model_path.stat().st_size
    except OSError:
        size_bytes = 0

    return VoiceInfo(
        id=voice_id,
        name=name,
        language=lang_code,
        language_family=lang_family,
        language_name=lang_name,
        quality=quality,
        sample_rate=(config.get("audio") or {}).get("sample_rate", 22050),
        num_speakers=config.get("num_speakers", 1),
        size_bytes=size_bytes,
        model_path=str(model_path),
        config_path=str(config_path),
    )


def _sort_key(voice: VoiceInfo) -> tuple:
    quality_rank = {"high": 0, "medium": 1, "low": 2, "x_low": 3}
    return (
        LANGUAGE_ORDER.get(voice.language_family, 9),
        voice.language,
        quality_rank.get(voice.quality, 9),
        voice.id,
    )


class PiperEngine:
    """Piper 语音合成引擎（线程安全）。"""

    def __init__(self, voice_dirs: Optional[Sequence[Union[str, Path]]] = None):
        self.voice_dirs = tuple(
            Path(d) for d in (voice_dirs or DEFAULT_VOICE_DIRS)
        )
        self._voices: Dict[str, VoiceInfo] = {}
        self._models: Dict[str, object] = {}
        self._load_lock = threading.Lock()   # 保护模型加载与缓存
        self._synth_lock = threading.Lock()  # 串行合成，避免 CPU 争抢
        self.refresh()

    # ------------------------------------------------------------------
    # 语音发现
    # ------------------------------------------------------------------
    def refresh(self) -> List[VoiceInfo]:
        """重新扫描语音目录并刷新可用语音列表。"""
        found: Dict[str, VoiceInfo] = {}
        for directory in self.voice_dirs:
            if not directory.is_dir():
                logger.info("语音目录不存在，已忽略：%s", directory)
                continue
            for model_path in sorted(directory.glob("*.onnx")):
                voice_id = model_path.stem
                if voice_id in found:
                    # 先扫描到的目录优先级更高
                    logger.debug("语音 %s 已被更高优先级目录覆盖", voice_id)
                    continue
                info = _build_voice_info(model_path)
                if info:
                    found[voice_id] = info

        self._voices = found
        # 清理已不存在语音的模型缓存
        for stale in set(self._models) - set(found):
            self._models.pop(stale, None)

        voices = sorted(found.values(), key=_sort_key)
        logger.info("发现 %d 个 Piper 语音：%s", len(voices), [v.id for v in voices])
        return voices

    @property
    def voices(self) -> List[VoiceInfo]:
        if not self._voices:
            self.refresh()
        return sorted(self._voices.values(), key=_sort_key)

    def voice_ids(self) -> List[str]:
        return [v.id for v in self.voices]

    def get(self, voice_id: Optional[str]) -> Optional[VoiceInfo]:
        """按 ID 获取语音；未指定时返回默认语音（中文优先）。"""
        if not voice_id:
            voices = self.voices
            return voices[0] if voices else None
        if voice_id in self._voices:
            return self._voices[voice_id]
        # 容忍大小写差异
        lowered = str(voice_id).lower()
        for vid, info in self._voices.items():
            if vid.lower() == lowered:
                return info
        return None

    # ------------------------------------------------------------------
    # 模型加载与合成
    # ------------------------------------------------------------------
    def _load_model(self, info: VoiceInfo):
        with self._load_lock:
            model = self._models.get(info.id)
            if model is not None:
                return model

            from piper import PiperVoice  # 延迟导入，便于给出友好报错

            logger.info("加载 Piper 语音模型：%s", info.model_path)
            model = PiperVoice.load(info.model_path, config_path=info.config_path)
            self._models[info.id] = model
            return model

    def synthesize(
        self,
        text: str,
        out_path: Union[str, Path],
        voice_id: Optional[str] = None,
        speed: float = 1.0,
    ) -> VoiceInfo:
        """将文本合成为 WAV 文件，返回实际使用的语音信息。"""
        info = self.get(voice_id)
        if info is None:
            raise ValueError(f"语音不存在：{voice_id}")

        model = self._load_model(info)

        # speed > 1 更快 => length_scale 更小
        speed = max(0.5, min(2.0, float(speed or 1.0)))
        length_scale = 1.0 / speed

        out_path = Path(out_path)
        with self._synth_lock:
            with wave.open(str(out_path), "wb") as wav_file:
                model.synthesize(
                    text,
                    wav_file,
                    length_scale=length_scale,
                    sentence_silence=0.2,
                )

        logger.info(
            "合成完成：voice=%s, speed=%.2f, size=%d bytes",
            info.id,
            speed,
            out_path.stat().st_size if out_path.exists() else 0,
        )
        return info
