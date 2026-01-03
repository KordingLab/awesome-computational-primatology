#!/usr/bin/env python3
"""
DOI-based PDF Downloader.

Extracts DOIs from README and tries multiple sources to download PDFs:
1. DOI.org redirect following
2. CrossRef API for PDF links
3. Semantic Scholar API
4. Publisher-specific patterns
5. PubMed Central

Usage:
    python doi_downloader.py --email your@email.com
"""

import argparse
import asyncio
import json
import re
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

import httpx

# Paths
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
README_PATH = PROJECT_ROOT / "README_updated.md"
PAPERS_FILE = DATA_DIR / "papers_with_abstracts.json"
PDFS_DIR = DATA_DIR / "pdfs"

RATE_LIMIT = 1.0


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


def extract_dois_from_readme() -> dict[str, str]:
    """Extract DOIs from README and map to paper names."""
    if not README_PATH.exists():
        return {}

    with open(README_PATH) as f:
        content = f.read()

    # Pattern: [Paper Name](https://doi.org/DOI)
    pattern = r'\[([^\]]+)\]\(https://doi\.org/([^\)]+)\)'
    matches = re.findall(pattern, content)

    doi_map = {}
    for name, doi in matches:
        # Clean up the DOI
        doi = doi.strip()
        doi_map[name.strip()] = doi

    return doi_map


def match_papers_to_dois(papers: list[dict], doi_map: dict[str, str]) -> dict[str, str]:
    """Match paper IDs to DOIs from README."""
    paper_dois = {}

    for p in papers:
        paper_id = p['id']
        name = p.get('name', '')

        # Try exact match first
        if name in doi_map:
            paper_dois[paper_id] = doi_map[name]
            continue

        # Try partial match
        for readme_name, doi in doi_map.items():
            if name and name.lower() in readme_name.lower():
                paper_dois[paper_id] = doi
                break
            if readme_name and readme_name.lower() in name.lower():
                paper_dois[paper_id] = doi
                break

        # Use DOI from paper data if available
        if paper_id not in paper_dois:
            paper_doi = p.get('doi', '')
            if paper_doi and not paper_doi.startswith('arXiv:'):
                paper_dois[paper_id] = paper_doi
            else:
                # Extract from URL
                url = p.get('url', '')
                match = re.search(r'doi\.org/(.+?)(?:\s|$|\))', url)
                if match:
                    paper_dois[paper_id] = match.group(1)

    return paper_dois


