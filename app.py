"""Flask 文本转语音应用（Piper 引擎）。"""

import json
import logging
import os
import time
import uuid
from pathlib import Path

from flask import Flask, jsonify, render_template, request

from tts_engine import PiperEngine

# ---------------------------------------------------------------------------
# 基础配置
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent

logging.basicConfig(
    level=os.environ.get("LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# 应用版本号
APP_VERSION = "0.2.0"

# 最大文本长度限制
MAX_TEXT_LENGTH = int(os.environ.get("MAX_TEXT_LENGTH", "5000"))

# 文件保留时长（小时），<=0 表示不自动清理
FILE_MAX_AGE_HOURS = float(os.environ.get("FILE_MAX_AGE_HOURS", "24"))

# 音频输出目录
AUDIO_DIR = Path(os.environ.get("AUDIO_DIR", BASE_DIR / "static" / "audio"))

# 语音模型目录（冒号分隔，优先级从高到低）
VOICE_DIRS = [
    d for d in os.environ.get(
        "PIPER_VOICE_DIRS", "/opt/piper-voices:/app/voices"
    ).split(":") if d
]

app = Flask(__name__, static_url_path="/static")
app.config["UPLOAD_FOLDER"] = str(AUDIO_DIR)
app.config["MAX_CONTENT_LENGTH"] = 1024 * 1024  # 请求体上限 1MB

AUDIO_DIR.mkdir(parents=True, exist_ok=True)

# 初始化 Piper 引擎（启动时扫描语音目录）
engine = PiperEngine(VOICE_DIRS)


# ---------------------------------------------------------------------------
# 工具函数
# ---------------------------------------------------------------------------
def cleanup_old_files(max_age_hours: float = FILE_MAX_AGE_HOURS) -> int:
    """清理超过指定时长的音频文件及其元数据。"""
    if max_age_hours <= 0 or not AUDIO_DIR.exists():
        return 0

    cutoff = time.time() - max_age_hours * 3600
    cleaned = 0
    for file in AUDIO_DIR.glob("*.wav"):
        try:
            if file.stat().st_mtime >= cutoff:
                continue
            file.unlink()
            meta = file.with_suffix(".json")
            if meta.exists():
                meta.unlink()
            cleaned += 1
        except OSError as exc:
            logger.warning("清理文件失败 %s: %s", file, exc)

    if cleaned:
        logger.info("已清理 %d 个过期语音文件", cleaned)
    return cleaned


def _resolve_voice(raw):
    """解析前端传入的 voice 参数。

    支持两种形式：
    - 语音 ID 字符串，如 "zh_CN-huayan-medium"（推荐）
    - 数字索引，如 "0"（兼容旧版前端）
    """
    if raw is None or raw == "":
        return None

    voices = engine.voices
    if isinstance(raw, bool):
        return None

    text = str(raw).strip()
    # 先按 ID 精确匹配
    if engine.get(text) is not None:
        return text

    # 再按索引匹配
    try:
        idx = int(text)
    except (TypeError, ValueError):
        return text  # 交给引擎报「语音不存在」
    if 0 <= idx < len(voices):
        return voices[idx].id
    return text


def _audio_meta_path(filename: str) -> Path:
    return AUDIO_DIR / f"{Path(filename).stem}.json"


# ---------------------------------------------------------------------------
# 路由
# ---------------------------------------------------------------------------
@app.route("/api/speech", methods=["POST"])
def api_speech():
    """文本转语音。"""
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"status": "error", "error": "请求体不能为空"}), 400

    text = (data.get("text") or "").strip()
    if not text:
        return jsonify({"status": "error", "error": "文本内容不能为空"}), 400

    if len(text) > MAX_TEXT_LENGTH:
        return jsonify({
            "status": "error",
            "error": f"文本长度不能超过 {MAX_TEXT_LENGTH} 字符",
        }), 400

    if not engine.voices:
        return jsonify({
            "status": "error",
            "error": "未找到任何 Piper 语音模型，请检查语音目录",
        }), 503

    voice_id = _resolve_voice(data.get("voice"))
    voice_info = engine.get(voice_id)
    if voice_info is None:
        return jsonify({
            "status": "error",
            "error": f"语音不存在：{data.get('voice')}",
        }), 400

    try:
        speed = float(data.get("speed") or 1.0)
    except (TypeError, ValueError):
        speed = 1.0

    filename = f"api_{uuid.uuid4().hex[:8]}.wav"
    filepath = AUDIO_DIR / filename

    logger.info(
        "语音请求：chars=%d, voice=%s, speed=%.2f, ip=%s",
        len(text), voice_info.id, speed, request.remote_addr,
    )

    started = time.time()
    try:
        engine.synthesize(text, filepath, voice_id=voice_info.id, speed=speed)
    except Exception as exc:  # 合成失败统一返回 500
        logger.exception("语音合成失败")
        if filepath.exists():
            filepath.unlink(missing_ok=True)
        return jsonify({
            "status": "error",
            "error": f"语音合成失败：{exc}",
        }), 500

    elapsed_ms = int((time.time() - started) * 1000)

    # 写入元数据，供历史列表展示
    try:
        meta = {
            "text": text,
            "voice": voice_info.id,
            "voice_name": voice_info.display_name,
            "language": voice_info.language,
            "speed": speed,
            "duration_ms": elapsed_ms,
            "created_at": time.time(),
        }
        _audio_meta_path(filename).write_text(
            json.dumps(meta, ensure_ascii=False), encoding="utf-8"
        )
    except OSError as exc:
        logger.warning("写入元数据失败：%s", exc)

    logger.info("合成成功：%s（%d ms）", filename, elapsed_ms)
    return jsonify({
        "status": "success",
        "url": f"/static/audio/{filename}",
        "voice": voice_info.id,
        "elapsed_ms": elapsed_ms,
    })


