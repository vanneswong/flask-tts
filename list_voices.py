"""
音色查看工具 — 列出 pyttsx3 在当前系统上所有可用的语音。

用法:
    python list_voices.py
"""

import sys
import platform
import importlib.metadata


def list_voices():
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
        print("    Windows: 设置 → 时间和语言 → 语言和区域 → 安装语音包")
        print("    Linux  : sudo apt install espeak-ng espeak-ng-data")
        print()
        sys.exit(1)

    print(f"✅ 共发现 {len(voices)} 个可用音色:\n")

    for i, voice in enumerate(voices):
        # 尝试从 voice.id 推断语言
        voice_id = voice.id.lower()
        lang_tag = ""
        if 'zh-cn' in voice_id or 'chinese' in voice_id:
            lang_tag = " 🇨🇳 中文"
        elif 'zh-tw' in voice_id:
            lang_tag = " 🇹🇼 繁体中文"
        elif 'en-us' in voice_id or 'english' in voice_id:
            lang_tag = " 🇺🇸 英文"
        elif 'en-gb' in voice_id:
            lang_tag = " 🇬🇧 英式英文"
        elif 'ja' in voice_id or 'japanese' in voice_id:
            lang_tag = " 🇯🇵 日文"
        elif 'ko' in voice_id or 'korean' in voice_id:
            lang_tag = " 🇰🇷 韩文"
        elif 'fr' in voice_id or 'french' in voice_id:
            lang_tag = " 🇫🇷 法文"
        elif 'de' in voice_id or 'german' in voice_id:
            lang_tag = " 🇩🇪 德文"
        elif 'es' in voice_id or 'spanish' in voice_id:
            lang_tag = " 🇪🇸 西班牙文"
        elif 'ru' in voice_id or 'russian' in voice_id:
            lang_tag = " 🇷🇺 俄文"
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
    print(f"{'─'*60}\n")


if __name__ == '__main__':
    list_voices()
