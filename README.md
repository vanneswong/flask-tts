# Flask Text-to-Speech (Piper) 应用

> 基于 Flask + [Piper](https://github.com/rhasspy/piper) 的**离线神经网络**文本转语音 Web 应用

当前版本：**v0.2.0**（引擎已由 pyttsx3 迁移至 Piper，旧实现见 `pyttsx3` 分支）

---

## 目录

- [项目概述](#项目概述)
- [为什么换用 Piper](#为什么换用-piper)
- [功能特性](#功能特性)
- [技术栈](#技术栈)
- [项目结构](#项目结构)
- [快速开始](#快速开始)
- [数据持久化](#数据持久化)
- [添加自定义语音](#添加自定义语音)
- [API 文档](#api-文档)
- [配置说明](#配置说明)
- [常见问题](#常见问题)

---

## 项目概述

这是一个离线文本转语音（TTS）服务，提供 Web 界面与 RESTful API。
音频由 **Piper**（基于 ONNX Runtime 的神经网络语音合成引擎）本地生成，
不依赖任何在线服务，音质远优于 espeak-ng 等共振峰合成器。

**核心优势**：

- ✅ **完全离线**：模型内置镜像，无需联网即可合成
- ✅ **音质自然**：神经网络 TTS（VITS 模型），非机械音
- ✅ **多架构**：同时提供 `linux/amd64` 与 `linux/arm64` 镜像
- ✅ **数据持久化**：通过 Docker 卷保留音频与自定义语音
- ✅ **双接口**：Web 界面 + REST API

---

## 为什么换用 Piper

| 对比项 | pyttsx3 (espeak-ng) | Piper |
|---|---|---|
| 合成方式 | 共振峰拼接，机械音 | VITS 神经网络 |
| 中文音质 | 生硬、断句差 | 自然，接近真人 |
| 音频格式 | WAV（曾误标 .mp3） | WAV（22050 Hz） |
| 依赖 | 系统 espeak-ng | 自带 espeak 音素数据，无需系统包 |
| 模型体积 | 极小 | 每语音约 60 MB |

> pyttsx3 的完整实现与文档保留在 `pyttsx3` 分支，可随时对照或回退。

---

## 功能特性

- 🎙️ **文本转语音**：中文 / 英文，支持 0.5x–2.0x 语速调节
- 🎧 **在线预览**：生成后立即播放，支持下载
- 📋 **历史列表**：右侧展示已生成的语音（文本、音色、语速、时间、大小）
- 🗂️ **多语音支持**：自动扫描语音目录，可按语言分组选择
- 💾 **持久化存储**：音频与自定义模型均支持卷挂载
- ❤️ **健康检查**：`/health` 供容器健康探针使用
- 🧹 **自动清理**：可选按时间清理过期音频

---

## 技术栈

| 层 | 技术 |
|---|---|
| Web 框架 | Flask 3.1.2 |
| TTS 引擎 | piper-tts 1.2.0（onnxruntime + piper-phonemize） |
| 运行环境 | Python 3.11（arm64 需 cp311 wheel） |
| 前端 | 原生 HTML/CSS/JS |
| 容器 | Docker / docker-compose |

> ⚠️ 使用 Python 3.11 而非 3.12：`piper-phonemize` 仅提供 cp311 的 aarch64 wheel。

---

## 项目结构

```
flask-tts/
├── app.py                      # Flask 应用（路由 / API）
├── tts_engine.py               # Piper 引擎封装（语音发现、缓存、合成）
├── templates/
│   └── index.html              # Web 界面
├── scripts/
│   └── download_voices.py      # 语音模型下载工具
├── voices/                     # 预置模型目录（构建时可选复用，不入库）
├── static/audio/               # 生成的音频（卷挂载点）
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── docs/Piper迁移说明.md
```

镜像内语音目录：

| 路径 | 用途 |
|---|---|
| `/opt/piper-voices` | 镜像内置模型（只读） |
| `/app/voices` | 用户挂载卷，用于追加自定义语音 |
| `/app/static/audio` | 生成的音频（卷挂载点） |

---

## 快速开始

### Docker（推荐）

```bash
# amd64 / arm64 自动匹配
docker run -d -p 5001:5001 --name flask-tts \
  -v flask-tts-audio:/app/static/audio \
  -v flask-tts-voices:/app/voices \
  --restart unless-stopped \
  ccr.ccs.tencentyun.com/mikewong/flask-tts:latest
```

或使用 compose：

```bash
docker compose up -d
```

访问 <http://localhost:5001>

### 本地运行

```bash
python3.11 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 下载语音模型到本地目录
python scripts/download_voices.py --out ./models zh_CN-huayan-medium en_US-lessac-medium

PIPER_VOICE_DIRS=./models AUDIO_DIR=./static/audio python app.py 5001
```

### 自行构建镜像

```bash
# 默认从 hf-mirror 下载模型
docker build -t flask-tts .

# 指定内置语音 / 更换下载源
docker build -t flask-tts \
  --build-arg PIPER_VOICES="zh_CN-huayan-medium en_US-lessac-medium en_GB-alba-medium" \
  --build-arg PIPER_VOICE_BASE=https://hf-mirror.com/rhasspy/piper-voices/resolve/v1.0.0 \
  .

# 多架构构建并推送
docker buildx build --platform linux/amd64,linux/arm64 \
  -t <registry>/flask-tts:latest --push .
```

> 若 `voices/` 目录中已存在同名 `.onnx` / `.onnx.json`，构建时直接复用，不联网下载。

---

## 数据持久化

| 挂载点 | 内容 | 说明 |
|---|---|---|
| `/app/static/audio` | 生成的 `.wav` 与同名 `.json` 元数据 | 不挂载则容器重建后丢失 |
| `/app/voices` | 自定义语音模型 | 不放也行，镜像已有内置模型 |

命名卷（推荐，权限自动处理）：

```bash
docker volume create flask-tts-audio
docker run -d -p 5001:5001 -v flask-tts-audio:/app/static/audio flask-tts
```

绑定挂载（需授权，容器以 uid 1000 运行）：

```bash
mkdir -p /srv/tts/audio && sudo chown -R 1000:1000 /srv/tts/audio
docker run -d -p 5001:5001 -v /srv/tts/audio:/app/static/audio flask-tts
```

---

## 添加自定义语音

Piper 语音可从 [rhasspy/piper-voices](https://huggingface.co/rhasspy/piper-voices) 获取，
每个语音需要 `.onnx` 与 `.onnx.json` 两个文件。

```bash
# 1. 查看可用语音
python3 scripts/download_voices.py --list --filter zh_,en_

# 2. 下载到宿主机的自定义语音目录
python3 scripts/download_voices.py --out /srv/tts/voices en_GB-alba-medium

# 3. 挂载该目录，服务启动时自动扫描
docker run -d -p 5001:5001 \
  -v /srv/tts/voices:/app/voices \
  flask-tts
```

重启容器后 `/api/voices` 即可看到新语音（中英文之外的语音同样支持）。

---

## API 文档

### `POST /api/speech` — 文本转语音

请求：

```json
{
  "text": "你好，世界",
  "voice": "zh_CN-huayan-medium",
  "speed": 1.0
}
```

| 字段 | 必填 | 说明 |
|---|---|---|
| `text` | ✅ | 待合成文本，最长 5000 字符 |
| `voice` | ❌ | 语音 ID，缺省用第一个（中文优先）；也兼容数字索引 |
| `speed` | ❌ | 语速 0.5–2.0，默认 1.0 |

响应：

```json
{
  "status": "success",
  "url": "/static/audio/api_1a2b3c4d.wav",
  "voice": "zh_CN-huayan-medium",
  "elapsed_ms": 780
}
```

错误示例：`400` 参数错误、`503` 未找到语音模型、`500` 合成失败。

### `GET /api/voices` — 可用语音列表

```json
{
  "status": "success",
  "engine": "piper",
  "voices": [
    {
      "id": "zh_CN-huayan-medium",
      "display_name": "简体中文 · huayan（中，zh_CN）",
      "language": "zh_CN",
      "language_family": "zh",
      "language_name": "简体中文",
      "quality": "medium",
      "quality_label": "中",
      "sample_rate": 22050,
      "num_speakers": 1,
      "size_bytes": 63201294
    }
  ]
}
```

### `GET /api/audio` — 已生成的语音列表

按创建时间倒序返回 `filename`、`url`、`size`、`text`、`voice`、`voice_name`、`speed`、`created_at`。

### `GET /health` — 健康检查

```json
{
  "status": "healthy",
  "engine": "piper",
  "version": "0.2.0",
  "available_voices": 2,
  "voices": ["zh_CN-huayan-medium", "en_US-lessac-medium"]
}
```

---

## 配置说明

通过环境变量调整行为：

| 变量 | 默认值 | 说明 |
|---|---|---|
| `PORT` | `5001` | 监听端口（也可用位置参数传入） |
| `AUDIO_DIR` | `./static/audio` | 音频输出目录 |
| `PIPER_VOICE_DIRS` | `/opt/piper-voices:/app/voices` | 语音搜索目录，冒号分隔，**靠前优先** |
| `MAX_TEXT_LENGTH` | `5000` | 单次合成最大字符数 |
| `FILE_MAX_AGE_HOURS` | `24` | 音频保留时长，`<=0` 表示不清理 |
| `LOG_LEVEL` | `INFO` | 日志级别 |

构建参数：

| 参数 | 默认值 | 说明 |
|---|---|---|
| `PIPER_VOICES` | `zh_CN-huayan-medium en_US-lessac-medium` | 内置语音列表（空格分隔） |
| `PIPER_VOICE_BASE` | `https://hf-mirror.com/.../v1.0.0` | 模型下载源 |
| `PIPER_INDEX_URL` / `PIP_INDEX_URL` | 阿里云 PyPI 镜像 | Python 依赖源 |

---

## 常见问题

**Q：容器启动后 `/api/voices` 返回 0 个语音？**
检查 `/opt/piper-voices` 是否有 `.onnx` 与 `.onnx.json` 成对文件；若自行构建时网络失败，可预先下载到 `voices/` 再构建。

**Q：中文合成出现英文读音？**
语音 ID 需与文本语言匹配：中文用 `zh_CN-*`，英文用 `en_*`。`voice` 传错语音会按该语音的语言规则发音。

**Q：第一次合成很慢？**
首次请求需加载 ONNX 模型（约 1–3 秒），之后缓存在内存中，通常在 1 秒内完成。

**Q：arm64 上能否运行？**
可以，镜像已提供 arm64 版本。注意基础镜像使用 Python 3.11（`piper-phonemize` 的 aarch64 轮子仅覆盖 cp311）。

**Q：如何回退到 pyttsx3？**
`git checkout pyttsx3`，或使用 v0.1.0 镜像标签。

---

## 许可与致谢

- Piper：<https://github.com/rhasspy/piper>（MIT）
- 语音模型：<https://huggingface.co/rhasspy/piper-voices>
