#!/usr/bin/env python3
"""
Multi-Source PDF Downloader for Computational Primatology Papers.

Tries multiple open-access sources to maximize PDF coverage:
1. bioRxiv/medRxiv API (fixes 403 errors)
2. Semantic Scholar API (finds OA versions)
3. Unpaywall API (finds legal OA versions)
4. PubMed Central
5. Direct PDF links

Usage:
    python multi_source_downloader.py --email your@email.com
"""

import argparse
import asyncio
import json
import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

import httpx

# Paths
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
PAPERS_FILE = DATA_DIR / "papers_with_abstracts.json"
PDFS_DIR = DATA_DIR / "pdfs"

# Rate limits (be respectful)
RATE_LIMIT_DELAY = 1.0


@dataclass
class DownloadResult:
    paper_id: str
    success: bool
    source: str = ""
    path: Optional[Path] = None
    error: Optional[str] = None


def load_papers() -> list[dict]:
    with open(PAPERS_FILE) as f:
        return json.load(f)


def get_downloaded_ids() -> set[str]:
    """Get set of already downloaded paper IDs."""
    downloaded = set()
    for subdir in PDFS_DIR.iterdir():
        if subdir.is_dir():
            for pdf in subdir.glob("*.pdf"):
                downloaded.add(pdf.stem)
    return downloaded


