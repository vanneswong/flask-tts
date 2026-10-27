#!/usr/bin/env python3
"""下载 Piper 语音模型。

文件清单取自 piper 内置的 voices.json 索引，因此无需手写路径规则。

用法：
    # 从镜像站下载
    python scripts/download_voices.py --out /opt/piper-voices \
        zh_CN-huayan-medium en_US-lessac-medium

    # 优先从本地目录复制（离线构建 / 避免重复下载）
    python scripts/download_voices.py --out ./voices --local ./local-voices \
        zh_CN-huayan-medium

    # 列出全部可用语音 ID
    python scripts/download_voices.py --list
"""

from __future__ import annotations

import argparse
import shutil
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

# 默认下载源（HuggingFace 镜像，国内可直连）
DEFAULT_BASE = "https://hf-mirror.com/rhasspy/piper-voices/resolve/v1.0.0"

SKIP_SUFFIXES = ("MODEL_CARD",)

CHUNK = 256 * 1024

# 部分镜像站会拦截默认的 Python-urllib UA
USER_AGENT = "Mozilla/5.0 (compatible; flask-tts/0.2; +https://github.com/vanneswong/flask-tts)"


def _load_index() -> dict:
    """读取 piper 内置语音索引。"""
    from piper.download import get_voices

    # 传入一个不含 voices.json 的目录，确保使用包内置索引
    return get_voices(Path("/tmp/.piper-voice-index-does-not-exist"))


def _voice_files(index: dict, voice_id: str) -> list[tuple[str, int | None]]:
    if voice_id not in index:
        raise SystemExit(
            f"未知语音：{voice_id}（可用 --list 查看全部语音）"
        )
    files = index[voice_id]["files"]
    return [
        (path, info.get("size_bytes"))
        for path, info in files.items()
        if not path.endswith(SKIP_SUFFIXES)
    ]


def _download(url: str, dst: Path, expected_size: int | None, retries: int = 5) -> None:
    """支持断点续传的下载。

    注意：piper 内置索引中的 size_bytes 可能与镜像站上的实际文件存在版本差异，
    因此大小不一致只告警，不作为失败重试的依据。
    """
    for attempt in range(1, retries + 1):
        pos = dst.stat().st_size if dst.exists() else 0
        headers = {"User-Agent": USER_AGENT}
        if pos:
            headers["Range"] = f"bytes={pos}-"

        req = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                resume = pos > 0 and resp.status == 206
                if pos and not resume:
                    pos = 0  # 服务端不支持 Range，重新下载
                total = int(resp.headers.get("Content-Length") or 0) + pos
                mode = "ab" if resume else "wb"
                with open(dst, mode) as fh:
                    while True:
                        chunk = resp.read(CHUNK)
                        if not chunk:
                            break
                        fh.write(chunk)
                        pos += len(chunk)
                        if total:
                            pct = min(100, pos * 100 // total)
                            print(f"\r    {dst.name}: {pct}% "
                                  f"({pos}/{total})", end="", flush=True)
            print()
        except (urllib.error.URLError, OSError, TimeoutError) as exc:
            print(f"\n    下载中断（第 {attempt}/{retries} 次）：{exc}")
            if attempt == retries:
                raise SystemExit(f"下载失败：{url}")
            time.sleep(min(2 * attempt, 10))
            continue

        actual = dst.stat().st_size
        if expected_size and actual != expected_size:
            print(f"    注意：{dst.name} 实际大小 {actual} 与索引记录的 "
                  f"{expected_size} 不同（索引版本差异），已接受")
        return


def main() -> None:
    parser = argparse.ArgumentParser(description="下载 Piper 语音模型")
    parser.add_argument("voice_ids", nargs="*", help="语音 ID，例如 zh_CN-huayan-medium")
    parser.add_argument("--out", default="/opt/piper-voices", help="模型输出目录")
    parser.add_argument("--local", default=None,
                        help="本地模型目录，命中则直接复制，避免重复下载")
    parser.add_argument("--base", default=DEFAULT_BASE, help="下载源基础地址")
    parser.add_argument("--list", action="store_true", help="列出全部语音 ID")
    parser.add_argument("--filter", default=None,
                        help="配合 --list，按前缀过滤（如 zh_、en_）")
    args = parser.parse_args()

    index = _load_index()

    if args.list:
        for vid in sorted(index):
            if args.filter and not vid.startswith(tuple(args.filter.split(","))):
                continue
            lang = (index[vid].get("language") or {}).get("name_native", "")
            quality = index[vid].get("quality", "")
            print(f"{vid:42s} {quality:8s} {lang}")
        return

    if not args.voice_ids:
        parser.error("请至少指定一个语音 ID，或使用 --list")

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    local_dir = Path(args.local) if args.local else None

    for voice_id in args.voice_ids:
        files = _voice_files(index, voice_id)
        print(f"[{voice_id}] 共 {len(files)} 个文件")
        for rel_path, size in files:
            name = Path(rel_path).name
            dst = out_dir / name

            if local_dir:
                src = local_dir / name
                if src.exists() and src.stat().st_size > 0:
                    if dst.exists() and dst.stat().st_size == src.stat().st_size:
                        print(f"    {name}: 已存在，跳过")
                        continue
                    shutil.copyfile(src, dst)
                    note = ""
                    if size and src.stat().st_size != size:
                        note = "（与索引记录大小不同，已接受）"
                    print(f"    {name}: 从本地复制完成{note}")
                    continue

            if dst.exists() and dst.stat().st_size > 0 and (
                not size or dst.stat().st_size == size
            ):
                print(f"    {name}: 已存在，跳过")
                continue

            url = f"{args.base.rstrip('/')}/{rel_path}"
            print(f"    {name}: 下载中 {url}")
            _download(url, dst, size)
            print(f"    {name}: 完成（{dst.stat().st_size} 字节）")

    print(f"\n✅ 语音模型已就绪：{out_dir}")


if __name__ == "__main__":
    sys.exit(main())
