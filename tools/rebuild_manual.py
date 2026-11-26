from __future__ import annotations

import argparse
import hashlib
import subprocess
import tempfile
from pathlib import Path

from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
CHAPTER_DIR = ROOT / "original_documents" / "1978_Excella_500_Repair_Manual_Chapters"
OUTPUT = ROOT / "manuals" / "1978_Airstream_Excella_500_Service_Manual.pdf"
CHAPTERS = [
    "Chassis.pdf",
    "Brakes.pdf",
    "Shell.pdf",
    "Interior.pdf",
    "water.pdf",
    "Drainange.pdf",
    "LPG.pdf",
    "Electrical.pdf",
    "Furnace.pdf",
    "Air Conditioner.pdf",
    "Water Heater.pdf",
    "Ranger and Oven.pdf",
    "Refrigerator.pdf",
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def run(command: list[str]) -> str:
    result = subprocess.run(
        command,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    return result.stdout


def merge(destination: Path) -> int:
    source_paths = [CHAPTER_DIR / filename for filename in CHAPTERS]
    for path in source_paths:
        if not path.exists():
            raise RuntimeError(f"Missing original document: {path.relative_to(ROOT)}")
        if len(PdfReader(str(path), strict=False).pages) < 1:
            raise RuntimeError(f"Original PDF has no pages: {path.name}")

    destination.parent.mkdir(parents=True, exist_ok=True)
    command = ["qpdf", "--empty", "--pages"]
    for path in source_paths:
        command.extend([str(path), "1-z"])
    command.extend(["--", str(destination)])
    run(command)
    run(["qpdf", "--check", str(destination)])
    return sum(len(PdfReader(str(path), strict=False).pages) for path in source_paths)


def verify() -> None:
    with tempfile.TemporaryDirectory(prefix="airstream-verify-") as temp_name:
        expected = Path(temp_name) / "expected.pdf"
        expected_pages = merge(expected)
        committed_pages = len(PdfReader(str(OUTPUT), strict=False).pages)
        if committed_pages != expected_pages:
            raise RuntimeError(
                f"Page count mismatch: committed={committed_pages}, expected={expected_pages}"
            )
        if sha256(OUTPUT) != sha256(expected):
            raise RuntimeError("Combined PDF does not match a fresh merge of the originals")
    print(f"PASS - verified {len(CHAPTERS)} original PDFs and {expected_pages} merged pages")


def main() -> None:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--verify", action="store_true")
    mode.add_argument("--rebuild", action="store_true")
    args = parser.parse_args()
    if args.verify:
        verify()
    else:
        pages = merge(OUTPUT)
        print(f"PASS - rebuilt {OUTPUT.name} with {pages} pages")


if __name__ == "__main__":
    main()
