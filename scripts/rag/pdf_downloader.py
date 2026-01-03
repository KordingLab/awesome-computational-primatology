#!/usr/bin/env python3
"""
PDF Downloader for Computational Primatology Papers.

Downloads PDFs in three phases:
- Phase 1: Direct downloads (arXiv, bioRxiv, direct PDF links)
- Phase 2: Unpaywall API for open-access versions of paywalled papers
- Phase 3: Generate list for manual download

Usage:
    python pdf_downloader.py --phase1              # Download easy ones
    python pdf_downloader.py --phase2 --email X   # Try Unpaywall
    python pdf_downloader.py --manual-list        # Generate manual list
    python pdf_downloader.py --all --email X      # Run all phases
"""

import argparse
import asyncio
import json
import re
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

# Paths
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
PAPERS_FILE = DATA_DIR / "papers_with_abstracts.json"
PDFS_DIR = DATA_DIR / "pdfs"

# Rate limiting
ARXIV_DELAY = 1.0  # arXiv asks for 1 request/second
BIORXIV_DELAY = 0.5
DEFAULT_DELAY = 0.3


@dataclass
class DownloadResult:
    """Result of a download attempt."""
    paper_id: str
    success: bool
    path: Optional[Path] = None
    error: Optional[str] = None
    source: str = "unknown"


@dataclass
class DownloadStats:
    """Statistics for download run."""
    phase: int
    attempted: int = 0
    succeeded: int = 0
    failed: int = 0
    skipped: int = 0
    results: list = field(default_factory=list)


def load_papers() -> list[dict]:
    """Load papers from JSON file."""
    with open(PAPERS_FILE) as f:
        return json.load(f)


def save_download_status(papers: list[dict], status_file: Path):
    """Save download status to file."""
    with open(status_file, 'w') as f:
        json.dump(papers, f, indent=2)


def get_pdf_path(paper: dict, source_type: str) -> Path:
    """Get the path where a PDF should be saved."""
    paper_id = paper['id']

    if source_type == 'arxiv':
        return PDFS_DIR / "arxiv" / f"{paper_id}.pdf"
    elif source_type == 'biorxiv':
        return PDFS_DIR / "biorxiv" / f"{paper_id}.pdf"
    elif source_type == 'open_access':
        return PDFS_DIR / "open_access" / f"{paper_id}.pdf"
    else:
        return PDFS_DIR / "manual" / f"{paper_id}.pdf"


def classify_url(url: str) -> tuple[str, Optional[str]]:
    """
    Classify URL and return (source_type, pdf_url).

    Returns:
        (source_type, pdf_url) where pdf_url is None if can't determine
    """
    if not url:
        return ('unknown', None)

    url_lower = url.lower()
    parsed = urlparse(url)

    # arXiv
    if 'arxiv.org' in url_lower:
        # Extract arXiv ID from various formats
        # https://arxiv.org/abs/2509.12193 -> https://arxiv.org/pdf/2509.12193.pdf
        # https://arxiv.org/pdf/2509.12193 -> https://arxiv.org/pdf/2509.12193.pdf
        match = re.search(r'arxiv\.org/(abs|pdf)/(\d+\.\d+)', url)
        if match:
            arxiv_id = match.group(2)
            return ('arxiv', f'https://arxiv.org/pdf/{arxiv_id}.pdf')
        return ('arxiv', None)

    # bioRxiv / medRxiv
    if 'biorxiv.org' in url_lower or 'medrxiv.org' in url_lower:
        # Already a full PDF
        if url_lower.endswith('.pdf'):
            return ('biorxiv', url)
        # https://www.biorxiv.org/content/10.1101/2024.01.29.577734v1
        # -> https://www.biorxiv.org/content/10.1101/2024.01.29.577734v1.full.pdf
        if '/content/' in url:
            pdf_url = url.rstrip('/') + '.full.pdf'
            return ('biorxiv', pdf_url)
        return ('biorxiv', None)

    # Direct PDF link
    if url_lower.endswith('.pdf'):
        return ('open_access', url)

    # OpenCV (openaccess.thecvf.com) - usually direct PDFs
    if 'openaccess.thecvf.com' in url_lower:
        return ('open_access', url)

    # PMC / PubMed Central
    if 'ncbi.nlm.nih.gov/pmc' in url_lower:
        # Need to extract PDF link from page
        return ('pmc', None)

    # Paywalled sources
    if any(domain in url_lower for domain in [
        'ieeexplore.ieee.org', 'link.springer.com', 'onlinelibrary.wiley.com',
        'sciencedirect.com', 'nature.com', 'science.org', 'cell.com',
        'tandfonline.com', 'dl.acm.org'
    ]):
        return ('paywalled', None)

    return ('unknown', None)


