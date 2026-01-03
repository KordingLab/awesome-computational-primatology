#!/usr/bin/env python3
"""
Browser-based PDF Downloader using Playwright.

Handles sites with Cloudflare protection (bioRxiv, etc.) by using a real browser.

Usage:
    python browser_downloader.py
"""

import json
import re
import time
from pathlib import Path
from typing import Optional

from playwright.sync_api import sync_playwright, Download

# Paths
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
PAPERS_FILE = DATA_DIR / "papers_with_abstracts.json"
PDFS_DIR = DATA_DIR / "pdfs"


def load_papers() -> list[dict]:
    with open(PAPERS_FILE) as f:
        return json.load(f)


def get_downloaded_ids() -> set[str]:
    downloaded = set()
    for subdir in PDFS_DIR.iterdir():
        if subdir.is_dir():
            for pdf in subdir.glob("*.pdf"):
                downloaded.add(pdf.stem)
    return downloaded


def extract_biorxiv_doi(url: str) -> Optional[str]:
    """Extract bioRxiv DOI from URL."""
    match = re.search(r"10\.1101/(\d+(?:\.\d+)*)", url)
    if match:
        return f"10.1101/{match.group(1)}"
    return None


def download_pdf_with_browser(p, pdf_url: str, dest: Path) -> bool:
    """Download a PDF using a fresh browser context."""
    browser = p.chromium.launch(headless=True)

    context = browser.new_context(
        user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        accept_downloads=True,
    )

    page = context.new_page()

    download_result = {"success": False, "download": None}

    def handle_download(download: Download):
        download_result["download"] = download
        download_result["success"] = True

    page.on("download", handle_download)

    try:
        # Navigate - this may throw "Download is starting" which is fine
        try:
            page.goto(pdf_url, wait_until="commit", timeout=60000)
        except Exception as e:
            if "Download is starting" not in str(e):
                raise

        # Wait for download to be triggered
        timeout = 30
        while not download_result["success"] and timeout > 0:
            time.sleep(1)
            timeout -= 1

        if download_result["success"] and download_result["download"]:
            download = download_result["download"]

            # Wait for download to complete
            path = download.path()

            if path:
                # Check if it's a PDF
                with open(path, 'rb') as f:
                    header = f.read(4)

                if header == b'%PDF':
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    download.save_as(dest)
                    browser.close()
                    return True
                else:
                    print(f"    Not a PDF (Cloudflare challenge?)")

    except Exception as e:
        print(f"    Error: {str(e)[:60]}")

    browser.close()
    return False


def main():
    papers = load_papers()
    downloaded = get_downloaded_ids()

    # Get bioRxiv papers that need downloading
    biorxiv_papers = []

    for p in papers:
        if p["id"] in downloaded:
            continue

        url = p.get("url", "")
        if "biorxiv.org" in url or "medrxiv.org" in url:
            biorxiv_papers.append(p)

    print(f"bioRxiv/medRxiv papers to download: {len(biorxiv_papers)}")

    if not biorxiv_papers:
        print("No papers to download with browser")
        return

    success_count = 0
    fail_count = 0

    with sync_playwright() as playwright:
        print("\n" + "=" * 60)
        print("Downloading bioRxiv/medRxiv papers...")
        print("=" * 60)

        for paper in biorxiv_papers:
            paper_id = paper["id"]
            url = paper.get("url", "")
            name = paper.get("name", "")[:40]

            print(f"\n  {paper_id}: {name}...")

            doi = extract_biorxiv_doi(url)
            if not doi:
                print(f"    Could not extract DOI from {url}")
                fail_count += 1
                continue

            pdf_url = f"https://www.biorxiv.org/content/{doi}.full.pdf"
            print(f"    URL: {pdf_url}")

            dest = PDFS_DIR / "biorxiv" / f"{paper_id}.pdf"

            if download_pdf_with_browser(playwright, pdf_url, dest):
                print(f"    ✓ Downloaded")
                success_count += 1
            else:
                fail_count += 1

            # Rate limit
            time.sleep(2)

    print("\n" + "=" * 60)
    print("BROWSER DOWNLOAD SUMMARY")
    print("=" * 60)
    print(f"Successful: {success_count}")
    print(f"Failed: {fail_count}")


if __name__ == "__main__":
    main()
