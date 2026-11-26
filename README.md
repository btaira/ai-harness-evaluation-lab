# Airstream

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
