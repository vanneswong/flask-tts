FROM python:3.12-slim

LABEL maintainer="flask-tts"
LABEL description="Flask Text-to-Speech Application based on pyttsx3"

WORKDIR /app

# 安装系统级语音依赖
RUN apt-get update && \
    apt-get install -y --no-install-recommends espeak-ng && \
    rm -rf /var/lib/apt/lists/*

# 安装 Python 依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

# 创建语音文件存储目录
RUN mkdir -p static/audio

# 声明可挂载的数据卷（用于持久化生成的语音文件）
VOLUME ["/app/static/audio"]

EXPOSE 5001

# 使用非 root 用户运行（可选，增强安全性）
RUN useradd --create-home --shell /bin/bash appuser && \
    chown -R appuser:appuser /app
USER appuser

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:5001/health')" || exit 1

CMD ["python", "app.py"]
