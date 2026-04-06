# Flask Text-to-Speech (pyttsx3) 应用

> 基于 Flask 和 pyttsx3 的离线文本转语音 Web 应用

## 📋 目录

- [项目概述](#项目概述)
- [功能特性](#功能特性)
- [技术栈](#技术栈)
- [项目结构](#项目结构)
- [快速开始](#快速开始)
- [API 文档](#api-文档)
- [Docker 部署](#docker-部署)
- [配置说明](#配置说明)
- [已知问题](#已知问题)
- [优化建议](#优化建议)
  - [总览表](#优化建议总览表)
  - [P0 - 必须修复](#p0---必须修复)
  - [P1 - 强烈建议](#p1---强烈建议)
  - [P2 - 建议优化](#p2---建议优化)
  - [完整优化代码参考](#完整优化代码参考)
- [常见问题](#常见问题)

---

## 项目概述

这是一个基于 Flask 框架和 pyttsx3 库的**离线文本转语音**（TTS）Web 应用。它提供了一个简洁的 Web 界面和 RESTful API，允许用户将文本转换为语音文件（MP3 格式），支持在线播放和下载。

**核心优势**：
- ✅ **离线运行**：无需网络连接，本地即可完成语音合成
- ✅ **多语言支持**：依赖系统语音引擎，支持中文、英文等多种语言
- ✅ **轻量部署**：依赖少，支持 Docker 容器化部署
- ✅ **双接口**：同时提供 Web 界面和 API 接口

---

## 功能特性

### 当前功能

| 功能 | 描述 |
|------|------|
| **API 接口** | `POST /api/speech` - 接收文本，返回语音文件 URL |
| **Web 界面** | 文本输入、音色选择、语音播放、文件下载 |
| **文件管理** | 自动保存生成的 MP3 文件到 `static/mp3/` 目录 |
| **响应式设计** | 基于 Tailwind CSS，自适应电脑和手机浏览器 |

---

## 技术栈

| 层级 | 技术 | 版本 |
|------|------|------|
| **后端框架** | Flask | 3.1.2 |
| **TTS 引擎** | pyttsx3 | 2.99 |
| **前端样式** | Tailwind CSS | CDN |
| **Python** | Python | 3.12+ |
| **系统依赖 (Linux)** | espeak, libespeak-dev | - |
| **容器化** | Docker | python:3.12-slim |

---

## 项目结构

```
flask-text2speech-pyttsx3/
├── app.py                      # Flask 主应用
├── requirements.txt            # Python 依赖
├── Dockerfile                  # Docker 构建文件
├── QWEN.md                     # 项目上下文文档
├── README.md                   # 本文件
├── static/
│   └── mp3/                    # 生成的语音文件存储目录
│       ├── api_1744386219.mp3
│       └── ...
└── templates/
    └── index.html              # Web 界面模板
```

### 关键文件说明

| 文件 | 说明 |
|------|------|
| `app.py` | Flask 应用主文件，定义 API 路由和页面路由 |
| `requirements.txt` | Python 依赖清单 |
| `Dockerfile` | 容器化部署配置 |
| `templates/index.html` | 响应式 Web 界面 |
| `static/mp3/` | 语音文件存储目录 |

---

## 快速开始

### 环境要求

- Python 3.12+
- Windows / macOS / Linux

### 安装依赖

```bash
pip install -r requirements.txt
```

### 系统依赖（仅 Linux）

```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install -y espeak libespeak-dev

# CentOS/RHEL
sudo yum install -y espeak espeak-devel
```

> **Windows/macOS 用户无需额外安装**，pyttsx3 会使用系统内置的语音引擎（SAPI5 / NSSpeechSynthesizer）。

### 启动应用

```bash
python app.py
```

访问 `http://localhost:5001` 即可使用 Web 界面。

---

## API 文档

### POST /api/speech

将文本转换为语音文件，返回文件访问 URL。

#### 请求

**Headers**:
```
Content-Type: application/json
```

**Body**:
```json
{
  "text": "你好，这是一个测试"
}
```

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `text` | string | ✅ 是 | 要转换的文本内容 |

#### 响应

**200 OK**:
```json
{
  "status": "success",
  "url": "/static/mp3/api_1775454895.mp3"
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `status` | string | 请求状态，固定返回 `"success"` |
| `url` | string | 生成的语音文件访问路径 |

#### 使用示例

```bash
# curl 请求
curl -X POST http://localhost:5001/api/speech \
  -H "Content-Type: application/json" \
  -d '{"text":"你好世界"}'

# Python 请求示例
import requests
response = requests.post(
    "http://localhost:5001/api/speech",
    json={"text": "你好世界"}
)
print(response.json())
```

---

## Docker 部署

### 构建镜像

```bash
docker build -t flask-tts .
```

### 运行容器

```bash
docker run -d -p 5001:5001 --name tts flask-tts
```

### 持久化语音文件

```bash
docker run -d \
  -p 5001:5001 \
  -v $(pwd)/static/mp3:/app/static/mp3 \
  --name tts \
  flask-tts
```

### Docker Compose（推荐）

创建 `docker-compose.yml`:
```yaml
version: '3.8'

services:
  tts:
    build: .
    ports:
      - "5001:5001"
    volumes:
      - ./static/mp3:/app/static/mp3
    restart: unless-stopped
```

启动：
```bash
docker-compose up -d
```

### Dockerfile 特性

| 特性 | 说明 |
|------|------|
| **基础镜像** | `python:3.12-slim` (轻量、安全) |
| **非 root 用户** | 使用 `appuser` 运行，增强安全性 |
| **健康检查** | 内置 `HEALTHCHECK`，每 30 秒检测 `/health` 接口 |
| **依赖清理** | `apt-get` 安装后清理缓存，减小镜像体积 |

---

## 配置说明

### 当前可配置项

| 配置 | 位置 | 默认值 | 说明 |
|------|------|--------|------|
| **端口** | `app.py` 第 44 行 | `5001` | Flask 服务监听端口 |
| **存储目录** | `app.py` 第 8 行 | `static/mp3` | 语音文件存储路径 |
| **语速** | 可通过 `engine.setProperty('rate', value)` 调整 | 系统默认 | 语音播放速度 |
| **音量** | 可通过 `engine.setProperty('volume', value)` 调整 | 1.0 (最大) | 音量大小 (0.0 ~ 1.0) |

### 修改语速和音量示例

在 `app.py` 中 `engine = pyttsx3.init()` 后添加：

```python
# 设置语速 (默认约 200)
engine.setProperty('rate', 180)

# 设置音量 (0.0 ~ 1.0)
engine.setProperty('volume', 1.0)
```

---

## 已知问题

### 1. 音色选择功能未实现

**问题描述**：前端页面有声区选择控件，并会将 `voice` 参数传递给后端，但后端 API **未处理该参数**，始终使用默认语音。

**影响**：用户无法通过界面切换不同音色。

**修复方案**：见 [优化建议 #1](#1-实现音色选择功能)

---

### 2. 并发请求可能导致阻塞

**问题描述**：`pyttsx3` 的 `engine.runAndWait()` 是**阻塞调用**，同一时刻只能处理一个请求。多个并发请求会导致排队等待。

**影响**：高并发场景下响应时间增加。

**修复方案**：见 [优化建议 #3](#3-使用线程锁解决并发问题)

---

### 3. 语音文件无自动清理机制

**问题描述**：生成的 MP3 文件会永久保存在 `static/mp3/` 目录，长期运行会占用大量磁盘空间。

**影响**：磁盘空间持续增长，需手动清理。

**修复方案**：见 [优化建议 #4](#4-添加文件自动清理机制)

---

### 4. 时间戳命名可能导致文件覆盖

**问题描述**：文件名使用秒级时间戳 (`int(time.time())`)，同一秒内的多个请求会产生相同文件名，导致文件被覆盖。

**影响**：高并发场景下文件丢失。

**修复方案**：见 [优化建议 #5](#5-改进文件命名规则)

---

## 优化建议

### 优化建议总览表

| 优先级 | # | 建议项 | 复杂度 | 影响范围 |
|:------:|:-:|--------|:------:|----------|
| 🔴 P0 | 1 | 实现音色选择功能 | 低 | 核心功能 |
| 🔴 P0 | 2 | 添加输入验证和错误处理 | 低 | 安全性和稳定性 |
| 🟡 P1 | 3 | 使用线程锁解决并发问题 | 低 | 多用户场景 |
| 🟡 P1 | 4 | 添加文件自动清理机制 | 中 | 运维成本 |
| 🟡 P1 | 5 | 改进文件命名规则 | 低 | 数据完整性 |
| 🟢 P2 | 6 | 添加请求限流 | 中 | 安全防护 |
| 🟢 P2 | 7 | 支持语速、音量等自定义参数 | 中 | 用户体验 |
| 🟢 P2 | 8 | 添加健康检查接口 | 低 | 运维监控 |
| 🟢 P2 | 9 | 前端体验优化（加载状态、错误提示） | 低 | 用户体验 |
| 🟢 P2 | 10 | 日志记录 | 低 | 问题排查 |

---

### P0 - 必须修复

#### 1. 实现音色选择功能

| 维度 | 说明 |
|------|------|
| **问题** | 前端传递了 `voice` 参数（音色索引），但后端完全忽略，始终使用默认语音 |
| **影响** | 页面上的音色选择下拉框形同虚设，用户无法切换音色 |
| **复杂度** | 低 — 只需在 `api_speech` 函数中添加 4-5 行代码 |

**修复方案**：

在 `api_speech` 函数中获取并设置音色：

```python
@app.route('/api/speech', methods=['POST'])
def api_speech():
    data = request.get_json()
    text = data.get('text', '')
    voice_id = data.get('voice')  # 新增：获取前端传来的音色索引

    # ... 文件命名逻辑 ...

    # 新增：根据音色索引设置语音
    if voice_id is not None:
        voices = engine.getProperty('voices')
        try:
            voice_idx = int(voice_id)
            if 0 <= voice_idx < len(voices):
                engine.setProperty('voice', voices[voice_idx].id)
        except (ValueError, TypeError):
            pass  # 音色参数无效时使用默认语音

    engine.save_to_file(text, filepath)
    # ... 后续逻辑 ...
```

---

#### 2. 添加输入验证和错误处理

| 维度 | 说明 |
|------|------|
| **问题** | 未检查空请求体、空文本、超长文本，可能导致异常或资源滥用 |
| **影响** | 恶意用户可发送超大文本导致服务器资源耗尽 |
| **复杂度** | 低 — 只需在函数开头添加前置检查 |

**修复方案**：

```python
@app.route('/api/speech', methods=['POST'])
def api_speech():
    data = request.get_json()
    if not data:
        return jsonify({'error': '请求体不能为空', 'status': 'error'}), 400

    text = data.get('text', '').strip()
    if not text:
        return jsonify({'error': '文本内容不能为空', 'status': 'error'}), 400

    MAX_TEXT_LENGTH = 5000
    if len(text) > MAX_TEXT_LENGTH:
        return jsonify({
            'error': f'文本长度不能超过 {MAX_TEXT_LENGTH} 字符',
            'status': 'error'
        }), 400

    # ... 继续处理 ...
```

**统一错误响应格式**：

```json
{
  "status": "error",
  "error": "文本内容不能为空"
}
```

---

### P1 - 强烈建议

#### 3. 使用线程锁解决并发问题

| 维度 | 说明 |
|------|------|
| **问题** | `pyttsx3` 的 `engine` 对象不是线程安全的，多个并发请求同时调用 `runAndWait()` 会抛出 `RuntimeError` |
| **影响** | 多用户同时使用时语音生成失败 |
| **复杂度** | 低 — 只需添加一个全局锁 |

**修复方案**：

```python
import threading

# 在 app.py 顶部，engine 初始化之后添加
engine_lock = threading.Lock()

@app.route('/api/speech', methods=['POST'])
def api_speech():
    # ... 前置验证 ...

    # 使用线程锁保护引擎调用
    with engine_lock:
        engine.save_to_file(text, filepath)
        try:
            engine.runAndWait()
        except RuntimeError as e:
            if 'run loop already started' in str(e):
                try:
                    engine.endLoop()
                    engine.runAndWait()
                except Exception:
                    return jsonify({
                        'status': 'error',
                        'error': '语音生成失败'
                    }), 500
            else:
                return jsonify({
                    'status': 'error',
                    'error': '语音生成失败'
                }), 500

    # ... 返回成功 ...
```

---

#### 4. 添加文件自动清理机制

| 维度 | 说明 |
|------|------|
| **问题** | 生成的 MP3 文件永久堆积在 `static/mp3/` 目录 |
| **影响** | 长期运行占用大量磁盘空间 |
| **复杂度** | 中 — 可选择简单清理或定时任务方案 |

**方案 A — 启动时清理（推荐，最简单）**：

```python
import time
from pathlib import Path

def cleanup_old_files(max_age_hours=24):
    """清理超过指定小时的旧文件"""
    folder = Path(app.config['UPLOAD_FOLDER'])
    if not folder.exists():
        return
    
    now = time.time()
    cutoff = now - (max_age_hours * 3600)
    cleaned = 0
    
    for file in folder.glob('*.mp3'):
        if file.stat().st_mtime < cutoff:
            file.unlink()
            cleaned += 1
    
    if cleaned > 0:
        print(f"已清理 {cleaned} 个过期语音文件")

# 在应用启动时调用（清理 24 小时前的文件）
cleanup_old_files(max_age_hours=24)
```

**方案 B — 定时任务（适合长期运行的服务）**：

需要额外依赖：`pip install APScheduler`

```python
from apscheduler.schedulers.background import BackgroundScheduler

scheduler = BackgroundScheduler()
scheduler.add_job(cleanup_old_files, 'interval', hours=1, args=[24])
scheduler.start()

# 在应用关闭时停止调度器
import atexit
atexit.register(lambda: scheduler.shutdown())
```

---

#### 5. 改进文件命名规则

| 维度 | 说明 |
|------|------|
| **问题** | 秒级时间戳在同一秒内的多个请求会产生文件名冲突 |
| **影响** | 高并发场景下文件被覆盖丢失 |
| **复杂度** | 低 — 只需修改文件名生成逻辑 |

**方案对比**：

| 方案 | 示例 | 优点 | 缺点 |
|------|------|------|------|
| **UUID（推荐）** | `api_a3f8b2c1.mp3` | 几乎零冲突 | 文件名不体现时间 |
| 毫秒时间戳 | `api_1775454895123.mp3` | 体现时间 | 极端并发仍可能冲突 |
| 时间戳 + 随机数 | `api_1775454895_7834.mp3` | 可读性好 | 稍长 |

**推荐实现（UUID 方案）**：

```python
import uuid

@app.route('/api/speech', methods=['POST'])
def api_speech():
    # ... 前置逻辑 ...
    
    # 使用 UUID 生成唯一文件名
    filename = f"api_{uuid.uuid4().hex[:8]}.mp3"
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    
    # ... 语音生成 ...
```

---

### P2 - 建议优化

#### 6. 添加请求限流

| 维度 | 说明 |
|------|------|
| **目的** | 防止恶意用户频繁调用 API 耗尽服务器资源 |
| **复杂度** | 中 — 需要额外依赖 |

**步骤 1**：添加依赖到 `requirements.txt`

```
Flask-Limiter==3.5.0
```

**步骤 2**：在 `app.py` 中添加限流配置

```python
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["20 per minute"],  # 默认每分钟 20 次
    storage_uri="memory://"           # 使用内存存储限流数据
)

@app.route('/api/speech', methods=['POST'])
@limiter.limit("5 per minute")  # API 接口更严格：每分钟 5 次
def api_speech():
    # ...
```

---

#### 7. 支持语速、音量等自定义参数

| 维度 | 说明 |
|------|------|
| **目的** | 让用户可通过 API 自定义语速、音量 |
| **复杂度** | 中 — 需修改 API 参数和引擎设置 |

**API 扩展**：

```python
@app.route('/api/speech', methods=['POST'])
def api_speech():
    data = request.get_json()
    text = data.get('text', '')
    voice_id = data.get('voice')
    rate = data.get('rate', 200)        # 语速，默认 200
    volume = data.get('volume', 1.0)    # 音量，默认最大

    # ... 验证逻辑 ...

    with engine_lock:
        # 设置语音参数
        engine.setProperty('rate', max(50, min(rate, 500)))    # 限制 50~500
        engine.setProperty('volume', max(0.0, min(volume, 1.0)))  # 限制 0.0~1.0

        if voice_id is not None:
            voices = engine.getProperty('voices')
            try:
                voice_idx = int(voice_id)
                if 0 <= voice_idx < len(voices):
                    engine.setProperty('voice', voices[voice_idx].id)
            except (ValueError, TypeError):
                pass

        engine.save_to_file(text, filepath)
        engine.runAndWait()

    return jsonify({'status': 'success', 'url': f'/static/mp3/{filename}'})
```

**请求示例**：

```json
{
  "text": "你好世界",
  "voice": 2,
  "rate": 180,
  "volume": 0.8
}
```

---

#### 8. 添加健康检查接口

| 维度 | 说明 |
|------|------|
| **目的** | 便于监控和容器编排（K8s/Docker 健康探测） |
| **复杂度** | 低 — 只需添加一个简单路由 |

```python
@app.route('/health')
def health():
    voices = engine.getProperty('voices')
    return jsonify({
        'status': 'healthy',
        'uptime': 'running',
        'available_voices': len(voices)
    })
```

**响应示例**：

```json
{
  "status": "healthy",
  "uptime": "running",
  "available_voices": 5
}
```

---

#### 9. 前端体验优化

| 维度 | 说明 |
|------|------|
| **目的** | 添加加载状态、错误提示，改善用户交互体验 |
| **复杂度** | 低 — 只需修改前端 JavaScript |

**修改 `templates/index.html` 中的 JavaScript**：

```javascript
document.getElementById('convert').addEventListener('click', async () => {
    const text = document.getElementById('text').value.trim();
    const voiceIndex = document.getElementById('voice').value;
    const convertBtn = document.getElementById('convert');

    if (!text) {
        alert('请输入文本');
        return;
    }

    // 设置加载状态
    convertBtn.disabled = true;
    convertBtn.textContent = '转换中...';
    convertBtn.classList.add('opacity-50', 'cursor-not-allowed');

    try {
        const response = await fetch('/api/speech', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text: text, voice: voiceIndex })
        });

        const data = await response.json();

        if (data.status === 'success') {
            const audio = document.getElementById('audio');
            audio.src = data.url;
            audio.classList.remove('hidden');

            const downloadLink = document.getElementById('download');
            downloadLink.href = data.url;
            downloadLink.classList.remove('hidden');
        } else {
            alert(data.error || '转换失败，请重试');
        }
    } catch (error) {
        console.error('Error:', error);
        alert('网络错误，请检查连接后重试');
    } finally {
        // 恢复按钮状态
        convertBtn.disabled = false;
        convertBtn.textContent = '转换为语音';
        convertBtn.classList.remove('opacity-50', 'cursor-not-allowed');
    }
});
```

---

#### 10. 日志记录

| 维度 | 说明 |
|------|------|
| **目的** | 记录请求信息和错误，便于问题排查 |
| **复杂度** | 低 — 只需配置 Python 标准 logging |

```python
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

logger = logging.getLogger(__name__)

@app.route('/api/speech', methods=['POST'])
def api_speech():
    data = request.get_json()
    text = data.get('text', '')

    logger.info(f'Speech request received: text_length={len(text)}, '
                f'ip={request.remote_addr}')

    # ... 处理逻辑 ...

    logger.info(f'Speech generated successfully: {filename}')
    return jsonify({'status': 'success', 'url': f'/static/mp3/{filename}'})
```

---

### 完整优化代码参考

以下是整合了所有 P0 + P1 优化后的完整 `app.py`：

```python
from flask import Flask, request, jsonify, render_template
import pyttsx3
import os
import time
import uuid
import threading
import logging
from pathlib import Path

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

app = Flask(__name__, static_url_path='/static')
app.config['UPLOAD_FOLDER'] = 'static/mp3'

# 确保 mp3 文件夹存在
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

# 初始化语音引擎
engine = pyttsx3.init()

# 线程锁（保护 pyttsx3 引擎的并发访问）
engine_lock = threading.Lock()

# 最大文本长度
MAX_TEXT_LENGTH = 5000

# 文件保留时长（小时）
FILE_MAX_AGE_HOURS = 24


def cleanup_old_files(max_age_hours=24):
    """清理超过指定小时的旧文件"""
    folder = Path(app.config['UPLOAD_FOLDER'])
    if not folder.exists():
        return

    now = time.time()
    cutoff = now - (max_age_hours * 3600)
    cleaned = 0

    for file in folder.glob('*.mp3'):
        if file.stat().st_mtime < cutoff:
            file.unlink()
            cleaned += 1

    if cleaned > 0:
        logger.info(f"已清理 {cleaned} 个过期语音文件")


# 应用启动时清理旧文件
cleanup_old_files(max_age_hours=FILE_MAX_AGE_HOURS)


@app.route('/health')
def health():
    """健康检查接口"""
    voices = engine.getProperty('voices')
    return jsonify({
        'status': 'healthy',
        'uptime': 'running',
        'available_voices': len(voices)
    })


@app.route('/api/speech', methods=['POST'])
def api_speech():
    """文本转语音 API"""
    data = request.get_json()
    if not data:
        return jsonify({'error': '请求体不能为空', 'status': 'error'}), 400

    text = data.get('text', '').strip()
    if not text:
        return jsonify({'error': '文本内容不能为空', 'status': 'error'}), 400

    if len(text) > MAX_TEXT_LENGTH:
        return jsonify({
            'error': f'文本长度不能超过 {MAX_TEXT_LENGTH} 字符',
            'status': 'error'
        }), 400

    voice_id = data.get('voice')
    rate = data.get('rate', 200)
    volume = data.get('volume', 1.0)

    logger.info(f'Speech request: text_length={len(text)}, voice={voice_id}, '
                f'ip={request.remote_addr}')

    # 使用 UUID 生成唯一文件名
    filename = f"api_{uuid.uuid4().hex[:8]}.mp3"
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)

    # 使用线程锁保护引擎调用
    with engine_lock:
        try:
            # 设置语音参数
            engine.setProperty('rate', max(50, min(int(rate), 500)))
            engine.setProperty('volume', max(0.0, min(float(volume), 1.0)))

            if voice_id is not None:
                voices = engine.getProperty('voices')
                try:
                    voice_idx = int(voice_id)
                    if 0 <= voice_idx < len(voices):
                        engine.setProperty('voice', voices[voice_idx].id)
                except (ValueError, TypeError):
                    pass

            engine.save_to_file(text, filepath)
            engine.runAndWait()

        except Exception as e:
            logger.error(f'Speech generation failed: {e}')
            return jsonify({
                'status': 'error',
                'error': f'语音生成失败: {str(e)}'
            }), 500

    logger.info(f'Speech generated: {filename}')
    return jsonify({
        'status': 'success',
        'url': f"/static/mp3/{filename}"
    })


@app.route('/')
def index():
    """主页"""
    voices = engine.getProperty('voices')
    return render_template('index.html', voices=voices)


if __name__ == '__main__':
    logger.info("Starting Flask Text-to-Speech application")
    app.run(host='0.0.0.0', port=5001)
```

---

## 常见问题

### Q1: Windows 下运行报错 `ModuleNotFoundError: No module named 'pyttsx3'`

**A**: 请确保已在当前 Python 环境中安装依赖：
```bash
pip install -r requirements.txt
```

---

### Q2: Linux 下语音生成失败

**A**: 请确保已安装 `espeak` 和 `libespeak-dev`：
```bash
sudo apt-get install -y espeak libespeak-dev
```

---

### Q3: 生成的语音文件无法播放

**A**: pyttsx3 在 Windows 下默认生成 WAV 格式但后缀为 MP3。如果遇到问题，可检查 `pyttsx3` 驱动配置。

---

### Q4: Docker 容器中无法使用语音功能

**A**: pyttsx3 依赖系统语音引擎，Docker 容器中需要安装 `espeak`。当前 `Dockerfile` 已包含此依赖，如果仍有问题，请检查容器日志：
```bash
docker logs tts
```

---

### Q5: 如何修改端口？

**A**: 编辑 `app.py` 最后一行：
```python
app.run(host='0.0.0.0', port=5001)  # 修改 port 参数
```

或在 Docker 中映射不同端口：
```bash
docker run -p 8080:5001 flask-tts
```

---

### Q6: 如何查看可用的音色列表？

**A**: 访问健康检查接口 `http://localhost:5001/health` 可查看可用音色数量。或在 Python 中运行：
```python
import pyttsx3
engine = pyttsx3.init()
voices = engine.getProperty('voices')
for v in voices:
    print(v.name, v.languages)
```

---

## 许可证

本项目仅供学习和参考使用。

---

## 更新日志

| 日期 | 版本 | 说明 |
|------|------|------|
| 2026-04-06 | 2.0.0 | 全面优化：输入验证、线程安全、UUID 文件名、文件清理、健康检查、日志、前端体验优化 |
| 2026-04-06 | 1.0.0 | 初始版本，基础 TTS 功能 |
