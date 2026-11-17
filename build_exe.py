# -*- coding: utf-8 -*-
"""
Kịch bản đóng gói phần mềm Pharta thành tệp thực thi độc lập duy nhất (.exe) trên Windows
theo yêu cầu UR.NF004 và tiêu chí AC-05.
Cách chạy:
    python build_exe.py
"""

import subprocess
import sys


def build() -> int:
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm",
        "--onefile",
        "--windowed",
        "--name", "Pharta",
        "--add-data", "giao_dien;giao_dien",
        "--add-data", "Core;Core",
        "main.py"
    ]
    print("Đang đóng gói Pharta.exe:", " ".join(cmd))
    return subprocess.call(cmd)


if __name__ == "__main__":
    raise SystemExit(build())
