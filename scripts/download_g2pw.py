#!/usr/bin/env python3
"""准备 Piper 中文拼音（pinyin）语音所需的 g2pW 资源。

piper-tts 1.4+ 的 ``phoneme_type: pinyin`` 语音（如 zh_CN-chaowen-medium、
zh_CN-xiao_ya-medium）依赖：

1. g2pW 模型（g2pw.onnx + 配置 + 字表），piper 默认在首次合成时从
   HuggingFace 下载到 ``<download_dir>/g2pW``；
2. ``bert-base-chinese`` 的 tokenizer（vocab.txt 等），由 transformers
   在运行时从 HuggingFace 拉取。

镜像构建时预置上述资源，并改写 g2pW 的 ``config.py`` 指向本地 tokenizer，
从而实现完全离线运行。

用法：
    python scripts/download_g2pw.py --out /opt/piper-data/g2pW \
        --bert-out /opt/piper-data/bert-base-chinese

    # 复用本地已下载的 g2pw.tar.gz
    python scripts/download_g2pw.py --archive ./assets/g2pw.tar.gz
"""

from __future__ import annotations

import argparse
import re
import shutil
import sys
import tarfile
import time
import urllib.error
import urllib.request
from pathlib import Path

DEFAULT_G2PW_URL = (
    "https://hf-mirror.com/datasets/rhasspy/piper-checkpoints/resolve/main/"
    "zh/zh_CN/_resources/g2pw.tar.gz"
)
DEFAULT_BERT_BASE = (
    "https://hf-mirror.com/google-bert/bert-base-chinese/resolve/main"
)

BERT_FILES = ("vocab.txt", "tokenizer_config.json", "tokenizer.json")

REQUIRED_FILES = (
    "g2pw.onnx",
    "config.py",
    "POLYPHONIC_CHARS.txt",
    "MONOPHONIC_CHARS.txt",
)

USER_AGENT = (
    "Mozilla/5.0 (compatible; flask-tts/0.2.2; "
    "+https://github.com/vanneswong/flask-tts)"
)

CHUNK_SIZE = 8 * 1024 * 1024


def _request(url: str, headers: dict | None = None) -> urllib.request.Request:
    merged = {"User-Agent": USER_AGENT}
    if headers:
        merged.update(headers)
    return urllib.request.Request(url, headers=merged)


def _download_small(url: str, dst: Path, retries: int = 5) -> None:
    """下载小文件（tokenizer 等），支持简单重试。"""
    dst.parent.mkdir(parents=True, exist_ok=True)
    part = dst.with_name(dst.name + ".part")
    for attempt in range(1, retries + 1):
        try:
            with urllib.request.urlopen(
                _request(url), timeout=60
            ) as resp, open(part, "wb") as fh:
                shutil.copyfileobj(resp, fh)
            if part.stat().st_size == 0:
                raise OSError("响应为空")
            part.replace(dst)
            return
        except (urllib.error.URLError, OSError, TimeoutError) as exc:
            print(f"    下载中断（第 {attempt}/{retries} 次）：{exc}")
            if attempt == retries:
                raise SystemExit(f"下载失败：{url}") from exc
            time.sleep(min(2 * attempt, 10))


