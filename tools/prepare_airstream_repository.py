from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import tempfile
from pathlib import Path

import requests
from pypdf import PdfReader
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

ROOT = Path(__file__).resolve().parents[1]
SERVICE_SOURCE_DIRECTORY = (
    "https://www.motorcycleproducts.org/AS-Temp/Manuals/"
    "78%20Airstream%20Shop%20Manual/"
    "78%20Excella%20500%20Repair%20Manual/"
)
OWNER_MANUAL_URL = (
    "https://www.airstream.com/wp-content/uploads/2018/11/"
    "1979-travel-trailer-airstream-owner-s-manual-60.pdf"
)
COMBINED_FILENAME = "1978_Airstream_Excella_500_Service_Manual.pdf"
QA_FILENAME = "1978_Airstream_Excella_500_Service_Manual_QA.txt"

CHAPTERS = [
    (1, "Chassis", "Chassis.pdf"),
    (2, "Brakes", "Brakes.pdf"),
    (3, "Shell", "Shell.pdf"),
    (4, "Interior", "Interior.pdf"),
    (5, "Water", "water.pdf"),
    (6, "Drainage", "Drainange.pdf"),
    (7, "L.P.G.", "LPG.pdf"),
    (8, "Electrical", "Electrical.pdf"),
    (9, "Furnace", "Furnace.pdf"),
    (10, "Air Conditioner", "Air Conditioner.pdf"),
    (11, "Water Heater", "Water Heater.pdf"),
    (12, "Range and Oven", "Ranger and Oven.pdf"),
    (13, "Refrigerator", "Refrigerator.pdf"),
]

README = """# Airstream

Technical documents and restoration records for a **1979 Airstream Sovereign**.

## Key files

- [`manuals/1978_Airstream_Excella_500_Service_Manual.pdf`](manuals/1978_Airstream_Excella_500_Service_Manual.pdf) - all 13 factory service sections assembled into one 275-page PDF.
- [`original_documents/1978_Excella_500_Repair_Manual_Chapters/`](original_documents/1978_Excella_500_Repair_Manual_Chapters/) - the untouched source chapter PDFs, preserving their original filenames.
- [`original_documents/1979-travel-trailer-airstream-owner-s-manual-60.pdf`](original_documents/1979-travel-trailer-airstream-owner-s-manual-60.pdf) - Airstream's exact-year 1979 travel-trailer owner's manual.
- [`original_documents/trailer/IMG_0719.jpeg`](original_documents/trailer/IMG_0719.jpeg) - original certification-plate photograph, when present in the migration source.
- [`notes/trailer-certification-panel.md`](notes/trailer-certification-panel.md) - transcription and explanation of the certification plate.
- [`metadata/airstream-source-manifest.json`](metadata/airstream-source-manifest.json) - source URLs, file hashes, page counts, and chapter order.
- [`reports/1978_Airstream_Excella_500_Service_Manual_QA.txt`](reports/1978_Airstream_Excella_500_Service_Manual_QA.txt) - merge and render-verification results.

## Compatibility note

The service material is labeled **1978 Excella 500**, not 1979 Sovereign. Much of the chassis, shell, plumbing, electrical, and appliance construction is applicable, but model-year-specific wiring, appliance models, tank arrangements, and component details should be cross-checked against the exact 1979 owner's manual and the trailer itself.

## Rebuild or verify

Ubuntu/Debian prerequisites:

```bash
sudo apt-get install qpdf poppler-utils
python -m pip install -r requirements.txt
```

Rebuild the combined manual from the preserved original chapters:

```bash
python tools/build_airstream_repository.py --rebuild
```

Verify the committed originals and combined PDF without changing them:

```bash
python tools/build_airstream_repository.py --verify-existing
```

## Rights

These files are retained for personal archival, maintenance, and restoration reference. See [`RIGHTS.md`](RIGHTS.md). Copyright and trademarks remain with their respective owners.
"""

