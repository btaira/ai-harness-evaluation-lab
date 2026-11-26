from __future__ import annotations

import hashlib
import importlib.util
import json
import shutil
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE_PATH = ROOT / "tools" / "prepare_airstream_repository.py"
spec = importlib.util.spec_from_file_location("airstream_base", BASE_PATH)
if spec is None or spec.loader is None:
    raise RuntimeError("Unable to load Airstream staging helpers")
base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)

README = """# Airstream

Technical documents and restoration records for a **1979 Airstream Sovereign**.

## Key files

- [`manuals/1978_Airstream_Excella_500_Service_Manual.pdf`](manuals/1978_Airstream_Excella_500_Service_Manual.pdf) - all 13 factory service sections assembled into one 275-page PDF.
- [`original_documents/1978_Excella_500_Repair_Manual_Chapters/`](original_documents/1978_Excella_500_Repair_Manual_Chapters/) - the untouched source chapter PDFs, preserving their original filenames.
- [`notes/trailer-certification-panel.md`](notes/trailer-certification-panel.md) - transcription and explanation of the certification plate.
- [`metadata/airstream-source-manifest.json`](metadata/airstream-source-manifest.json) - source URLs, hashes, page counts, and chapter order.
- [`reports/1978_Airstream_Excella_500_Service_Manual_QA.txt`](reports/1978_Airstream_Excella_500_Service_Manual_QA.txt) - merge and render-verification results.

## Compatibility note

The service material is labeled **1978 Excella 500**, not 1979 Sovereign. Much of the chassis, shell, plumbing, electrical, and appliance construction is applicable, but model-year-specific wiring, appliance models, tank arrangements, and component details should be cross-checked against the trailer and an exact-year owner's manual.

Airstream's current manuals and archive database is available at:

- https://www.airstream.com/support-tools/owner-resources/owners-manuals-parts-books/

The previously published direct URL for the 1979 owner's manual currently redirects into an error loop, so it was not archived here as an original file.

## Verify or rebuild

Ubuntu/Debian prerequisites:

```bash
sudo apt-get install qpdf poppler-utils
python -m pip install -r requirements.txt
```

Verify the committed originals and combined PDF:

```bash
python tools/rebuild_manual.py --verify
```

Rebuild the combined PDF from the preserved original chapters:

```bash
python tools/rebuild_manual.py --rebuild
```

## Rights

These files are retained for personal archival, maintenance, and restoration reference. See [`RIGHTS.md`](RIGHTS.md). Copyright and trademarks remain with their respective owners.
"""

ORIGINALS_README = """# Original documents

This directory contains the 13 source repair-manual PDFs in the form in which they were retrieved.

- `1978_Excella_500_Repair_Manual_Chapters/` preserves the source filenames unchanged.
- Two filenames contain apparent original typos: `Drainange.pdf` and `Ranger and Oven.pdf`; they are intentionally preserved.
- The unrelated `Camping at Orange County Parks 3 13[1].pdf` file from the source web directory was deliberately excluded.

Airstream's current owner-manual and document database is linked from the repository README. The old direct 1979 owner-manual URL is no longer a reliable download endpoint and was not stored as an original file.
"""

PHOTO_README = """# Trailer photograph

The certification-plate photograph supplied in the ChatGPT conversation was named `IMG_0719.jpeg`.

The GitHub connector used for this migration can write repository text and existing GitHub blobs, but it cannot directly transfer a binary attachment from the chat into a newly staged repository. The original local file was therefore not silently recompressed or replaced.

Expected original file:

- Filename: `IMG_0719.jpeg`
- Size: 772,955 bytes
- SHA-256: `fd1301436f8c01ff17aa6f2021f62cf542b40e0bf8ddb2b8c8e0cd11c4fb0ffc`

Place the original file in this directory to complete the photo archive.
"""

FINAL_WORKFLOW = """name: Verify Airstream documents

on:
  workflow_dispatch:
  push:
    paths:
      - "metadata/airstream-source-manifest.json"
      - "manuals/**"
      - "original_documents/1978_Excella_500_Repair_Manual_Chapters/**"
      - "tools/rebuild_manual.py"
      - "requirements.txt"

permissions:
  contents: read

jobs:
  verify:
    runs-on: ubuntu-latest
    timeout-minutes: 30
    steps:
      - uses: actions/checkout@v4
      - name: Install PDF tools
        run: |
          sudo apt-get update -qq
          sudo apt-get install -y -qq qpdf poppler-utils
          python -m pip install --disable-pip-version-check --quiet -r requirements.txt
      - name: Verify committed documents
        run: python tools/rebuild_manual.py --verify
"""

REBUILD_SCRIPT = r'''from __future__ import annotations

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
'''


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def public_record(record: dict[str, object]) -> dict[str, object]:
    return {
        key: value
        for key, value in record.items()
        if key not in {"path", "start", "end"}
    }


