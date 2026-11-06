# syntax=docker/dockerfile:1

# ---------------------------------------------------------------------------
# 数据阶段：准备与架构无关的中文拼音资源（g2pW + BERT tokenizer）
# 在构建机架构上执行一次，避免多架构构建时重复下载
# ---------------------------------------------------------------------------
FROM --platform=$BUILDPLATFORM python:3.11-slim AS data

ARG PIPER_G2PW_URL="https://hf-mirror.com/datasets/rhasspy/piper-checkpoints/resolve/main/zh/zh_CN/_resources/g2pw.tar.gz"
ARG PIPER_BERT_BASE="https://hf-mirror.com/google-bert/bert-base-chinese/resolve/main"

COPY scripts/download_g2pw.py /tmp/download_g2pw.py
# 若本地 assets/g2pw.tar.gz 存在则直接复用，否则联网下载
COPY assets/ /tmp/local-assets/

RUN python /tmp/download_g2pw.py \
        --out /opt/piper-data/g2pW \
        --bert-out /opt/piper-data/bert-base-chinese \
        --archive /tmp/local-assets/g2pw.tar.gz \
        --g2pw-url "${PIPER_G2PW_URL}" \
        --bert-base "${PIPER_BERT_BASE}" \
 && rm -f /opt/piper-data/g2pw.tar.gz \
 && chmod -R a+rX /opt/piper-data


# ---------------------------------------------------------------------------
# 运行镜像
# ---------------------------------------------------------------------------
FROM python:3.11-slim

LABEL maintainer="vanneswong"
LABEL description="Flask Text-to-Speech Application based on Piper (offline neural TTS)"
LABEL version="0.2.3"

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIPER_DATA_DIR=/opt/piper-data \
    HF_HUB_OFFLINE=1 \
    TRANSFORMERS_OFFLINE=1 \
    HF_HUB_DISABLE_TELEMETRY=1 \
    MALLOC_ARENA_MAX=2

WORKDIR /app

# 依赖源与语音源（国内网络环境默认走镜像）
ARG PIP_INDEX_URL=https://mirrors.aliyun.com/pypi/simple
ARG PIPER_VOICE_BASE=https://hf-mirror.com/rhasspy/piper-voices/resolve/main
# 内置语音模型（空格分隔），可通过 --build-arg 覆盖
ARG PIPER_VOICES="zh_CN-huayan-medium zh_CN-chaowen-medium zh_CN-xiao_ya-medium en_US-lessac-medium"

# 安装 Python 依赖（piper-tts[zh] 提供 g2pW/拼音音素化支持）
COPY requirements.txt .
RUN pip install --index-url "${PIP_INDEX_URL}" --trusted-host mirrors.aliyun.com \
        -r requirements.txt

# 预置拼音语音资源（g2pW 模型 + BERT tokenizer）
COPY --from=data /opt/piper-data /opt/piper-data

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
 && chmod -R a+rX /opt/piper-voices /opt/piper-data
USER appuser

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:5001/health')" || exit 1

CMD ["python", "app.py"]
