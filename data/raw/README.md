# Raw Data Snapshot

This folder holds a local, reproducible snapshot of the Ontario Open Data LTB Order Catalogue used for MVP 0 development. It is **not committed to git** (see root `.gitignore`) — regenerate it with the command below.

## Source

* **Dataset:** LTB Order Catalogue — Ontario Open Data
* **Download URL:** `https://data.ontario.ca/datastore/dump/86e75d11-1c2c-4cd9-9b0d-9fccec302b30?bom=True`
* **Format:** CSV, UTF-8 with BOM, bilingual (English/French) column headers

## Files

* `ltb_2026.csv` — full catalogue dump, downloaded 2026-09-13 (UTC). ~49,269 data rows, 18 columns.

## Reproducing the snapshot

```
curl -L -o data/raw/ltb_2026.csv "https://data.ontario.ca/datastore/dump/86e75d11-1c2c-4cd9-9b0d-9fccec302b30?bom=True"
```

Re-run this whenever a fresh snapshot is needed; update the download date above when you do.
