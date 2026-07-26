"""Extract rule text from cached HAR chapter PDFs into raw/har/.

    python tools/har_text.py

Writes, per chapter in CHAPTERS below:

    raw/har/har-<chapter>.txt    verbatim pdfplumber extract_text output,
                                 one page per formfeed (\\f). NOT cleaned:
                                 running headers, page numbers and the
                                 received-date stamp are all still present,
                                 and dashes are NOT normalised. Cleaning is
                                 a parse-time concern (tools/har_rules.py),
                                 so a parser fix never forces re-extraction.
    raw/har/_manifest.json       provenance: source URL, retrieval date,
                                 SHA-256 of the source PDF, page count.

The PDF itself stays in raw/har/_pdf/ (gitignored). Provenance is the hash,
not the blob.

Idempotent: re-running overwrites the .txt from the cached PDF. It never
re-downloads; fetching is a curl step recorded in the manifest's url field.
"""
import json
import os
import sys

import pdfplumber

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from har_lib import RAW_HAR, RAW_PDF, sha256_file

# One entry per ingested chapter PDF. `retrieved` is the date the PDF was
# actually downloaded, recorded here because extraction may be re-run later.
CHAPTERS = [
    {
        "chapter": "3-160",
        "catchline": "Election Campaign Contributions and Expenditures",
        "pdf": "HAR3-160120916.pdf",
        "url": "https://ags.hawaii.gov/campaign/files/2016/12/HAR3-160120916.pdf",
        "source_page": "https://ags.hawaii.gov/campaign/legal-resources/hawaii-administrative-rules/",
        "retrieved": "2026-07-25",
        "effective_as_printed": "December 9, 2016",
    },
    {
        "chapter": "3-161",
        "catchline": "Administrative Practice and Procedure Before the "
                     "Campaign Spending Commission",
        "pdf": "HAR3-161120916.pdf",
        "url": "https://ags.hawaii.gov/campaign/files/2016/12/HAR3-161120916.pdf",
        "source_page": "https://ags.hawaii.gov/campaign/legal-resources/hawaii-administrative-rules/",
        "retrieved": "2026-07-25",
        "effective_as_printed": "December 9, 2016",
    },
]


def main():
    os.makedirs(RAW_HAR, exist_ok=True)
    manifest_path = os.path.join(RAW_HAR, "_manifest.json")
    manifest = {}
    if os.path.exists(manifest_path):
        manifest = json.load(open(manifest_path, encoding="utf-8"))

    for ch in CHAPTERS:
        pdf_path = os.path.join(RAW_PDF, ch["pdf"])
        if not os.path.exists(pdf_path):
            print(f"MISSING PDF for {ch['chapter']}: {pdf_path}", file=sys.stderr)
            print(f"  fetch it first:  curl -sSL -A <browser UA> {ch['url']}",
                  file=sys.stderr)
            sys.exit(1)

        pages = []
        with pdfplumber.open(pdf_path) as pdf:
            for p in pdf.pages:
                pages.append(p.extract_text() or "")
        text = "\f".join(pages)

        out = os.path.join(RAW_HAR, f"har-{ch['chapter']}.txt")
        with open(out, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)

        manifest[f"har-{ch['chapter']}.txt"] = {
            "chapter": ch["chapter"],
            "catchline": ch["catchline"],
            "pdf": ch["pdf"],
            "sha256_pdf": sha256_file(pdf_path),
            "url": ch["url"],
            "source_page": ch["source_page"],
            "retrieved": ch["retrieved"],
            "effective_as_printed": ch["effective_as_printed"],
            "pages": len(pages),
            "extractor": "pdfplumber extract_text, one page per formfeed, verbatim",
        }
        print(f"{ch['chapter']}: {len(pages)} pages -> {os.path.basename(out)}")

    with open(manifest_path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(manifest, fh, indent=1, ensure_ascii=False)
        fh.write("\n")
    print(f"manifest: {len(manifest)} entries")


if __name__ == "__main__":
    main()