class PDFDownloader:
    """Async PDF downloader with rate limiting and retries."""

    def __init__(self, email: Optional[str] = None):
        self.email = email
        self.client: Optional[httpx.AsyncClient] = None

    async def __aenter__(self):
        self.client = httpx.AsyncClient(
            timeout=60.0,
            follow_redirects=True,
            headers={
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
                              'AppleWebKit/537.36 (KHTML, like Gecko) '
                              'Chrome/120.0.0.0 Safari/537.36'
            }
        )
        return self

    async def __aexit__(self, *args):
        if self.client:
            await self.client.aclose()

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def download_pdf(self, url: str, dest: Path) -> bool:
        """Download a PDF from URL to destination."""
        try:
            response = await self.client.get(url)
            response.raise_for_status()

            # Verify it's actually a PDF
            content_type = response.headers.get('content-type', '').lower()
            if 'pdf' not in content_type and not response.content[:4] == b'%PDF':
                raise ValueError(f"Not a PDF: {content_type}")

            # Create parent directory if needed
            dest.parent.mkdir(parents=True, exist_ok=True)

            # Write file
            with open(dest, 'wb') as f:
                f.write(response.content)

            return True

        except Exception as e:
            print(f"  Error downloading {url}: {e}")
            raise

    async def download_phase1(self, papers: list[dict]) -> DownloadStats:
        """
        Phase 1: Download papers with direct PDF access.

        Handles: arXiv, bioRxiv, direct .pdf links
        """
        stats = DownloadStats(phase=1)

        for paper in papers:
            paper_id = paper['id']
            url = paper.get('url', '')

            source_type, pdf_url = classify_url(url)

            # Skip if not a Phase 1 source
            if source_type not in ('arxiv', 'biorxiv', 'open_access'):
                continue

            if pdf_url is None:
                print(f"  {paper_id}: Could not determine PDF URL from {url}")
                stats.failed += 1
                stats.results.append(DownloadResult(
                    paper_id=paper_id, success=False,
                    error="Could not determine PDF URL", source=source_type
                ))
                continue

            dest = get_pdf_path(paper, source_type)

            # Skip if already downloaded
            if dest.exists():
                print(f"  {paper_id}: Already downloaded")
                stats.skipped += 1
                continue

            stats.attempted += 1
            print(f"  {paper_id}: Downloading from {source_type}...")

            try:
                await self.download_pdf(pdf_url, dest)
                print(f"    -> Saved to {dest}")
                stats.succeeded += 1
                stats.results.append(DownloadResult(
                    paper_id=paper_id, success=True, path=dest, source=source_type
                ))

                # Rate limiting
                if source_type == 'arxiv':
                    await asyncio.sleep(ARXIV_DELAY)
                elif source_type == 'biorxiv':
                    await asyncio.sleep(BIORXIV_DELAY)
                else:
                    await asyncio.sleep(DEFAULT_DELAY)

            except Exception as e:
                print(f"    -> Failed: {e}")
                stats.failed += 1
                stats.results.append(DownloadResult(
                    paper_id=paper_id, success=False, error=str(e), source=source_type
                ))

        return stats

    async def try_unpaywall(self, doi: str) -> Optional[str]:
        """Try to find open-access PDF via Unpaywall API."""
        if not self.email:
            return None

        # Clean DOI - remove arXiv: prefix if present
        if doi.startswith('arXiv:'):
            return None  # arXiv handled in Phase 1

        if doi.startswith('10.1101/'):
            return None  # bioRxiv handled in Phase 1

        try:
            url = f"https://api.unpaywall.org/v2/{doi}?email={self.email}"
            response = await self.client.get(url)

            if response.status_code != 200:
                return None

            data = response.json()

            # Try to find best open-access URL
            if data.get('best_oa_location'):
                pdf_url = data['best_oa_location'].get('url_for_pdf')
                if pdf_url:
                    return pdf_url

            # Try other OA locations
            for loc in data.get('oa_locations', []):
                if loc.get('url_for_pdf'):
                    return loc['url_for_pdf']

            return None

        except Exception as e:
            print(f"    Unpaywall error for {doi}: {e}")
            return None

    async def download_phase2(self, papers: list[dict]) -> DownloadStats:
        """
        Phase 2: Try Unpaywall API for paywalled papers.

        Requires email for API access.
        """
        if not self.email:
            raise ValueError("Email required for Phase 2 (Unpaywall API)")

        stats = DownloadStats(phase=2)

        for paper in papers:
            paper_id = paper['id']
            url = paper.get('url', '')
            doi = paper.get('doi', '')

            source_type, _ = classify_url(url)

            # Skip if already handled in Phase 1 or no DOI
            if source_type in ('arxiv', 'biorxiv', 'open_access'):
                continue

            if not doi or doi.startswith('arXiv:'):
                continue

            dest = get_pdf_path(paper, 'open_access')

            # Skip if already downloaded
            if dest.exists():
                print(f"  {paper_id}: Already downloaded")
                stats.skipped += 1
                continue

            stats.attempted += 1
            print(f"  {paper_id}: Trying Unpaywall for DOI {doi}...")

            pdf_url = await self.try_unpaywall(doi)

            if pdf_url:
                try:
                    await self.download_pdf(pdf_url, dest)
                    print(f"    -> Found and saved: {dest}")
                    stats.succeeded += 1
                    stats.results.append(DownloadResult(
                        paper_id=paper_id, success=True, path=dest, source='unpaywall'
                    ))
                except Exception as e:
                    print(f"    -> Download failed: {e}")
                    stats.failed += 1
                    stats.results.append(DownloadResult(
                        paper_id=paper_id, success=False, error=str(e), source='unpaywall'
                    ))
            else:
                print(f"    -> No open-access version found")
                stats.failed += 1
                stats.results.append(DownloadResult(
                    paper_id=paper_id, success=False,
                    error="No open-access version", source='unpaywall'
                ))

            await asyncio.sleep(0.5)  # Rate limit Unpaywall

        return stats