def write_metadata_and_report(
    tree: Path,
    records: list[dict[str, object]],
    output_pdf: Path,
    render_checks: list[str],
    qpdf_result: str,
) -> None:
    manifest = {
        "title": "Airstream document archive",
        "trailer": "1979 Airstream Sovereign",
        "service_manual_source_directory": base.SERVICE_SOURCE_DIRECTORY,
        "combined_output": f"manuals/{base.COMBINED_FILENAME}",
        "chapters": [public_record(record) for record in records],
        "related_document_database": (
            "https://www.airstream.com/support-tools/owner-resources/"
            "owners-manuals-parts-books/"
        ),
        "excluded": [
            {
                "filename": "Camping at Orange County Parks 3 13[1].pdf",
                "reason": "Unrelated to the Airstream service manual",
            }
        ],
    }
    metadata_dir = tree / "metadata"
    metadata_dir.mkdir(parents=True, exist_ok=True)
    (metadata_dir / "airstream-source-manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n",
        encoding="utf-8",
    )

    checksum_lines = [
        f"{record['sha256']}  {record['local_path']}" for record in records
    ]
    checksum_lines.append(
        f"{sha256(output_pdf)}  manuals/{base.COMBINED_FILENAME}"
    )
    (metadata_dir / "SHA256SUMS.txt").write_text(
        "\n".join(checksum_lines) + "\n",
        encoding="utf-8",
    )

    report = [
        "1978 Airstream Excella 500 Service Manual",
        "Combined PDF build and QA report",
        "=" * 58,
        f"Source directory: {base.SERVICE_SOURCE_DIRECTORY}",
        "",
        "Included source PDFs (manual chapter order):",
    ]
    for record in records:
        report.append(
            f"  {int(record['chapter']):02d}. {record['title']} - "
            f"{record['filename']} - {record['pages']} pages - "
            f"merged pages {record['start']}-{record['end']} - "
            f"{record['bytes']} bytes - SHA-256 {record['sha256']}"
        )
    report.extend(
        [
            "",
            "Excluded source-directory file:",
            "  Camping at Orange County Parks 3 13[1].pdf - unrelated to the manual",
            "",
            "Verification results:",
            f"  PASS - all {len(records)} service-manual source PDFs are readable",
            f"  PASS - merged page count equals source total: {sum(int(r['pages']) for r in records)}",
            "  PASS - every merged page preserves its source media box and rotation",
            f"  PASS - qpdf structural check completed ({qpdf_result})",
            f"  PASS - {len(render_checks)} source/merged boundary-page render comparisons",
        ]
    )
    report.extend(f"  {item}" for item in render_checks)
    report.extend(
        [
            "",
            "Combined file:",
            f"  Filename: {output_pdf.name}",
            f"  Pages: {sum(int(r['pages']) for r in records)}",
            f"  Bytes: {output_pdf.stat().st_size}",
            f"  SHA-256: {sha256(output_pdf)}",
            "",
            "Overall result: PASS",
        ]
    )
    report_dir = tree / "reports"
    report_dir.mkdir(parents=True, exist_ok=True)
    (report_dir / base.QA_FILENAME).write_text(
        "\n".join(report) + "\n",
        encoding="utf-8",
    )


def prepare() -> None:
    with tempfile.TemporaryDirectory(prefix="airstream-repository-v2-") as temp_name:
        temp = Path(temp_name)
        tree = temp / "final"
        chapter_dir = (
            tree
            / "original_documents"
            / "1978_Excella_500_Repair_Manual_Chapters"
        )
        chapter_dir.mkdir(parents=True, exist_ok=True)
        session = base.session_with_retries()

        for _, _, filename in base.CHAPTERS:
            base.download_pdf(
                session,
                base.SERVICE_SOURCE_DIRECTORY + base.requests.utils.quote(filename),
                chapter_dir / filename,
            )

        output_pdf = tree / "manuals" / base.COMBINED_FILENAME
        records, render_checks, qpdf_result = base.merge_and_verify(
            chapter_dir,
            output_pdf,
            temp / "renders",
        )

        (tree / "README.md").write_text(README, encoding="utf-8")
        (tree / "RIGHTS.md").write_text(base.RIGHTS, encoding="utf-8")
        (tree / "requirements.txt").write_text(
            "pypdf>=5.0\n",
            encoding="utf-8",
        )

        originals = tree / "original_documents"
        (originals / "README.md").write_text(ORIGINALS_README, encoding="utf-8")
        trailer_dir = originals / "trailer"
        trailer_dir.mkdir(parents=True, exist_ok=True)
        (trailer_dir / "README.md").write_text(PHOTO_README, encoding="utf-8")

        notes = tree / "notes"
        notes.mkdir(parents=True, exist_ok=True)
        (notes / "trailer-certification-panel.md").write_text(
            base.PANEL_NOTES,
            encoding="utf-8",
        )

        tools = tree / "tools"
        tools.mkdir(parents=True, exist_ok=True)
        (tools / "rebuild_manual.py").write_text(REBUILD_SCRIPT, encoding="utf-8")

        workflows = tree / ".github" / "workflows"
        workflows.mkdir(parents=True, exist_ok=True)
        (workflows / "verify-manual.yml").write_text(
            FINAL_WORKFLOW,
            encoding="utf-8",
        )

        write_metadata_and_report(
            tree,
            records,
            output_pdf,
            render_checks,
            qpdf_result,
        )

        for item in ROOT.iterdir():
            if item.name == ".git":
                continue
            if item.is_dir() and not item.is_symlink():
                shutil.rmtree(item)
            else:
                item.unlink()
        for item in tree.iterdir():
            destination = ROOT / item.name
            if item.is_dir():
                shutil.copytree(item, destination)
            else:
                shutil.copy2(item, destination)


if __name__ == "__main__":
    prepare()
