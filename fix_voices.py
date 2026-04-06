"""
注册表修复工具 — 将 Speech Platform 语音复制到 SAPI5 路径，使 pyttsx3 可以识别。

以管理员权限运行:
    python fix_voices.py
"""

import os
import sys
import subprocess
import tempfile
import ctypes


def is_admin():
    """检查是否以管理员权限运行"""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except Exception:
        return False


def run_as_admin():
    """以管理员权限重新运行"""
    script = os.path.abspath(sys.argv[0])
    params = f'"{script}"'
    # sys.executable 是当前 Python 解释器路径
    ret = ctypes.windll.shell32.ShellExecuteW(
        None, "runas", sys.executable, params, None, 1
    )
    if int(ret) <= 32:
        print("❌ 无法获取管理员权限，请右键以管理员身份运行。")
        sys.exit(1)


SOURCE_PATH = r"HKLM\SOFTWARE\Microsoft\Speech Server\v11.0\Voices\Tokens"
TARGET_PATH = r"HKLM\SOFTWARE\Microsoft\Speech\Voices\Tokens"


def get_voice_keys():
    """获取 Speech Platform 下所有语音的注册表项名称"""
    try:
        result = subprocess.run(
            ["reg", "query", SOURCE_PATH],
            capture_output=True, text=True, encoding="gbk"
        )
        if result.returncode != 0:
            return []
        keys = []
        for line in result.stdout.strip().split("\n"):
            line = line.strip()
            if line and "Tokens" in line and not line.endswith("Tokens"):
                key_name = line.rsplit("\\", 1)[-1]
                keys.append(key_name)
        return keys
    except Exception:
        return []


def export_key(key_name):
    """导出注册表项到临时 .reg 文件"""
    source = f"{SOURCE_PATH}\\{key_name}"
    temp_dir = tempfile.gettempdir()
    reg_file = os.path.join(temp_dir, f"{key_name}.reg")

    result = subprocess.run(
        ["reg", "export", source, reg_file, "/y"],
        capture_output=True, text=True, encoding="gbk"
    )
    if result.returncode != 0:
        print(f"  ❌ 导出失败: {key_name}")
        return None
    return reg_file


def modify_and_import(reg_file, key_name):
    """修改 .reg 文件中的路径并导入"""
    try:
        with open(reg_file, "r", encoding="utf-16-le") as f:
            content = f.read()
    except UnicodeDecodeError:
        # 尝试其他编码
        with open(reg_file, "r", encoding="utf-8") as f:
            content = f.read()

    # 替换注册表路径
    old_path = r"HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Speech Server\v11.0\Voices\Tokens"
    new_path = r"HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Speech\Voices\Tokens"
    content = content.replace(old_path, new_path)

    # 写回临时文件
    with open(reg_file, "w", encoding="utf-16-le") as f:
        f.write(content)

    # 导入
    result = subprocess.run(
        ["reg", "import", reg_file],
        capture_output=True, text=True, encoding="gbk"
    )
    return result.returncode == 0


def main():
    # 检查管理员权限
    if not is_admin():
        print("⚠ 需要管理员权限来修改注册表。")
        print("正在请求管理员权限...\n")
        run_as_admin()
        sys.exit(0)

    print("=" * 60)
    print("  pyttsx3 语音注册表修复工具")
    print("=" * 60)
    print()

    # 获取 Speech Platform 下的语音
    voice_keys = get_voice_keys()

    if not voice_keys:
        print("ℹ 未检测到 Speech Platform 语音，无需修复。")
        print("  请先安装 Microsoft Speech Platform 语音包。")
        return

    print(f"✅ 发现 {len(voice_keys)} 个 Speech Platform 语音:\n")
    for key in voice_keys:
        print(f"  • {key}")

    print()
    print("即将把这些语音复制到 SAPI5 路径，使 pyttsx3 可以识别...")
    print()

    success_count = 0
    for key in voice_keys:
        reg_file = export_key(key)
        if reg_file is None:
            continue

        if modify_and_import(reg_file, key):
            print(f"  ✅ 已注册: {key}")
            success_count += 1
            # 清理临时文件
            try:
                os.remove(reg_file)
            except OSError:
                pass
        else:
            print(f"  ❌ 注册失败: {key}")

    print()
    print("=" * 60)
    if success_count > 0:
        print(f"✅ 成功注册 {success_count} 个语音！")
        print()
        print("⚠ 请重启 Python 后运行以下命令验证:")
        print("   python list_voices.py")
    else:
        print("❌ 所有语音注册失败，请检查权限后重试。")
    print("=" * 60)


if __name__ == "__main__":
    main()
