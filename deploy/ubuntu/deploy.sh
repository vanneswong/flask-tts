#!/bin/bash
#
# Flask TTS 应用 - Ubuntu 一键部署脚本
# 使用方法: bash deploy.sh
#

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}╔══════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║     Flask 文本转语音应用 - Ubuntu 部署脚本              ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════╝${NC}"
echo ""

# 获取项目根目录
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$(dirname "$SCRIPT_DIR")")"

echo -e "${YELLOW}[1/5] 检查系统环境...${NC}"

# 检查是否 Ubuntu/Debian
if ! command -v apt &> /dev/null; then
    echo -e "${RED}❌ 此脚本仅支持 Ubuntu/Debian 系统${NC}"
    exit 1
fi

# 检查 Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ 未检测到 Python3，请先安装: sudo apt install python3 python3-pip${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Python3: $(python3 --version)${NC}"

# 检查 pip
if ! command -v pip3 &> /dev/null; then
    echo -e "${YELLOW}正在安装 pip3...${NC}"
    sudo apt install -y python3-pip
fi

# 检查 espeak
if ! dpkg -l | grep -q espeak; then
    echo -e "${YELLOW}正在安装 espeak 依赖...${NC}"
    sudo apt update
    sudo apt install -y espeak libespeak-dev
    echo -e "${GREEN}✅ espeak 安装完成${NC}"
else
    echo -e "${GREEN}✅ espeak 已安装${NC}"
fi

echo ""
echo -e "${YELLOW}[2/5] 选择部署端口${NC}"

# 让用户输入端口
while true; do
    read -p "请输入部署端口 (1024-65535): " PORT
    
    # 验证输入是否为数字
    if ! [[ "$PORT" =~ ^[0-9]+$ ]]; then
        echo -e "${RED}❌ 请输入有效的数字${NC}"
        continue
    fi
    
    # 验证端口范围
    if [ "$PORT" -lt 1024 ] || [ "$PORT" -gt 65535 ]; then
        echo -e "${RED}❌ 端口必须在 1024-65535 范围内${NC}"
        continue
    fi
    
    # 检查端口是否被占用
    if netstat -tuln 2>/dev/null | grep -q ":$PORT " || ss -tuln 2>/dev/null | grep -q ":$PORT "; then
        echo -e "${RED}❌ 端口 $PORT 已被占用，请选择其他端口${NC}"
        continue
    fi
    
    break
done

echo -e "${GREEN}✅ 部署端口: $PORT${NC}"

echo ""
echo -e "${YELLOW}[3/5] 创建 Python 虚拟环境...${NC}"

cd "$PROJECT_DIR"

# 创建虚拟环境
if [ -d "venv" ]; then
    echo -e "${YELLOW}虚拟环境已存在，将重新创建${NC}"
    rm -rf venv
fi

python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip

echo -e "${GREEN}✅ 虚拟环境创建成功${NC}"

echo ""
echo -e "${YELLOW}[4/5] 安装依赖...${NC}"

pip install -r requirements.txt

echo -e "${GREEN}✅ 依赖安装完成${NC}"

echo ""
echo -e "${YELLOW}[5/5] 配置 systemd 服务...${NC}"

# 创建 systemd 服务文件
SERVICE_FILE="/etc/systemd/system/flask-tts.service"

sudo tee "$SERVICE_FILE" > /dev/null <<EOF
[Unit]
Description=Flask Text-to-Speech Application
After=network.target

[Service]
Type=simple
User=$USER
Group=$USER
WorkingDirectory=$PROJECT_DIR
Environment="PATH=$PROJECT_DIR/venv/bin"
ExecStart=$PROJECT_DIR/venv/bin/python app.py $PORT
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

echo -e "${GREEN}✅ systemd 服务配置完成${NC}"

echo ""
echo -e "${BLUE}正在启动服务...${NC}"

# 重载 systemd 配置
sudo systemctl daemon-reload

# 停止旧服务（如果存在）
sudo systemctl stop flask-tts 2>/dev/null || true

# 启用并启动服务
sudo systemctl enable flask-tts
sudo systemctl start flask-tts

# 等待服务启动
sleep 2

# 检查服务状态
if systemctl is-active --quiet flask-tts; then
    echo ""
    echo -e "${GREEN}╔══════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║              🎉 部署成功！                              ║${NC}"
    echo -e "${GREEN}╚══════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "  访问地址: ${BLUE}http://localhost:$PORT${NC}"
    echo -e "  API 地址: ${BLUE}http://localhost:$PORT/api/speech${NC}"
    echo -e "  健康检查: ${BLUE}http://localhost:$PORT/health${NC}"
    echo ""
    echo -e "  常用命令:"
    echo -e "    查看状态:  ${YELLOW}sudo systemctl status flask-tts${NC}"
    echo -e "    停止服务:  ${YELLOW}sudo systemctl stop flask-tts${NC}"
    echo -e "    重启服务:  ${YELLOW}sudo systemctl restart flask-tts${NC}"
    echo -e "    查看日志:  ${YELLOW}journalctl -u flask-tts -f${NC}"
    echo ""
else
    echo ""
    echo -e "${RED}❌ 服务启动失败，请检查日志:${NC}"
    echo -e "${YELLOW}journalctl -u flask-tts -e${NC}"
    exit 1
fi