@app.route("/api/voices")
def api_voices():
    """返回可用语音列表。"""
    return jsonify({
        "status": "success",
        "engine": "piper",
        "voices": [v.to_dict() for v in engine.voices],
    })


@app.route("/api/audio")
def api_audio_list():
    """返回已生成的语音列表（最新的在前）。"""
    items = []
    for file in AUDIO_DIR.glob("*.wav"):
        meta = {}
        meta_file = _audio_meta_path(file.name)
        if meta_file.exists():
            try:
                meta = json.loads(meta_file.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                meta = {}
        try:
            stat = file.stat()
        except OSError:
            continue

        items.append({
            "filename": file.name,
            "url": f"/static/audio/{file.name}",
            "size": stat.st_size,
            "mtime": stat.st_mtime,
            "text": meta.get("text", ""),
            "voice": meta.get("voice", ""),
            "voice_name": meta.get("voice_name", meta.get("voice", "")),
            "speed": meta.get("speed", 1.0),
            "created_at": meta.get("created_at", stat.st_mtime),
        })

    items.sort(key=lambda x: x.get("created_at", 0), reverse=True)
    return jsonify({"status": "success", "items": items})


@app.route("/health")
def health():
    """健康检查接口。"""
    voices = engine.voices
    return jsonify({
        "status": "healthy",
        "engine": "piper",
        "version": APP_VERSION,
        "available_voices": len(voices),
        "voices": engine.voice_ids(),
    })


@app.route("/")
def index():
    """主页。"""
    # 按语言预分组（保持引擎的排序：中文优先）
    groups: dict[str, list] = {}
    for voice in engine.voices:
        groups.setdefault(voice.language_name, []).append(voice)

    return render_template(
        "index.html",
        voice_groups=list(groups.items()),
        voice_total=len(engine.voices),
        version=APP_VERSION,
        max_text_length=MAX_TEXT_LENGTH,
    )


# 应用启动时清理过期文件
cleanup_old_files()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Flask Text-to-Speech (Piper)")
    parser.add_argument(
        "port", type=int, nargs="?", default=int(os.environ.get("PORT", "5001")),
        help="监听端口（默认 5001）",
    )
    args = parser.parse_args()

    logger.info("启动 Piper TTS 服务，端口 %d，可用语音 %d 个",
                args.port, len(engine.voices))
    app.run(host="0.0.0.0", port=args.port)
