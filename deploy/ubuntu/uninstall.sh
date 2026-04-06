#!/bin/bash
#
# Flask TTS 应用 - Ubuntu 卸载脚本
# 使用方法: bash uninstall.sh
#

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}╔══════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║     Flask 文本转语音应用 - Ubuntu 卸载脚本              ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════╝${NC}"
echo ""

SERVICE_NAME="flask-tts"
SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"

# 检查服务是否存在
if [ ! -f "$SERVICE_FILE" ]; then
    echo -e "${RED}❌ 未检测到 ${SERVICE_NAME} 服务${NC}"
    echo -e "${YELLOW}   可能已被卸载或未安装过此项目${NC}"
    exit 1
fi

# 获取服务配置信息
echo -e "${YELLOW}[1/4] 读取服务配置...${NC}"
WORK_DIR=$(grep -oP 'WorkingDirectory=\K.*' "$SERVICE_FILE" 2>/dev/null || echo "")
EXEC_START=$(grep -oP 'ExecStart=\K.*' "$SERVICE_FILE" 2>/dev/null || echo "")
PORT=$(echo "$EXEC_START" | grep -oP 'app\.py\s+\K[0-9]+' 2>/dev/null || echo "未知")

echo -e "  服务文件 : ${BLUE}$SERVICE_FILE${NC}"
echo -e "  项目路径 : ${BLUE}$WORK_DIR${NC}"
echo -e "  运行端口 : ${BLUE}$PORT${NC}"
echo ""

# 确认卸载端口
if [ "$PORT" != "未知" ]; then
    echo -e "${YELLOW}[2/4] 确认卸载信息${NC}"
    echo -e "  检测到服务运行在端口 ${GREEN}$PORT${NC}"
    read -p "  确认卸载此服务? (y/N): " CONFIRM
    
    if [[ ! "$CONFIRM" =~ ^[Yy]$ ]]; then
        echo -e "${YELLOW}❌ 已取消卸载${NC}"
        exit 0
    fi
else
    echo -e "${YELLOW}[2/4] 请输入部署端口${NC}"
    read -p "  端口号: " PORT
    
    if ! [[ "$PORT" =~ ^[0-9]+$ ]]; then
        echo -e "${RED}❌ 请输入有效的端口号${NC}"
        exit 1
    fi
fi

# 停止服务
echo ""
echo -e "${YELLOW}[3/4] 停止并删除服务...${NC}"

if systemctl is-active --quiet "$SERVICE_NAME"; then
    echo -e "  正在停止服务..."
    sudo systemctl stop "$SERVICE_NAME"
    echo -e "  ${GREEN}✅ 服务已停止${NC}"
else
    echo -e "  ${YELLOW}⚠ 服务未运行${NC}"
fi

# 禁用服务
sudo systemctl disable "$SERVICE_NAME" 2>/dev/null || true

# 删除服务文件
if [ -f "$SERVICE_FILE" ]; then
    sudo rm "$SERVICE_FILE"
    echo -e "  ${GREEN}✅ 服务文件已删除${NC}"
fi

# 重载 systemd
sudo systemctl daemon-reload
sudo systemctl reset-failed 2>/dev/null || true

echo -e "  ${GREEN}✅ systemd 配置已清理${NC}"

# 删除项目文件
echo ""
echo -e "${YELLOW}[4/4] 清理项目文件${NC}"

if [ -n "$WORK_DIR" ] && [ -d "$WORK_DIR" ]; then
    echo -e "  项目路径: ${BLUE}$WORK_DIR${NC}"
    read -p "  是否删除项目目录? (y/N): " DEL_DIR
    
    if [[ "$DEL_DIR" =~ ^[Yy]$ ]]; then
        # 先停止可能还在运行的 Python 进程
        pkill -f "python app.py $PORT" 2>/dev/null || true
        
        rm -rf "$WORK_DIR"
        echo -e "  ${GREEN}✅ 项目目录已删除${NC}"
    else
        echo -e "  ${YELLOW}⚠ 项目目录已保留${NC}"
    fi
else
    echo -e "  ${YELLOW}⚠ 未找到项目目录，跳过删除${NC}"
fi

# 完成
echo ""
echo -e "${GREEN}╔══════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║              🎉 卸载完成！                              ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "  已清理:"
echo -e "    ✅ systemd 服务 (${SERVICE_NAME})"
echo -e "    ✅ 端口 ${PORT} 已释放"
if [[ "$DEL_DIR" =~ ^[Yy]$ ]]; then
    echo -e "    ✅ 项目文件"
fi
echo ""
