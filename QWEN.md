# Flask Text-to-Speech (pyttsx3) 项目上下文

## 项目概述

这是一个基于 Flask 框架和 pyttsx3 库的文本转语音（TTS）Web 应用。该项目提供了一个简单的 Web 界面和 API 接口，允许用户将文本转换为语音文件（MP3 格式），并支持在线播放和下载。

### 主要功能

- **API 接口** (`/api/speech`): 接受 JSON 格式的文本输入，返回生成的语音文件 URL
- **Web 界面** (`/`): 提供用户友好的界面，支持文本输入、音色选择、语音播放和下载
- **Docker 支持**: 提供容器化部署方案，便于在不同环境中运行

### 技术栈

- **后端**: Python 3.9+, Flask 2.3.2
- **TTS 引擎**: pyttsx3 2.98 (离线文本转语音库)
- **前端**: HTML5 + Tailwind CSS (通过 CDN 加载)
- **部署**: Docker (基于 python:3.9-slim 镜像)
- **系统依赖**: espeak, libespeak-dev (Linux 环境下的语音合成依赖)

## 项目结构

```
flask-text2speech-pyttsx3/
├── app.py                 # Flask 主应用程序
├── requirements.txt       # Python 依赖文件
├── Dockerfile             # Docker 容器构建文件
├── QWEN.md                # 项目上下文文档
├── 创建一个基于edge_tts文本转语音应用.txt  # 原始需求文档
├── static/
│   └── mp3/               # 生成的语音文件存储目录
└── templates/
    └── index.html         # Web 界面模板
```

## 关键文件说明

### `app.py`
- Flask 应用主文件，定义了两个路由：
  - `GET /`: 渲染主页模板，传递可用语音列表
  - `POST /api/speech`: 接收 JSON 数据中的 `text` 字段，生成语音文件并返回 URL
- 使用 `pyttsx3` 初始化语音引擎
- 语音文件保存在 `static/mp3/` 目录下，命名格式为 `api_<timestamp>.mp3`
- 服务运行在 **5001 端口**

### `requirements.txt`
- 定义了两个核心依赖：
  - `Flask==2.3.2`: Web 框架
  - `pyttsx3==2.98`: 离线文本转语音库

### `Dockerfile`
- 基于 `python:3.9-slim` 镜像
- 安装系统级语音依赖 (`espeak`, `libespeak-dev`)
- 安装 Python 依赖并暴露 5001 端口

### `templates/index.html`
- 使用 Tailwind CSS 美化的响应式界面
- 包含以下控件：
  - 文本输入框 (textarea)
  - 音色选择下拉框 (select)
  - 转换按钮、播放按钮、下载链接
  - 音频播放器 (HTML5 audio)
- 通过 JavaScript 调用 `/api/speech` API 实现语音转换

## 运行和部署

### 本地运行

**前提条件**:
- Python 3.9+
- 安装 pyttsx3 的系统依赖：
  - **Linux**: `sudo apt-get install espeak libespeak-dev`
  - **Windows**: 通常无需额外安装 (使用 SAPI5)
  - **macOS**: 使用内置的 `nsss` 语音框架

**启动步骤**:
```bash
# 安装依赖
pip install -r requirements.txt

# 运行应用
python app.py
```

应用将在 `http://localhost:5001` 启动。

### Docker 部署

```bash
# 构建镜像
docker build -t flask-tts .

# 运行容器
docker run -p 5001:5001 flask-tts
```

## API 文档

### POST /api/speech

**请求体** (JSON):
```json
{
  "text": "要转换的文本内容"
}
```

**响应体** (JSON):
```json
{
  "status": "success",
  "url": "/static/mp3/api_1744386219.mp3"
}
```

**说明**:
- 语音文件自动保存在 `static/mp3/` 目录
- 文件命名规则: `api_<unix_timestamp>.mp3`

## 开发注意事项

### 已知问题

1. **pyttsx3 的 runAndWait() 问题**: 代码中已处理 `run loop already started` 的运行时错误，通过捕获异常并调用 `engine.endLoop()` 来解决。

2. **音色选择未实现**: 前端页面有声区选择控件，但后端 API 当前**未使用**传入的 `voice` 参数。每次转换都使用默认语音。

3. **文件累积**: 生成的语音文件会持续保存在 `static/mp3/` 目录中，建议定期清理旧文件以节省磁盘空间。

### 可能的改进方向

- 实现音色选择功能 (后端需处理 `voice` 参数并调用 `engine.setProperty('voice', voice_id)`)
- 添加文件自动清理机制 (如定时删除旧文件)
- 支持更多输出格式 (如 WAV, OGG)
- 添加请求限流和输入验证
- 实现异步语音生成 (使用 Celery 等任务队列)

## 端口配置

Flask 应用默认运行在 **5001 端口** (在 `app.py` 的 `app.run()` 中定义)。