RIGHTS = """# Source and rights notice

This repository preserves historical Airstream service and owner's documentation for personal archival, maintenance, and restoration reference.

- Copyright in the manuals and original illustrations remains with the applicable rights holders.
- Airstream names and marks remain the property of their owner.
- The repository does not claim ownership of the preserved source manuals.
- Verify redistribution rights before making a repository containing these documents public or redistributing the files elsewhere.
- Source URLs and checksums are recorded so each preserved file can be traced to its source.
"""

ORIGINALS_README = """# Original documents

This directory contains source material in the form in which it was retrieved or supplied.

## Contents

- `1978_Excella_500_Repair_Manual_Chapters/` - the 13 individual factory repair-manual PDFs, with the source filenames unchanged. Two source filenames contain apparent original typos: `Drainange.pdf` and `Ranger and Oven.pdf`; they are intentionally preserved.
- `1979-travel-trailer-airstream-owner-s-manual-60.pdf` - the official 1979 Airstream travel-trailer owner's manual.
- `trailer/IMG_0719.jpeg` - the original trailer certification-plate photograph, if available during migration.

The unrelated `Camping at Orange County Parks 3 13[1].pdf` file from the source web directory was deliberately excluded.
"""

PANEL_NOTES = """# Trailer certification panel

The photographed plate is the trailer's federal certification, weight, tire, and identification label.

## Legible specifications

| Marking | Meaning |
|---|---|
| Manufacturer | Airstream, Inc. |
| Date of manufacture | January 30, 1979 |
| GVWR | 7,100 lb maximum fully loaded trailer weight |
| Front GAWR | 3,200 lb maximum front-axle load |
| Rear GAWR | 3,200 lb maximum rear-axle load |
| Original tires | 7.00-15 LT Load Range C or 7.00-15 XCA Load Range C |
| Original rims | 15 x 6 |
| Original cold pressure | 45 psi |
| Vehicle type | Trailer |
| Plate part number | 385722 |

The two axle ratings total 6,400 lb. The difference between that total and the 7,100-lb GVWR is carried in part through the trailer tongue and tow vehicle; neither axle may exceed its own 3,200-lb rating.

The 45-psi marking applies to the original tire specification. Replacement tires, wheels, and valve stems must be compatible, and inflation should follow the replacement tire manufacturer's load data without exceeding wheel or component ratings.

## VIN caution

The VIN stamping in the photograph is faint. Do not use a transcription from the photograph for registration or title work without comparing the physical plate directly with the title and any additional stamped identification on the trailer.
"""

FINAL_WORKFLOW = """name: Verify Airstream documents

on:
  workflow_dispatch:
  push:
    paths:
      - "metadata/airstream-source-manifest.json"
      - "manuals/**"
      - "original_documents/**"
      - "tools/build_airstream_repository.py"
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
        run: python tools/build_airstream_repository.py --verify-existing
"""


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def run(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )


def session_with_retries() -> requests.Session:
    retry = Retry(
        total=6,
        connect=6,
        read=6,
        backoff_factor=2,
        status_forcelist=(408, 429, 500, 502, 503, 504),
        allowed_methods=frozenset({"GET"}),
    )
    session = requests.Session()
    session.mount("https://", HTTPAdapter(max_retries=retry))
    session.headers.update(
        {
            "User-Agent": (
                "Mozilla/5.0 (X11; Linux x86_64) "
                "AppleWebKit/537.36 Chrome/131.0 Safari/537.36"
            ),
            "Accept": "application/pdf,*/*;q=0.8",
        }
    )
    return session


