from __future__ import annotations

import importlib.util
import shutil
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
V2_PATH = ROOT / "tools" / "prepare_airstream_repository_v2.py"
spec = importlib.util.spec_from_file_location("airstream_v2", V2_PATH)
if spec is None or spec.loader is None:
    raise RuntimeError("Unable to load Airstream v2 staging helpers")
v2 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(v2)
base = v2.base


def prepare() -> None:
    with tempfile.TemporaryDirectory(prefix="airstream-repository-v3-") as temp_name:
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

        (tree / "README.md").write_text(v2.README, encoding="utf-8")
        (tree / "RIGHTS.md").write_text(base.RIGHTS, encoding="utf-8")
        (tree / "requirements.txt").write_text("pypdf>=5.0\n", encoding="utf-8")

        originals = tree / "original_documents"
        (originals / "README.md").write_text(v2.ORIGINALS_README, encoding="utf-8")
        trailer_dir = originals / "trailer"
        trailer_dir.mkdir(parents=True, exist_ok=True)
        (trailer_dir / "README.md").write_text(v2.PHOTO_README, encoding="utf-8")

        notes = tree / "notes"
        notes.mkdir(parents=True, exist_ok=True)
        (notes / "trailer-certification-panel.md").write_text(
            base.PANEL_NOTES,
            encoding="utf-8",
        )

        tools = tree / "tools"
        tools.mkdir(parents=True, exist_ok=True)
        (tools / "rebuild_manual.py").write_text(
            v2.REBUILD_SCRIPT,
            encoding="utf-8",
        )

        # Preserve the existing workflow tree byte-for-byte so the workflow
        # token is not asked to create, update, or delete workflow files.
        existing_github = ROOT / ".github"
        if existing_github.exists():
            shutil.copytree(existing_github, tree / ".github")

        v2.write_metadata_and_report(
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
