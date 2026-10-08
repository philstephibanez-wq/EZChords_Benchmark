from __future__ import annotations

import argparse
import hashlib
import importlib
import os
import shutil
import subprocess
import sys
import tempfile
import urllib.request
from pathlib import Path

BEAT_THIS_URL = "https://cloud.cp.jku.at/public.php/dav/files/7ik4RrBKTS273gp/final0.ckpt"


def install_pymongo(dep_root: Path) -> None:
    dep_root.mkdir(parents=True, exist_ok=True)
    cmd = [
        sys.executable, "-m", "pip", "install",
        "--upgrade", "--target", str(dep_root),
        "pymongo>=4.11,<5",
    ]
    print("PROFILE_R3B10D_MONGO_DEP_INSTALL", " ".join(cmd))
    subprocess.run(cmd, check=True)

    if str(dep_root) not in sys.path:
        sys.path.append(str(dep_root))
    importlib.import_module("pymongo")
    print(f"PROFILE_R3B10D_PYMONGO_OK {dep_root}")


def install_beat_this_checkpoint(target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)

    if target.is_file() and target.stat().st_size > 10_000_000:
        digest = hashlib.sha256(target.read_bytes()).hexdigest()
        print(
            "PROFILE_R3B10D_BEAT_THIS_ALREADY_PRESENT "
            f"path={target} size={target.stat().st_size} sha256={digest}"
        )
        return

    fd, temp_name = tempfile.mkstemp(
        prefix="beat_this-final0-",
        suffix=".ckpt.tmp",
        dir=str(target.parent),
    )
    os.close(fd)
    temp = Path(temp_name)

    try:
        print(f"PROFILE_R3B10D_BEAT_THIS_DOWNLOAD {BEAT_THIS_URL}")
        with urllib.request.urlopen(BEAT_THIS_URL, timeout=120) as response:
            with temp.open("wb") as out:
                shutil.copyfileobj(response, out)

        if temp.stat().st_size <= 10_000_000:
            raise RuntimeError(f"beat_this_checkpoint_too_small:{temp.stat().st_size}")

        temp.replace(target)
        digest = hashlib.sha256(target.read_bytes()).hexdigest()
        print(
            "PROFILE_R3B10D_BEAT_THIS_OK "
            f"path={target} size={target.stat().st_size} sha256={digest}"
        )
    finally:
        temp.unlink(missing_ok=True)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mongo-dep-root", default=r"H:\temp\EZStudio_lab\deps\mongo-r1")
    ap.add_argument(
        "--beat-this-checkpoint",
        default=r"H:\EZStudioModels\beat_this\beat_this-final0.ckpt",
    )
    args = ap.parse_args()

    install_pymongo(Path(args.mongo_dep_root))
    install_beat_this_checkpoint(Path(args.beat_this_checkpoint))
    print("EZSTUDIO_PROFILE_R3B10D_RUNTIME_INSTALL_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
