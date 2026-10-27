# syntax=docker/dockerfile:1

# 使用 Python 3.11：piper-phonemize 提供 cp311 的 amd64/arm64 wheel（cp312 缺 arm64）
FROM python:3.11-slim

LABEL maintainer="vanneswong"
LABEL description="Flask Text-to-Speech Application based on Piper (offline neural TTS)"

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# 依赖源与语音源（国内网络环境默认走镜像）
ARG PIP_INDEX_URL=https://mirrors.aliyun.com/pypi/simple
ARG PIPER_VOICE_BASE=https://hf-mirror.com/rhasspy/piper-voices/resolve/v1.0.0
# 内置语音模型（空格分隔），可通过 --build-arg 覆盖
ARG PIPER_VOICES="zh_CN-huayan-medium en_US-lessac-medium"

# 安装 Python 依赖（piper-tts 自带 espeak-ng 音素数据，无需系统级语音包）
COPY requirements.txt .
RUN pip install --index-url "${PIP_INDEX_URL}" --trusted-host mirrors.aliyun.com \
        -r requirements.txt

# 准备语音模型：优先使用构建上下文内预置的模型，缺失则从镜像站下载
COPY scripts/download_voices.py /tmp/download_voices.py
COPY voices/ /tmp/local-voices/
RUN python /tmp/download_voices.py \
        --base "${PIPER_VOICE_BASE}" \
        --out /opt/piper-voices \
        --local /tmp/local-voices \
        ${PIPER_VOICES} \
 && rm -rf /tmp/local-voices /tmp/download_voices.py

# 复制应用代码
COPY app.py tts_engine.py ./
COPY templates/ ./templates/

# 数据目录：生成的音频 / 用户自定义语音
RUN mkdir -p /app/static/audio /app/voices

# 声明可挂载卷，用于数据持久化
VOLUME ["/app/static/audio", "/app/voices"]

EXPOSE 5001

# 以非 root 用户运行
RUN useradd --create-home --shell /bin/bash appuser \
 && chown -R appuser:appuser /app \
 && chmod -R a+rX /opt/piper-voices
USER appuser

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:5001/health')" || exit 1

CMD ["python", "app.py"]