class MultiSourceDownloader:
    def __init__(self, email: str):
        self.email = email
        self.client: Optional[httpx.AsyncClient] = None
        self.stats = {
            "biorxiv": {"attempted": 0, "success": 0},
            "semantic_scholar": {"attempted": 0, "success": 0},
            "unpaywall": {"attempted": 0, "success": 0},
            "pmc": {"attempted": 0, "success": 0},
            "direct": {"attempted": 0, "success": 0},
        }

    async def __aenter__(self):
        self.client = httpx.AsyncClient(
            timeout=60.0,
            follow_redirects=True,
            headers={
                "User-Agent": "Mozilla/5.0 (compatible; PrimatologyRAG/1.0; mailto:{})".format(self.email)
            }
        )
        return self

    async def __aexit__(self, *args):
        if self.client:
            await self.client.aclose()

    async def download_pdf(self, url: str, dest: Path) -> bool:
        """Download PDF from URL."""
        try:
            response = await self.client.get(url)
            response.raise_for_status()

            # Verify it's a PDF
            content_type = response.headers.get("content-type", "").lower()
            if "pdf" not in content_type and not response.content[:4] == b"%PDF":
                return False

            dest.parent.mkdir(parents=True, exist_ok=True)
            with open(dest, "wb") as f:
                f.write(response.content)
            return True
        except Exception as e:
            print(f"      Download error: {e}")
            return False

    async def try_biorxiv_api(self, url: str, paper_id: str) -> Optional[Path]:
        """Try bioRxiv/medRxiv API to get PDF."""
        # Extract DOI from URL
        # e.g., https://www.biorxiv.org/content/10.1101/2024.01.29.577734v1
        match = re.search(r"10\.1101/(\d+\.\d+\.\d+\.\d+)(v\d+)?", url)
        if not match:
            return None

        biorxiv_id = match.group(1)
        version = match.group(2) or ""

        self.stats["biorxiv"]["attempted"] += 1

        # Try direct PDF URL with version
        pdf_url = f"https://www.biorxiv.org/content/10.1101/{biorxiv_id}{version}.full.pdf"
        dest = PDFS_DIR / "biorxiv" / f"{paper_id}.pdf"

        print(f"    Trying bioRxiv: {pdf_url}")

        # Try with different headers
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
                "Accept": "application/pdf,*/*",
                "Referer": url,
            }
            response = await self.client.get(pdf_url, headers=headers)

            if response.status_code == 200:
                content_type = response.headers.get("content-type", "")
                if "pdf" in content_type or response.content[:4] == b"%PDF":
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    with open(dest, "wb") as f:
                        f.write(response.content)
                    self.stats["biorxiv"]["success"] += 1
                    return dest
        except Exception as e:
            print(f"      bioRxiv error: {e}")

        # Try without version
        if version:
            pdf_url = f"https://www.biorxiv.org/content/10.1101/{biorxiv_id}.full.pdf"
            try:
                response = await self.client.get(pdf_url, headers=headers)
                if response.status_code == 200 and response.content[:4] == b"%PDF":
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    with open(dest, "wb") as f:
                        f.write(response.content)
                    self.stats["biorxiv"]["success"] += 1
                    return dest
            except:
                pass

        return None

    async def try_semantic_scholar(self, paper: dict) -> Optional[Path]:
        """Try Semantic Scholar API to find open access PDF."""
        doi = paper.get("doi", "")
        title = paper.get("name", "") or paper.get("title", "")

        if not doi and not title:
            return None

        self.stats["semantic_scholar"]["attempted"] += 1

        try:
            # Search by DOI first
            if doi and not doi.startswith("arXiv:"):
                url = f"https://api.semanticscholar.org/graph/v1/paper/DOI:{doi}?fields=openAccessPdf,title"
                response = await self.client.get(url)

                if response.status_code == 200:
                    data = response.json()
                    if data.get("openAccessPdf", {}).get("url"):
                        pdf_url = data["openAccessPdf"]["url"]
                        dest = PDFS_DIR / "open_access" / f"{paper['id']}.pdf"
                        print(f"    Trying Semantic Scholar: {pdf_url[:60]}...")

                        if await self.download_pdf(pdf_url, dest):
                            self.stats["semantic_scholar"]["success"] += 1
                            return dest

            # Search by title
            if title:
                await asyncio.sleep(RATE_LIMIT_DELAY)
                search_url = f"https://api.semanticscholar.org/graph/v1/paper/search?query={title[:100]}&fields=openAccessPdf,title&limit=1"
                response = await self.client.get(search_url)

                if response.status_code == 200:
                    data = response.json()
                    if data.get("data"):
                        paper_data = data["data"][0]
                        if paper_data.get("openAccessPdf", {}).get("url"):
                            pdf_url = paper_data["openAccessPdf"]["url"]
                            dest = PDFS_DIR / "open_access" / f"{paper['id']}.pdf"
                            print(f"    Trying S2 title search: {pdf_url[:60]}...")

                            if await self.download_pdf(pdf_url, dest):
                                self.stats["semantic_scholar"]["success"] += 1
                                return dest

        except Exception as e:
            print(f"      Semantic Scholar error: {e}")

        return None

    async def try_unpaywall(self, paper: dict) -> Optional[Path]:
        """Try Unpaywall API to find open access PDF."""
        doi = paper.get("doi", "")

        if not doi or doi.startswith("arXiv:") or doi.startswith("10.1101/"):
            return None

        self.stats["unpaywall"]["attempted"] += 1

        try:
            url = f"https://api.unpaywall.org/v2/{doi}?email={self.email}"
            response = await self.client.get(url)

            if response.status_code == 200:
                data = response.json()

                # Try best OA location first
                pdf_url = None
                if data.get("best_oa_location", {}).get("url_for_pdf"):
                    pdf_url = data["best_oa_location"]["url_for_pdf"]
                else:
                    # Try other locations
                    for loc in data.get("oa_locations", []):
                        if loc.get("url_for_pdf"):
                            pdf_url = loc["url_for_pdf"]
                            break

                if pdf_url:
                    dest = PDFS_DIR / "open_access" / f"{paper['id']}.pdf"
                    print(f"    Trying Unpaywall: {pdf_url[:60]}...")

                    if await self.download_pdf(pdf_url, dest):
                        self.stats["unpaywall"]["success"] += 1
                        return dest

        except Exception as e:
            print(f"      Unpaywall error: {e}")

        return None

    async def try_pmc(self, paper: dict) -> Optional[Path]:
        """Try PubMed Central for open access PDF."""
        doi = paper.get("doi", "")
        url = paper.get("url", "")

        # Check if it's a PMC URL
        if "ncbi.nlm.nih.gov/pmc" in url:
            match = re.search(r"PMC(\d+)", url)
            if match:
                pmc_id = match.group(1)
                self.stats["pmc"]["attempted"] += 1

                pdf_url = f"https://www.ncbi.nlm.nih.gov/pmc/articles/PMC{pmc_id}/pdf/"
                dest = PDFS_DIR / "open_access" / f"{paper['id']}.pdf"
                print(f"    Trying PMC: {pdf_url}")

                if await self.download_pdf(pdf_url, dest):
                    self.stats["pmc"]["success"] += 1
                    return dest

        # Try to find PMC ID via DOI
        if doi and not doi.startswith("arXiv:"):
            try:
                # Use NCBI E-utilities to find PMC ID
                eutils_url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pmc&term={doi}[doi]&retmode=json"
                response = await self.client.get(eutils_url)

                if response.status_code == 200:
                    data = response.json()
                    id_list = data.get("esearchresult", {}).get("idlist", [])

                    if id_list:
                        pmc_id = id_list[0]
                        self.stats["pmc"]["attempted"] += 1

                        pdf_url = f"https://www.ncbi.nlm.nih.gov/pmc/articles/PMC{pmc_id}/pdf/"
                        dest = PDFS_DIR / "open_access" / f"{paper['id']}.pdf"
                        print(f"    Trying PMC via DOI: {pdf_url}")

                        if await self.download_pdf(pdf_url, dest):
                            self.stats["pmc"]["success"] += 1
                            return dest

            except Exception as e:
                print(f"      PMC lookup error: {e}")

        return None

    async def try_direct_pdf(self, paper: dict) -> Optional[Path]:
        """Try direct PDF link if URL ends in .pdf."""
        url = paper.get("url", "")

        if url.endswith(".pdf"):
            self.stats["direct"]["attempted"] += 1
            dest = PDFS_DIR / "open_access" / f"{paper['id']}.pdf"
            print(f"    Trying direct: {url[:60]}...")

            if await self.download_pdf(url, dest):
                self.stats["direct"]["success"] += 1
                return dest

        return None

    async def download_paper(self, paper: dict) -> DownloadResult:
        """Try all sources to download a paper."""
        paper_id = paper["id"]
        url = paper.get("url", "")

        print(f"\n  {paper_id}: {paper.get('name', '')[:40]}...")

        # 1. Try bioRxiv/medRxiv API
        if "biorxiv.org" in url or "medrxiv.org" in url:
            result = await self.try_biorxiv_api(url, paper_id)
            if result:
                return DownloadResult(paper_id, True, "biorxiv", result)
            await asyncio.sleep(RATE_LIMIT_DELAY)

        # 2. Try Semantic Scholar
        result = await self.try_semantic_scholar(paper)
        if result:
            return DownloadResult(paper_id, True, "semantic_scholar", result)
        await asyncio.sleep(RATE_LIMIT_DELAY)

        # 3. Try Unpaywall
        result = await self.try_unpaywall(paper)
        if result:
            return DownloadResult(paper_id, True, "unpaywall", result)
        await asyncio.sleep(RATE_LIMIT_DELAY)

        # 4. Try PMC
        result = await self.try_pmc(paper)
        if result:
            return DownloadResult(paper_id, True, "pmc", result)
        await asyncio.sleep(RATE_LIMIT_DELAY)

        # 5. Try direct PDF link
        result = await self.try_direct_pdf(paper)
        if result:
            return DownloadResult(paper_id, True, "direct", result)

        return DownloadResult(paper_id, False, error="No open access version found")

    async def download_all_missing(self, papers: list[dict]) -> list[DownloadResult]:
        """Download all missing papers."""
        downloaded = get_downloaded_ids()
        missing = [p for p in papers if p["id"] not in downloaded]

        print(f"Papers to download: {len(missing)}")
        print(f"Already downloaded: {len(downloaded)}")

        results = []
        for paper in missing:
            result = await self.download_paper(paper)
            results.append(result)

            if result.success:
                print(f"    ✓ Downloaded via {result.source}")

        return results


async def main():
    parser = argparse.ArgumentParser(description="Multi-source PDF downloader")
    parser.add_argument("--email", required=True, help="Email for API access")
    args = parser.parse_args()

    papers = load_papers()
    print(f"Loaded {len(papers)} papers\n")

    async with MultiSourceDownloader(args.email) as downloader:
        results = await downloader.download_all_missing(papers)

        # Summary
        print("\n" + "=" * 60)
        print("DOWNLOAD SUMMARY")
        print("=" * 60)

        successful = [r for r in results if r.success]
        failed = [r for r in results if not r.success]

        print(f"\nTotal attempted: {len(results)}")
        print(f"Successful: {len(successful)}")
        print(f"Failed: {len(failed)}")

        print("\nBy source:")
        for source, stats in downloader.stats.items():
            if stats["attempted"] > 0:
                print(f"  {source}: {stats['success']}/{stats['attempted']}")

        if failed:
            print(f"\nFailed papers ({len(failed)}):")
            for r in failed[:10]:
                print(f"  - {r.paper_id}")
            if len(failed) > 10:
                print(f"  ... and {len(failed) - 10} more")


if __name__ == "__main__":
    asyncio.run(main())