class DOIDownloader:
    def __init__(self, email: str):
        self.email = email
        self.client: Optional[httpx.AsyncClient] = None
        self.stats = {
            "crossref": 0,
            "semantic_scholar": 0,
            "publisher": 0,
            "pmc": 0,
            "unpaywall": 0,
        }

    async def __aenter__(self):
        self.client = httpx.AsyncClient(
            timeout=60.0,
            follow_redirects=True,
            headers={
                "User-Agent": f"PrimatologyRAG/1.0 (mailto:{self.email})"
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

            content_type = response.headers.get("content-type", "").lower()
            if "pdf" in content_type or response.content[:4] == b"%PDF":
                dest.parent.mkdir(parents=True, exist_ok=True)
                with open(dest, "wb") as f:
                    f.write(response.content)
                return True
        except Exception as e:
            pass
        return False

    async def try_crossref(self, doi: str) -> Optional[str]:
        """Try CrossRef API for PDF link."""
        try:
            url = f"https://api.crossref.org/works/{doi}"
            response = await self.client.get(url, headers={
                "User-Agent": f"PrimatologyRAG/1.0 (mailto:{self.email})"
            })

            if response.status_code == 200:
                data = response.json()
                message = data.get("message", {})

                # Check for PDF link in links
                for link in message.get("link", []):
                    if link.get("content-type") == "application/pdf":
                        return link.get("URL")

                # Check for full-text links
                for link in message.get("link", []):
                    url = link.get("URL", "")
                    if "pdf" in url.lower():
                        return url
        except:
            pass
        return None

    async def try_unpaywall(self, doi: str) -> Optional[str]:
        """Try Unpaywall API."""
        try:
            url = f"https://api.unpaywall.org/v2/{doi}?email={self.email}"
            response = await self.client.get(url)

            if response.status_code == 200:
                data = response.json()

                if data.get("best_oa_location", {}).get("url_for_pdf"):
                    return data["best_oa_location"]["url_for_pdf"]

                for loc in data.get("oa_locations", []):
                    if loc.get("url_for_pdf"):
                        return loc["url_for_pdf"]
        except:
            pass
        return None

    async def try_semantic_scholar(self, doi: str) -> Optional[str]:
        """Try Semantic Scholar API."""
        try:
            url = f"https://api.semanticscholar.org/graph/v1/paper/DOI:{doi}?fields=openAccessPdf"
            response = await self.client.get(url)

            if response.status_code == 200:
                data = response.json()
                if data.get("openAccessPdf", {}).get("url"):
                    return data["openAccessPdf"]["url"]
        except:
            pass
        return None

    async def try_pmc(self, doi: str) -> Optional[str]:
        """Try to find PMC version via DOI."""
        try:
            # Use NCBI E-utilities
            url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pmc&term={doi}[doi]&retmode=json"
            response = await self.client.get(url)

            if response.status_code == 200:
                data = response.json()
                id_list = data.get("esearchresult", {}).get("idlist", [])

                if id_list:
                    pmc_id = id_list[0]
                    return f"https://www.ncbi.nlm.nih.gov/pmc/articles/PMC{pmc_id}/pdf/"
        except:
            pass
        return None

    async def try_publisher_patterns(self, doi: str) -> Optional[str]:
        """Try common publisher PDF URL patterns."""
        patterns = []

        # Springer
        if "10.1007" in doi:
            article_id = doi.split("/")[-1]
            patterns.append(f"https://link.springer.com/content/pdf/{doi}.pdf")

        # Wiley
        if "10.1111" in doi or "10.1002" in doi:
            patterns.append(f"https://onlinelibrary.wiley.com/doi/pdfdirect/{doi}")

        # Nature
        if "10.1038" in doi:
            patterns.append(f"https://www.nature.com/articles/{doi.split('/')[-1]}.pdf")

        # Science
        if "10.1126" in doi:
            patterns.append(f"https://www.science.org/doi/pdf/{doi}")

        # PLOS
        if "10.1371" in doi:
            patterns.append(f"https://journals.plos.org/plosone/article/file?id={doi}&type=printable")

        # Frontiers
        if "10.3389" in doi:
            patterns.append(f"https://www.frontiersin.org/articles/{doi}/pdf")

        for url in patterns:
            try:
                response = await self.client.head(url, follow_redirects=True)
                if response.status_code == 200:
                    content_type = response.headers.get("content-type", "")
                    if "pdf" in content_type.lower():
                        return url
            except:
                continue

        return None

    async def download_by_doi(self, doi: str, paper_id: str, paper_name: str) -> bool:
        """Try all methods to download a paper by DOI."""
        print(f"\n  {paper_id}: {paper_name[:40]}...")
        print(f"    DOI: {doi}")

        dest = PDFS_DIR / "open_access" / f"{paper_id}.pdf"

        # Skip if already downloaded
        if dest.exists():
            print(f"    Already downloaded")
            return True

        # 1. Try Unpaywall (best for finding legal OA versions)
        print(f"    Trying Unpaywall...")
        pdf_url = await self.try_unpaywall(doi)
        if pdf_url:
            if await self.download_pdf(pdf_url, dest):
                print(f"    ✓ Downloaded via Unpaywall")
                self.stats["unpaywall"] += 1
                return True

        await asyncio.sleep(RATE_LIMIT)

        # 2. Try Semantic Scholar
        print(f"    Trying Semantic Scholar...")
        pdf_url = await self.try_semantic_scholar(doi)
        if pdf_url:
            if await self.download_pdf(pdf_url, dest):
                print(f"    ✓ Downloaded via Semantic Scholar")
                self.stats["semantic_scholar"] += 1
                return True

        await asyncio.sleep(RATE_LIMIT)

        # 3. Try CrossRef
        print(f"    Trying CrossRef...")
        pdf_url = await self.try_crossref(doi)
        if pdf_url:
            if await self.download_pdf(pdf_url, dest):
                print(f"    ✓ Downloaded via CrossRef")
                self.stats["crossref"] += 1
                return True

        await asyncio.sleep(RATE_LIMIT)

        # 4. Try PMC
        print(f"    Trying PMC...")
        pdf_url = await self.try_pmc(doi)
        if pdf_url:
            if await self.download_pdf(pdf_url, dest):
                print(f"    ✓ Downloaded via PMC")
                self.stats["pmc"] += 1
                return True

        await asyncio.sleep(RATE_LIMIT)

        # 5. Try publisher patterns
        print(f"    Trying publisher patterns...")
        pdf_url = await self.try_publisher_patterns(doi)
        if pdf_url:
            if await self.download_pdf(pdf_url, dest):
                print(f"    ✓ Downloaded via publisher")
                self.stats["publisher"] += 1
                return True

        print(f"    ✗ No open access version found")
        return False


async def main():
    parser = argparse.ArgumentParser(description="DOI-based PDF downloader")
    parser.add_argument("--email", required=True, help="Email for API access")
    args = parser.parse_args()

    # Load data
    papers = load_papers()
    downloaded = get_downloaded_ids()

    # Extract DOIs from README
    doi_map = extract_dois_from_readme()
    print(f"Found {len(doi_map)} DOIs in README")

    # Match papers to DOIs
    paper_dois = match_papers_to_dois(papers, doi_map)

    # Filter to missing papers with DOIs
    missing_with_doi = []
    for p in papers:
        if p['id'] in downloaded:
            continue
        if p['id'] in paper_dois:
            missing_with_doi.append({
                'id': p['id'],
                'name': p.get('name', ''),
                'doi': paper_dois[p['id']]
            })

    print(f"Missing papers with DOIs: {len(missing_with_doi)}")
    print(f"Already downloaded: {len(downloaded)}")

    if not missing_with_doi:
        print("No papers to download")
        return

    success = 0
    fail = 0

    async with DOIDownloader(args.email) as downloader:
        for paper in missing_with_doi:
            result = await downloader.download_by_doi(
                paper['doi'],
                paper['id'],
                paper['name']
            )
            if result:
                success += 1
            else:
                fail += 1

        print("\n" + "=" * 60)
        print("DOI DOWNLOAD SUMMARY")
        print("=" * 60)
        print(f"Successful: {success}")
        print(f"Failed: {fail}")
        print(f"\nBy source:")
        for source, count in downloader.stats.items():
            if count > 0:
                print(f"  {source}: {count}")


if __name__ == "__main__":
    asyncio.run(main())