def _download_chunked(url: str, dst: Path, retries: int = 8) -> None:
    """按 Range 分块下载大文件。

    HuggingFace 的 Xet 存储在大文件长连接上容易中断，分块下载并逐块重试
    可以显著提高构建成功率。数据边接收边落盘，连接中断后可从断点继续。
    """
    dst.parent.mkdir(parents=True, exist_ok=True)
    part = dst.with_name(dst.name + ".part")

    total: int | None = None
    start = part.stat().st_size if part.exists() else 0
    mode = "r+b" if part.exists() else "w+b"
    attempt = 0

    with open(part, mode) as fh:
        while total is None or start < total:
            end = start + CHUNK_SIZE - 1
            try:
                req = _request(url, {"Range": f"bytes={start}-{end}"})
                with urllib.request.urlopen(req, timeout=60) as resp:
                    if resp.status == 200:
                        # 服务端不支持 Range：从头开始流式读取
                        total = None
                        start = 0
                        fh.seek(0)
                        fh.truncate(0)
                    else:
                        content_range = resp.headers.get("Content-Range", "")
                        match = re.search(r"/\s*(\d+)\s*$", content_range)
                        if match:
                            total = int(match.group(1))
                        fh.seek(start)

                    while True:
                        data = resp.read(256 * 1024)
                        if not data:
                            break
                        fh.write(data)
                        fh.flush()
                        start += len(data)
                        if total and start > total:
                            # 服务端返回了超出范围的数据，截断即可
                            fh.truncate(total)
                            start = total
                            break
                        pct = (
                            min(100, start * 100 // total) if total else 0
                        )
                        print(
                            f"\r    {dst.name}: {pct}% "
                            f"({start}/{total or '?'})",
                            end="",
                            flush=True,
                        )

                if total is None:
                    # 没有 Content-Range：认为一次读完
                    total = start
                attempt = 0
            except (urllib.error.URLError, OSError, TimeoutError) as exc:
                attempt += 1
                print(
                    f"\n    分块下载中断（第 {attempt}/{retries} 次）："
                    f"{exc}"
                )
                if attempt >= retries:
                    raise SystemExit(f"下载失败：{url}") from exc
                time.sleep(min(2 * attempt, 10))

    print()
    actual = part.stat().st_size
    if total is not None and actual != total:
        raise SystemExit(
            f"下载文件大小不完整：{dst.name} {actual}/{total}"
        )
    part.replace(dst)


def _safe_extract(archive: Path, out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    with tarfile.open(archive, "r:gz") as tar:
        for member in tar.getmembers():
            target = out_dir / member.name
            if member.name.startswith("/") or ".." in Path(member.name).parts:
                raise SystemExit(f"压缩包包含不安全路径：{member.name}")
            if not str(target.resolve()).startswith(str(out_dir.resolve())):
                raise SystemExit(f"压缩包路径越界：{member.name}")
        tar.extractall(out_dir)


def _patch_config(config_path: Path, bert_dir: Path) -> None:
    """将 g2pW 的 model_source 指向本地 tokenizer 目录。"""
    text = config_path.read_text(encoding="utf-8")
    replacement = f"model_source = {str(bert_dir)!r}"
    new_text, count = re.subn(
        r"^model_source\s*=.*$", replacement, text, flags=re.MULTILINE
    )
    if count == 0:
        new_text = text.rstrip() + f"\n{replacement}\n"
    if new_text != text:
        config_path.write_text(new_text, encoding="utf-8")


def _g2pw_ready(out_dir: Path, bert_dir: Path) -> bool:
    if not all((out_dir / name).is_file() for name in REQUIRED_FILES):
        return False
    try:
        text = (out_dir / "config.py").read_text(encoding="utf-8")
    except OSError:
        return False
    return str(bert_dir) in text


def _bert_ready(bert_dir: Path) -> bool:
    return all((bert_dir / name).is_file() for name in BERT_FILES)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="准备 Piper 拼音语音的 g2pW + BERT tokenizer 资源"
    )
    parser.add_argument(
        "--out", default="/opt/piper-data/g2pW",
        help="g2pW 资源输出目录",
    )
    parser.add_argument(
        "--bert-out", default="/opt/piper-data/bert-base-chinese",
        help="BERT tokenizer 输出目录",
    )
    parser.add_argument(
        "--archive", default=None,
        help="本地 g2pw.tar.gz（存在则复用，不联网下载）",
    )
    parser.add_argument(
        "--g2pw-url", default=DEFAULT_G2PW_URL, help="g2pw.tar.gz 下载地址",
    )
    parser.add_argument(
        "--bert-base", default=DEFAULT_BERT_BASE,
        help="BERT tokenizer 文件下载地址",
    )
    parser.add_argument(
        "--force", action="store_true", help="强制重新下载/解压",
    )
    args = parser.parse_args()

    out_dir = Path(args.out)
    bert_dir = Path(args.bert_out)

    if not args.force and _g2pw_ready(out_dir, bert_dir):
        print(f"✅ g2pW 资源已就绪：{out_dir}")
    else:
        archive = Path(args.archive) if args.archive else None
        if archive and archive.is_file():
            print(f"[g2pW] 使用本地压缩包：{archive}")
        else:
            if archive:
                print(f"[g2pW] 本地压缩包不存在：{archive}，改为联网下载")
            archive = out_dir.parent / "g2pw.tar.gz"
            if args.force or not archive.is_file() or archive.stat().st_size < 1024:
                print(f"[g2pW] 下载 {args.g2pw_url}")
                _download_chunked(args.g2pw_url, archive)

        print(f"[g2pW] 解压到 {out_dir}")
        _safe_extract(archive, out_dir)

    missing = [name for name in REQUIRED_FILES if not (out_dir / name).is_file()]
    if missing:
        raise SystemExit(f"g2pW 资源缺失：{missing}")

    if not args.force and _bert_ready(bert_dir):
        print(f"✅ BERT tokenizer 已就绪：{bert_dir}")
    else:
        bert_dir.mkdir(parents=True, exist_ok=True)
        for name in BERT_FILES:
            print(f"[BERT] 下载 {name}")
            _download_small(f"{args.bert_base.rstrip('/')}/{name}", bert_dir / name)

    missing = [name for name in BERT_FILES if not (bert_dir / name).is_file()]
    if missing:
        raise SystemExit(f"BERT tokenizer 资源缺失：{missing}")

    _patch_config(out_dir / "config.py", bert_dir)
    print(f"\n✅ 拼音语音资源已就绪：{out_dir}")


if __name__ == "__main__":
    sys.exit(main())
