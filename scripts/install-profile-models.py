from __future__ import annotations

import argparse
import importlib
import subprocess
import sys
from pathlib import Path


def ensure_packages(dep_root: Path) -> None:
    dep_root.mkdir(parents=True, exist_ok=True)

    packages = [
        "transformers>=4.57,<5",
        "huggingface_hub>=0.34,<1",
        "safetensors>=0.5",
        "tokenizers>=0.21",
    ]

    cmd = [
        sys.executable, "-m", "pip", "install",
        "--upgrade", "--target", str(dep_root), *packages,
    ]
    print("PROFILE_R3B10_DEP_INSTALL", " ".join(cmd))
    subprocess.run(cmd, check=True)

    if str(dep_root) not in sys.path:
        sys.path.append(str(dep_root))

    for name in ("transformers", "huggingface_hub", "safetensors", "tokenizers"):
        importlib.import_module(name)


def download_model(dep_root: Path, model_root: Path) -> None:
    if str(dep_root) not in sys.path:
        sys.path.append(str(dep_root))

    from huggingface_hub import snapshot_download

    target = model_root / "clap-htsat-unfused"
    target.mkdir(parents=True, exist_ok=True)

    snapshot_download(
        repo_id="laion/clap-htsat-unfused",
        local_dir=str(target),
    )
    print(f"PROFILE_R3B10_CLAP_MODEL_OK {target}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--dep-root",
        default=r"H:\temp\EZStudio_lab\deps\profile-r3b10",
    )
    ap.add_argument(
        "--model-root",
        default=r"H:\EZStudioModels\profile",
    )
    args = ap.parse_args()

    dep_root = Path(args.dep_root)
    model_root = Path(args.model_root)

    ensure_packages(dep_root)
    download_model(dep_root, model_root)

    print("EZSTUDIO_PROFILE_R3B10_MODELS_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