def generate_manual_list(papers: list[dict], output_file: Path) -> int:
    """
    Generate a list of papers that need manual download.

    Returns count of papers needing manual download.
    """
    manual_papers = []

    for paper in papers:
        paper_id = paper['id']
        url = paper.get('url', '')
        doi = paper.get('doi', '')

        source_type, _ = classify_url(url)
        dest = get_pdf_path(paper, source_type)

        # Skip if already downloaded
        if dest.exists():
            continue

        # Check all possible download locations
        for subdir in ['arxiv', 'biorxiv', 'open_access', 'manual']:
            check_path = PDFS_DIR / subdir / f"{paper_id}.pdf"
            if check_path.exists():
                break
        else:
            # Not downloaded yet
            manual_papers.append({
                'id': paper_id,
                'name': paper.get('name', paper.get('title', 'Unknown')),
                'year': paper.get('year', ''),
                'url': url,
                'doi': doi,
                'source_type': source_type,
                'download_to': str(PDFS_DIR / "manual" / f"{paper_id}.pdf")
            })

    # Write markdown file
    with open(output_file, 'w') as f:
        f.write("# Papers Requiring Manual Download\n\n")
        f.write(f"Total: {len(manual_papers)} papers\n\n")
        f.write("Download each PDF and save to the path shown.\n\n")
        f.write("| ID | Name | Year | URL | Save To |\n")
        f.write("|---|---|---|---|---|\n")

        for p in manual_papers:
            name = p['name'][:30] + '...' if len(p['name']) > 30 else p['name']
            f.write(f"| {p['id']} | {name} | {p['year']} | [Link]({p['url']}) | `manual/{p['id']}.pdf` |\n")

    print(f"\nManual download list saved to: {output_file}")
    print(f"Papers needing manual download: {len(manual_papers)}")

    return len(manual_papers)


async def main():
    parser = argparse.ArgumentParser(description="Download PDFs for primatology papers")
    parser.add_argument('--phase1', action='store_true', help='Run Phase 1 (direct downloads)')
    parser.add_argument('--phase2', action='store_true', help='Run Phase 2 (Unpaywall)')
    parser.add_argument('--manual-list', action='store_true', help='Generate manual download list')
    parser.add_argument('--all', action='store_true', help='Run all phases')
    parser.add_argument('--email', type=str, help='Email for Unpaywall API')
    args = parser.parse_args()

    if not any([args.phase1, args.phase2, args.manual_list, args.all]):
        parser.print_help()
        return

    papers = load_papers()
    print(f"Loaded {len(papers)} papers\n")

    async with PDFDownloader(email=args.email) as downloader:
        if args.all or args.phase1:
            print("=" * 50)
            print("PHASE 1: Direct Downloads (arXiv, bioRxiv, etc.)")
            print("=" * 50)
            stats = await downloader.download_phase1(papers)
            print(f"\nPhase 1 Results:")
            print(f"  Attempted: {stats.attempted}")
            print(f"  Succeeded: {stats.succeeded}")
            print(f"  Failed: {stats.failed}")
            print(f"  Skipped (already downloaded): {stats.skipped}")

        if args.all or args.phase2:
            if not args.email:
                print("\nSkipping Phase 2: --email required for Unpaywall API")
            else:
                print("\n" + "=" * 50)
                print("PHASE 2: Unpaywall API")
                print("=" * 50)
                stats = await downloader.download_phase2(papers)
                print(f"\nPhase 2 Results:")
                print(f"  Attempted: {stats.attempted}")
                print(f"  Succeeded: {stats.succeeded}")
                print(f"  Failed: {stats.failed}")
                print(f"  Skipped: {stats.skipped}")

    if args.all or args.manual_list:
        print("\n" + "=" * 50)
        print("PHASE 3: Manual Download List")
        print("=" * 50)
        output_file = DATA_DIR / "manual_downloads.md"
        generate_manual_list(papers, output_file)


if __name__ == "__main__":
    asyncio.run(main())