def download_pdf(session: requests.Session, url: str, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    with session.get(url, stream=True, timeout=(30, 240)) as response:
        response.raise_for_status()
        with destination.open("wb") as handle:
            for chunk in response.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    handle.write(chunk)
    if destination.stat().st_size == 0:
        raise RuntimeError(f"Downloaded empty file: {destination.name}")
    with destination.open("rb") as handle:
        if b"%PDF-" not in handle.read(1024):
            raise RuntimeError(f"Downloaded content is not a PDF: {destination.name}")


def render_page(pdf: Path, page_number: int, prefix: Path) -> Path:
    run(
        [
            "pdftoppm",
            "-f",
            str(page_number),
            "-l",
            str(page_number),
            "-r",
            "100",
            "-singlefile",
            str(pdf),
            str(prefix),
        ]
    )
    rendered = prefix.with_suffix(".ppm")
    if not rendered.exists() or rendered.stat().st_size == 0:
        raise RuntimeError(f"Renderer did not create {rendered}")
    return rendered


def inspect_sources(chapter_dir: Path) -> tuple[list[dict[str, object]], int]:
    records: list[dict[str, object]] = []
    total_pages = 0
    for number, title, filename in CHAPTERS:
        path = chapter_dir / filename
        reader = PdfReader(str(path), strict=False)
        pages = len(reader.pages)
        if pages < 1:
            raise RuntimeError(f"PDF has no pages: {filename}")
        start = total_pages + 1
        end = total_pages + pages
        records.append(
            {
                "chapter": number,
                "title": title,
                "filename": filename,
                "url": SERVICE_SOURCE_DIRECTORY + requests.utils.quote(filename),
                "local_path": (
                    "original_documents/1978_Excella_500_Repair_Manual_Chapters/"
                    + filename
                ),
                "pages": pages,
                "start": start,
                "end": end,
                "bytes": path.stat().st_size,
                "sha256": sha256(path),
                "path": path,
            }
        )
        total_pages = end
    return records, total_pages


def merge_and_verify(
    chapter_dir: Path,
    output_pdf: Path,
    render_dir: Path,
) -> tuple[list[dict[str, object]], list[str], str]:
    records, source_page_total = inspect_sources(chapter_dir)
    output_pdf.parent.mkdir(parents=True, exist_ok=True)

    command = ["qpdf", "--empty", "--pages"]
    for record in records:
        command.extend([str(record["path"]), "1-z"])
    command.extend(["--", str(output_pdf)])
    run(command)

    qpdf_result = run(["qpdf", "--check", str(output_pdf)]).stdout.strip()
    merged_reader = PdfReader(str(output_pdf), strict=False)
    if len(merged_reader.pages) != source_page_total:
        raise RuntimeError(
            f"Page-count mismatch: merged={len(merged_reader.pages)}, "
            f"sources={source_page_total}"
        )

    offset = 0
    for record in records:
        source_reader = PdfReader(str(record["path"]), strict=False)
        for source_index, source_page in enumerate(source_reader.pages):
            merged_page = merged_reader.pages[offset + source_index]
            source_box = tuple(round(float(value), 5) for value in source_page.mediabox)
            merged_box = tuple(round(float(value), 5) for value in merged_page.mediabox)
            if source_box != merged_box:
                raise RuntimeError(
                    f"Media-box mismatch in {record['filename']} page {source_index + 1}"
                )
            source_rotation = int(source_page.get("/Rotate", 0) or 0) % 360
            merged_rotation = int(merged_page.get("/Rotate", 0) or 0) % 360
            if source_rotation != merged_rotation:
                raise RuntimeError(
                    f"Rotation mismatch in {record['filename']} page {source_index + 1}"
                )
        offset += int(record["pages"])

    render_dir.mkdir(parents=True, exist_ok=True)
    render_checks: list[str] = []
    for record in records:
        for source_page_number in sorted({1, int(record["pages"])}):
            merged_page_number = int(record["start"]) + source_page_number - 1
            label = f"chapter-{int(record['chapter']):02d}-page-{source_page_number}"
            source_render = render_page(
                Path(record["path"]),
                source_page_number,
                render_dir / f"{label}-source",
            )
            merged_render = render_page(
                output_pdf,
                merged_page_number,
                render_dir / f"{label}-merged",
            )
            source_hash = sha256(source_render)
            merged_hash = sha256(merged_render)
            if source_hash != merged_hash:
                raise RuntimeError(
                    f"Rendered-page mismatch: {record['filename']} page "
                    f"{source_page_number} vs merged page {merged_page_number}"
                )
            render_checks.append(
                f"PASS - {record['filename']} source page {source_page_number} "
                f"matches merged page {merged_page_number} - SHA-256 {source_hash}"
            )

    return records, render_checks, qpdf_result


def public_record(record: dict[str, object]) -> dict[str, object]:
    return {key: value for key, value in record.items() if key != "path" and key not in {"start", "end"}}


def write_metadata_and_report(
    tree: Path,
    records: list[dict[str, object]],
    owner_path: Path,
    output_pdf: Path,
    render_checks: list[str],
    qpdf_result: str,
) -> None:
    owner_reader = PdfReader(str(owner_path), strict=False)
    if len(owner_reader.pages) < 1:
        raise RuntimeError("The 1979 owner's manual has no pages")

    manifest = {
        "title": "Airstream document archive",
        "trailer": "1979 Airstream Sovereign",
        "service_manual_source_directory": SERVICE_SOURCE_DIRECTORY,
        "combined_output": f"manuals/{COMBINED_FILENAME}",
        "owner_manual": {
            "filename": owner_path.name,
            "url": OWNER_MANUAL_URL,
            "local_path": f"original_documents/{owner_path.name}",
            "pages": len(owner_reader.pages),
            "bytes": owner_path.stat().st_size,
            "sha256": sha256(owner_path),
        },
        "chapters": [public_record(record) for record in records],
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
    checksum_lines.extend(
        [
            f"{manifest['owner_manual']['sha256']}  {manifest['owner_manual']['local_path']}",
            f"{sha256(output_pdf)}  manuals/{COMBINED_FILENAME}",
        ]
    )
    photo = tree / "original_documents" / "trailer" / "IMG_0719.jpeg"
    if photo.exists():
        checksum_lines.append(
            f"{sha256(photo)}  original_documents/trailer/IMG_0719.jpeg"
        )
    (metadata_dir / "SHA256SUMS.txt").write_text(
        "\n".join(checksum_lines) + "\n",
        encoding="utf-8",
    )

    report = [
        "1978 Airstream Excella 500 Service Manual",
        "Combined PDF build and QA report",
        "=" * 58,
        f"Source directory: {SERVICE_SOURCE_DIRECTORY}",
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
    (report_dir / QA_FILENAME).write_text("\n".join(report) + "\n", encoding="utf-8")


def write_text_files(tree: Path, script_source: Path) -> None:
    (tree / "README.md").write_text(README, encoding="utf-8")
    (tree / "RIGHTS.md").write_text(RIGHTS, encoding="utf-8")
    (tree / "requirements.txt").write_text("requests>=2.31\npypdf>=5.0\n", encoding="utf-8")

    originals = tree / "original_documents"
    originals.mkdir(parents=True, exist_ok=True)
    (originals / "README.md").write_text(ORIGINALS_README, encoding="utf-8")

    notes = tree / "notes"
    notes.mkdir(parents=True, exist_ok=True)
    (notes / "trailer-certification-panel.md").write_text(PANEL_NOTES, encoding="utf-8")

    tools = tree / "tools"
    tools.mkdir(parents=True, exist_ok=True)
    shutil.copy2(script_source, tools / "build_airstream_repository.py")

    workflows = tree / ".github" / "workflows"
    workflows.mkdir(parents=True, exist_ok=True)
    (workflows / "verify-manual.yml").write_text(FINAL_WORKFLOW, encoding="utf-8")


def prepare_clean_tree() -> None:
    with tempfile.TemporaryDirectory(prefix="airstream-repository-") as temp_name:
        temp = Path(temp_name)
        tree = temp / "final"
        chapter_dir = tree / "original_documents" / "1978_Excella_500_Repair_Manual_Chapters"
        chapter_dir.mkdir(parents=True, exist_ok=True)
        session = session_with_retries()

        for _, _, filename in CHAPTERS:
            download_pdf(
                session,
                SERVICE_SOURCE_DIRECTORY + requests.utils.quote(filename),
                chapter_dir / filename,
            )

        owner_path = tree / "original_documents" / "1979-travel-trailer-airstream-owner-s-manual-60.pdf"
        download_pdf(session, OWNER_MANUAL_URL, owner_path)

        incoming_photo = ROOT / "incoming" / "IMG_0719.jpeg"
        if incoming_photo.exists():
            photo_dir = tree / "original_documents" / "trailer"
            photo_dir.mkdir(parents=True, exist_ok=True)
            shutil.copy2(incoming_photo, photo_dir / "IMG_0719.jpeg")

        output_pdf = tree / "manuals" / COMBINED_FILENAME
        records, render_checks, qpdf_result = merge_and_verify(
            chapter_dir,
            output_pdf,
            temp / "renders",
        )
        write_text_files(tree, Path(__file__).resolve())
        write_metadata_and_report(
            tree,
            records,
            owner_path,
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


def verify_existing() -> None:
    manifest_path = ROOT / "metadata" / "airstream-source-manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    for entry in manifest["chapters"]:
        path = ROOT / str(entry["local_path"])
        if not path.exists():
            raise RuntimeError(f"Missing source document: {entry['local_path']}")
        if sha256(path) != entry["sha256"]:
            raise RuntimeError(f"Checksum mismatch: {entry['local_path']}")
    owner = manifest["owner_manual"]
    owner_path = ROOT / str(owner["local_path"])
    if sha256(owner_path) != owner["sha256"]:
        raise RuntimeError(f"Checksum mismatch: {owner['local_path']}")

    chapter_dir = ROOT / "original_documents" / "1978_Excella_500_Repair_Manual_Chapters"
    output_pdf = ROOT / "manuals" / COMBINED_FILENAME
    with tempfile.TemporaryDirectory(prefix="airstream-verify-") as temp_name:
        expected = Path(temp_name) / "expected.pdf"
        records, _, _ = merge_and_verify(
            chapter_dir,
            expected,
            Path(temp_name) / "renders",
        )
        if sha256(expected) != sha256(output_pdf):
            raise RuntimeError("Combined PDF does not match a fresh merge of the preserved originals")
        if len(PdfReader(str(output_pdf), strict=False).pages) != sum(int(r["pages"]) for r in records):
            raise RuntimeError("Committed combined PDF page count is incorrect")
    print("PASS - committed Airstream documents and combined PDF are verified")


def rebuild() -> None:
    chapter_dir = ROOT / "original_documents" / "1978_Excella_500_Repair_Manual_Chapters"
    output_pdf = ROOT / "manuals" / COMBINED_FILENAME
    with tempfile.TemporaryDirectory(prefix="airstream-rebuild-") as temp_name:
        records, render_checks, qpdf_result = merge_and_verify(
            chapter_dir,
            output_pdf,
            Path(temp_name) / "renders",
        )
    owner_path = ROOT / "original_documents" / "1979-travel-trailer-airstream-owner-s-manual-60.pdf"
    write_metadata_and_report(
        ROOT,
        records,
        owner_path,
        output_pdf,
        render_checks,
        qpdf_result,
    )
    print(f"PASS - rebuilt {output_pdf}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Build and verify the Airstream document archive")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--stage-clean-tree", action="store_true")
    mode.add_argument("--verify-existing", action="store_true")
    mode.add_argument("--rebuild", action="store_true")
    args = parser.parse_args()

    if args.stage_clean_tree:
        prepare_clean_tree()
    elif args.verify_existing:
        verify_existing()
    else:
        rebuild()


if __name__ == "__main__":
    main()
