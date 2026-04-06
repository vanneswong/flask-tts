"""
音色查看工具 — 列出 pyttsx3 在当前系统上所有可用的语音。

用法:
    python list_voices.py          # 默认只显示中文和英文
    python list_voices.py --all    # 显示所有语言
"""

import sys
import platform
import argparse
import importlib.metadata


def list_voices(show_all=False):
    try:
        import pyttsx3
    except ImportError:
        print("错误: 未安装 pyttsx3，请先运行: pip install pyttsx3")
        sys.exit(1)

    pyttsx3_version = importlib.metadata.version('pyttsx3')

    print(f"\n{'='*60}")
    print(f"  系统可用音色列表")
    print(f"{'='*60}")
    print(f"  操作系统 : {platform.system()} {platform.release()}")
    print(f"  Python    : {platform.python_version()}")
    print(f"  pyttsx3   : {pyttsx3_version}")
    print(f"{'='*60}\n")

    engine = pyttsx3.init()
    voices = engine.getProperty('voices')

    if not voices:
        print("⚠ 未检测到任何可用音色。")
        print("  请检查:")
        print("    Linux  : sudo apt install espeak-ng")
        print()
        sys.exit(1)

    # 定义中文/英文的关键词
    zh_keywords = ['zh', 'cmn', 'yue', 'hak', 'chinese', 'mandarin', 'cantonese']
    en_keywords = ['en', 'english']

    def is_zh_or_en(voice_id):
        vid = voice_id.lower()
        for kw in zh_keywords:
            if kw in vid:
                return True
        for kw in en_keywords:
            if kw in vid:
                return True
        return False

    # 过滤语音
    if not show_all:
        voices = [v for v in voices if is_zh_or_en(v.id)]

    if not voices:
        print("⚠ 未检测到中文或英文语音。")
        print("  查看全部语音: python list_voices.py --all")
        print()
        sys.exit(1)

    print(f"✅ 发现 {len(voices)} 个可用音色:\n")

    for i, voice in enumerate(voices):
        # 尝试从 voice.id 推断语言
        voice_id = voice.id.lower()
        lang_tag = ""
        if any(kw in voice_id for kw in ['zh', 'cmn', 'chinese', 'mandarin']):
            lang_tag = " 🇨🇳 中文"
        elif 'yue' in voice_id or 'cantonese' in voice_id:
            lang_tag = " 🇭🇰 粤语"
        elif 'en-us' in voice_id or 'english' in voice_id:
            lang_tag = " 🇺🇸 英文"
        elif 'en-gb' in voice_id:
            lang_tag = " 🇬🇧 英式英文"
        elif 'en' in voice_id:
            lang_tag = " 🇬🇧 英文"
        elif voice.languages:
            lang_tag = f" {voice.languages[0]}"

        print(f"  [{i}] {voice.name}{lang_tag}")
        print(f"      ID: {voice.id}")
        if voice.languages:
            print(f"      Languages: {voice.languages}")
        print()

    # 输出使用提示
    print(f"{'─'*60}")
    print("  使用方法:")
    print(f"    在 API 请求中传入 voice 参数（音色索引）即可:")
    print(f"    curl -X POST http://localhost:5001/api/speech \\")
    print(f"      -H 'Content-Type: application/json' \\")
    print(f"      -d '{{\"text\":\"你好\",\"voice\":\"0\"}}'")
    print(f"{'─'*60}")

    if not show_all:
        print(f"\n  💡 查看所有 {len(engine.getProperty('voices'))} 种语言:")
        print(f"     python list_voices.py --all\n")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='查看系统可用音色')
    parser.add_argument('--all', action='store_true', help='显示所有语言（默认只显示中文和英文）')
    args = parser.parse_args()
    list_voices(show_all=args.all)
