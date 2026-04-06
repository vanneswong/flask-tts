#!/bin/bash
#
# 部署包打包脚本
# 使用方法: bash package.sh
#

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PACKAGE_NAME="flask-tts-ubuntu"
OUTPUT_FILE="$SCRIPT_DIR/${PACKAGE_NAME}.tar.gz"

echo -e "${BLUE}╔══════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║     Flask TTS Ubuntu 部署包打包工具                    ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════╝${NC}"
echo ""

cd "$SCRIPT_DIR"

if [ ! -d "$PACKAGE_NAME" ]; then
    echo -e "${RED}❌ 部署包目录 $PACKAGE_NAME 不存在${NC}"
    exit 1
fi

# 清理旧的语音文件
rm -f "$PACKAGE_NAME/static/mp3/"*.mp3 2>/dev/null || true

# 设置执行权限
chmod +x "$PACKAGE_NAME/deploy.sh"
chmod +x "$PACKAGE_NAME/list_voices.py"

echo -e "${YELLOW}正在打包...${NC}"

tar -czf "$OUTPUT_FILE" "$PACKAGE_NAME/"

FILE_SIZE=$(du -h "$OUTPUT_FILE" | cut -f1)

echo ""
echo -e "${GREEN}╔══════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}  ✅ 打包完成！                                          ${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "  输出文件: ${BLUE}$OUTPUT_FILE${NC}"
echo -e "  文件大小: ${BLUE}$FILE_SIZE${NC}"
echo ""
echo -e "  部署方式:"
echo -e "    1. 将 ${YELLOW}${PACKAGE_NAME}.tar.gz${NC} 上传到 Ubuntu 服务器"
echo -e "    2. 解压: ${YELLOW}tar -xzf ${PACKAGE_NAME}.tar.gz${NC}"
echo -e "    3. 进入目录: ${YELLOW}cd ${PACKAGE_NAME}${NC}"
echo -e "    4. 运行部署: ${YELLOW}bash deploy.sh${NC}"
echo ""
