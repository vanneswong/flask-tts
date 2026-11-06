#!/usr/bin/env python3
"""下载 Piper 语音模型（适配 piper-tts 1.8+）。

piper-tts 1.3 之后不再在 Python 包内附带 voices.json 索引，语音文件统一位于
HuggingFace 仓库 ``rhasspy/piper-voices`` 的 ``main`` 分支，路径规则固定为：

    <family>/<lang_code>/<name>/<quality>/<lang_code>-<name>-<quality>.onnx
    <family>/<lang_code>/<name>/<quality>/<lang_code>-<name>-<quality>.onnx.json

因此本脚本直接按规则拼接下载地址，不再依赖 piper 包内索引。

用法：
    # 从镜像站下载
    python scripts/download_voices.py --out /opt/piper-voices \
        zh_CN-huayan-medium en_US-lessac-medium

    # 优先从本地目录复制（离线构建 / 避免重复下载）
    python scripts/download_voices.py --out ./voices --local ./local-voices \
        zh_CN-chaowen-medium

    # 列出全部可用语音 ID（需要联网获取 voices.json）
    python scripts/download_voices.py --list --filter zh_,en_
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

# 默认下载源（HuggingFace 镜像，国内可直连）
DEFAULT_BASE = "https://hf-mirror.com/rhasspy/piper-voices/resolve/main"

VOICE_PATTERN = re.compile(
    r"^(?P<family>[^-]+)_(?P<region>[^-]+)-"
    r"(?P<name>[^-]+)-(?P<quality>.+)$"
)

# 部分镜像站会拦截默认的 Python-urllib UA
USER_AGENT = (
    "Mozilla/5.0 (compatible; flask-tts/0.2.2; "
    "+https://github.com/vanneswong/flask-tts)"
)

CHUNK = 256 * 1024


def _voice_paths(voice_id: str) -> list[str]:
    """根据语音 ID 生成相对路径（模型 + 配置）。"""
    match = VOICE_PATTERN.match(voice_id.strip())
    if not match:
        raise SystemExit(
            f"语音 ID 格式不正确：{voice_id}"
            "（应形如 zh_CN-chaowen-medium）"
        )

    family = match.group("family")
    lang_code = f"{family}_{match.group('region')}"
    name = match.group("name")
    quality = match.group("quality")
    prefix = f"{family}/{lang_code}/{name}/{quality}/{lang_code}-{name}-{quality}"
    return [prefix + ".onnx", prefix + ".onnx.json"]


def _load_voice_index(base: str) -> dict:
    """读取远程 voices.json（用于 --list）。"""
    url = f"{base.rstrip('/')}/voices.json"
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return json.load(resp)
    except (urllib.error.URLError, OSError, ValueError) as exc:
        raise SystemExit(f"获取语音索引失败：{url}\n{exc}") from exc


def _download(
    url: str,
    dst: Path,
    retries: int = 5,
) -> None:
    """支持断点续传的下载，成功后原子替换目标文件。"""
    part = dst.with_name(dst.name + ".part")
    for attempt in range(1, retries + 1):
        pos = part.stat().st_size if part.exists() else 0
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
                with open(part, mode) as fh:
                    while True:
                        chunk = resp.read(CHUNK)
                        if not chunk:
                            break
                        fh.write(chunk)
                        pos += len(chunk)
                        if total:
                            pct = min(100, pos * 100 // total)
                            print(
                                f"\r    {dst.name}: {pct}% ({pos}/{total})",
                                end="",
                                flush=True,
                            )
            print()
        except (urllib.error.URLError, OSError, TimeoutError) as exc:
            print(f"\n    下载中断（第 {attempt}/{retries} 次）：{exc}")
            if attempt == retries:
                raise SystemExit(f"下载失败：{url}") from exc
            time.sleep(min(2 * attempt, 10))
            continue

        if not part.exists() or part.stat().st_size == 0:
            raise SystemExit(f"下载结果为空：{url}")
        part.replace(dst)
        return


def _copy_local(src: Path, dst: Path) -> None:
    part = dst.with_name(dst.name + ".part")
    shutil.copyfile(src, part)
    part.replace(dst)


def _looks_complete(path: Path) -> bool:
    """粗略判断文件是否完整（避免把上次中断的残留当成成品）。"""
    try:
        size = path.stat().st_size
    except OSError:
        return False
    if size <= 0:
        return False
    if path.suffix == ".onnx":
        return size > 1024 * 1024
    return True


def main() -> None:
    parser = argparse.ArgumentParser(description="下载 Piper 语音模型")
    parser.add_argument(
        "voice_ids", nargs="*",
        help="语音 ID，例如 zh_CN-chaowen-medium",
    )
    parser.add_argument(
        "--out", default="/opt/piper-voices", help="模型输出目录",
    )
    parser.add_argument(
        "--local", default=None,
        help="本地模型目录，命中则直接复制，避免重复下载",
    )
    parser.add_argument(
        "--base", default=DEFAULT_BASE, help="下载源基础地址",
    )
    parser.add_argument("--list", action="store_true", help="列出全部语音 ID")
    parser.add_argument(
        "--filter", default=None,
        help="配合 --list，按前缀过滤（如 zh_,en_）",
    )
    parser.add_argument(
        "--force", action="store_true", help="强制重新下载（覆盖已有文件）",
    )
    args = parser.parse_args()

    if args.list:
        index = _load_voice_index(args.base)
        for vid in sorted(index):
            if args.filter and not vid.startswith(
                tuple(args.filter.split(","))
            ):
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
        rel_paths = _voice_paths(voice_id)
        print(f"[{voice_id}] 共 {len(rel_paths)} 个文件")
        for rel_path in rel_paths:
            name = Path(rel_path).name
            dst = out_dir / name

            if not args.force and _looks_complete(dst):
                print(f"    {name}: 已存在，跳过")
                continue

            if local_dir:
                src = local_dir / name
                if _looks_complete(src):
                    _copy_local(src, dst)
                    print(f"    {name}: 从本地复制完成")
                    continue

            url = f"{args.base.rstrip('/')}/{rel_path}"
            print(f"    {name}: 下载中 {url}")
            _download(url, dst)
            print(f"    {name}: 完成（{dst.stat().st_size} 字节）")

    print(f"\n✅ 语音模型已就绪：{out_dir}")


if __name__ == "__main__":
    sys.exit(main())
