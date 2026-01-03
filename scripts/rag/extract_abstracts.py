#!/usr/bin/env python3
"""
Extract abstracts and titles for papers in the computational primatology database.

Uses multiple APIs:
- CrossRef API for DOI-based papers
- arXiv API for arXiv papers
- bioRxiv/medRxiv API for preprints

Usage:
    python extract_abstracts.py [--input papers/metadata.json] [--output data/papers_with_abstracts.json]
"""

import argparse
import json
import re
import time
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, asdict
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET


@dataclass
class PaperWithAbstract:
    """Paper metadata with abstract."""
    id: str
    year: str
    name: str
    url: str
    topics: str
    animal: str
    doi: Optional[str]
    title: Optional[str]
    abstract: Optional[str]
    authors: Optional[str]
    source: str  # 'crossref', 'arxiv', 'biorxiv', 'manual', 'not_found'


def extract_arxiv_id(url: str, doi: Optional[str]) -> Optional[str]:
    """Extract arXiv ID from URL or DOI."""
    # From DOI like "arXiv:2509.12193"
    if doi and doi.startswith("arXiv:"):
        return doi.replace("arXiv:", "")

    # From URL like "https://arxiv.org/abs/2509.12193" or "https://arxiv.org/pdf/2509.12193"
    patterns = [
        r"arxiv\.org/abs/(\d+\.\d+)",
        r"arxiv\.org/pdf/(\d+\.\d+)",
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None


def extract_biorxiv_doi(url: str, doi: Optional[str]) -> Optional[str]:
    """Extract bioRxiv/medRxiv DOI from URL."""
    if doi and doi.startswith("10.1101/"):
        return doi

    # From URL like "https://www.biorxiv.org/content/10.1101/2025.08.12.669927v1"
    match = re.search(r"10\.1101/[\d.]+", url)
    if match:
        return match.group(0)
    return None


def fetch_arxiv_metadata(arxiv_id: str) -> Optional[dict]:
    """Fetch paper metadata from arXiv API."""
    url = f"http://export.arxiv.org/api/query?id_list={arxiv_id}"

    try:
        with urllib.request.urlopen(url, timeout=30) as response:
            xml_data = response.read().decode('utf-8')

        # Parse XML
        root = ET.fromstring(xml_data)
        ns = {'atom': 'http://www.w3.org/2005/Atom'}

        entry = root.find('atom:entry', ns)
        if entry is None:
            return None

        title_elem = entry.find('atom:title', ns)
        summary_elem = entry.find('atom:summary', ns)

        # Get authors
        authors = []
        for author in entry.findall('atom:author', ns):
            name = author.find('atom:name', ns)
            if name is not None:
                authors.append(name.text)

        return {
            'title': title_elem.text.strip().replace('\n', ' ') if title_elem is not None else None,
            'abstract': summary_elem.text.strip().replace('\n', ' ') if summary_elem is not None else None,
            'authors': ', '.join(authors) if authors else None,
        }
    except Exception as e:
        print(f"  arXiv API error for {arxiv_id}: {e}")
        return None


def fetch_crossref_metadata(doi: str) -> Optional[dict]:
    """Fetch paper metadata from CrossRef API."""
    # Clean DOI
    doi = doi.strip()
    if not doi.startswith("10."):
        return None

    url = f"https://api.crossref.org/works/{urllib.parse.quote(doi, safe='')}"
    headers = {'User-Agent': 'ComputationalPrimatologyBot/1.0 (mailto:research@example.com)'}

    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=30) as response:
            data = json.loads(response.read().decode('utf-8'))

        work = data.get('message', {})

        # Get title
        title = work.get('title', [None])[0]

        # Get abstract
        abstract = work.get('abstract')
        if abstract:
            # Remove JATS XML tags
            abstract = re.sub(r'<[^>]+>', '', abstract).strip()

        # Get authors
        authors = []
        for author in work.get('author', []):
            given = author.get('given', '')
            family = author.get('family', '')
            if family:
                authors.append(f"{given} {family}".strip())

        return {
            'title': title,
            'abstract': abstract,
            'authors': ', '.join(authors) if authors else None,
        }
    except urllib.error.HTTPError as e:
        if e.code == 404:
            print(f"  CrossRef: DOI not found: {doi}")
        else:
            print(f"  CrossRef API error for {doi}: {e}")
        return None
    except Exception as e:
        print(f"  CrossRef API error for {doi}: {e}")
        return None


def fetch_biorxiv_metadata(doi: str) -> Optional[dict]:
    """Fetch paper metadata from bioRxiv/medRxiv API."""
    # bioRxiv API: https://api.biorxiv.org/details/biorxiv/{doi}
    url = f"https://api.biorxiv.org/details/biorxiv/{doi}"

    try:
        with urllib.request.urlopen(url, timeout=30) as response:
            data = json.loads(response.read().decode('utf-8'))

        collection = data.get('collection', [])
        if not collection:
            # Try medRxiv
            url = f"https://api.biorxiv.org/details/medrxiv/{doi}"
            with urllib.request.urlopen(url, timeout=30) as response:
                data = json.loads(response.read().decode('utf-8'))
            collection = data.get('collection', [])

        if not collection:
            return None

        # Get latest version
        paper = collection[-1]

        return {
            'title': paper.get('title'),
            'abstract': paper.get('abstract'),
            'authors': paper.get('authors'),
        }
    except Exception as e:
        print(f"  bioRxiv API error for {doi}: {e}")
        return None


def clean_proxy_url(url: str) -> str:
    """Remove university proxy from URLs.

    Handles patterns like:
    - https://ieeexplore-ieee-org.proxy.library.upenn.edu/path
      -> https://ieeexplore.ieee.org/path
    - https://www-tandfonline-com.proxy.library.upenn.edu/path
      -> https://www.tandfonline.com/path
    """
    # Pattern: domain-with-hyphens.proxy.library.X.edu
    proxy_match = re.match(r'https?://([^.]+)\.proxy\.library\.[^/]+(/.*)?$', url)
    if proxy_match:
        hyphenated_domain = proxy_match.group(1)
        path = proxy_match.group(2) or ''
        # Convert hyphens to dots in domain
        real_domain = hyphenated_domain.replace('-', '.')
        return f'https://{real_domain}{path}'

    # Pattern: domain-with-hyphens-com.proxy.X.edu
    proxy_match2 = re.match(r'https?://([^.]+)\.proxy\.[^/]+(/.*)?$', url)
    if proxy_match2:
        hyphenated_domain = proxy_match2.group(1)
        path = proxy_match2.group(2) or ''
        real_domain = hyphenated_domain.replace('-', '.')
        return f'https://{real_domain}{path}'

    return url


def process_paper(paper: dict, idx: int) -> PaperWithAbstract:
    """Process a single paper and fetch its metadata."""
    url = clean_proxy_url(paper.get('url', ''))
    doi = paper.get('doi')
    name = paper.get('name', '')  # Original name from README - keep this as title

    print(f"[{idx}] Processing: {name}")

    # Create base paper - use 'name' from README as the authoritative title
    result = PaperWithAbstract(
        id=f"paper_{idx}",
        year=paper.get('year', ''),
        name=name,
        url=url,
        topics=paper.get('topics', ''),
        animal=paper.get('animal', ''),
        doi=doi,
        title=name,  # Use name from README as title (it's correct)
        abstract=None,
        authors=None,
        source='not_found',
    )

    # Try arXiv first
    arxiv_id = extract_arxiv_id(url, doi)
    if arxiv_id:
        print(f"  Trying arXiv: {arxiv_id}")
        metadata = fetch_arxiv_metadata(arxiv_id)
        if metadata and metadata.get('abstract'):
            # Keep original title from README, only get abstract and authors from API
            result.abstract = metadata['abstract']
            result.authors = metadata['authors']
            result.source = 'arxiv'
            print(f"  Found via arXiv")
            return result
        time.sleep(0.5)  # Rate limiting

    # Try bioRxiv/medRxiv
    biorxiv_doi = extract_biorxiv_doi(url, doi)
    if biorxiv_doi:
        print(f"  Trying bioRxiv: {biorxiv_doi}")
        metadata = fetch_biorxiv_metadata(biorxiv_doi)
        if metadata and metadata.get('abstract'):
            # Keep original title from README, only get abstract and authors from API
            result.abstract = metadata['abstract']
            result.authors = metadata['authors']
            result.source = 'biorxiv'
            print(f"  Found via bioRxiv")
            return result
        time.sleep(0.5)

    # Try CrossRef for DOI-based papers
    if doi and doi.startswith("10."):
        print(f"  Trying CrossRef: {doi}")
        metadata = fetch_crossref_metadata(doi)
        if metadata:
            # Keep original title from README - CrossRef often returns wrong titles
            # Also don't use CrossRef authors - they're often wrong for this dataset
            if metadata.get('abstract'):
                result.abstract = metadata['abstract']
                result.source = 'crossref'
                print(f"  Found via CrossRef")
            # Only use CrossRef authors if we have none and crossref returned something
            # But we skip this since CrossRef metadata is unreliable for many of these papers
            return result
        time.sleep(0.5)

    print(f"  No abstract found")
    return result


def main():
    parser = argparse.ArgumentParser(description='Extract paper abstracts')
    parser.add_argument('--input', '-i', default='papers/metadata.json',
                        help='Input metadata JSON file')
    parser.add_argument('--output', '-o', default='data/papers_with_abstracts.json',
                        help='Output JSON file with abstracts')
    parser.add_argument('--limit', '-l', type=int, default=None,
                        help='Limit number of papers to process (for testing)')
    args = parser.parse_args()

    # Resolve paths
    script_dir = Path(__file__).parent
    repo_root = script_dir.parent.parent

    input_path = repo_root / args.input
    output_path = repo_root / args.output

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Load input metadata
    print(f"Loading papers from {input_path}")
    with open(input_path, 'r') as f:
        papers = json.load(f)

    print(f"Found {len(papers)} papers")

    # Deduplicate by URL (some papers appear multiple times)
    seen_urls = set()
    unique_papers = []
    for paper in papers:
        url = paper.get('url', '')
        if url not in seen_urls:
            seen_urls.add(url)
            unique_papers.append(paper)

    print(f"After deduplication: {len(unique_papers)} unique papers")

    if args.limit:
        unique_papers = unique_papers[:args.limit]
        print(f"Limited to {len(unique_papers)} papers for testing")

    # Process papers
    results = []
    for idx, paper in enumerate(unique_papers, 1):
        result = process_paper(paper, idx)
        results.append(asdict(result))
        time.sleep(0.3)  # Rate limiting between papers

    # Save results
    print(f"\nSaving results to {output_path}")
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)

    # Print summary
    found = sum(1 for r in results if r['abstract'])
    print(f"\nSummary:")
    print(f"  Total papers: {len(results)}")
    print(f"  With abstracts: {found} ({100*found/len(results):.1f}%)")
    print(f"  Sources: {', '.join(set(r['source'] for r in results))}")

    by_source = {}
    for r in results:
        by_source[r['source']] = by_source.get(r['source'], 0) + 1
    for source, count in sorted(by_source.items()):
        print(f"    {source}: {count}")


if __name__ == '__main__':
    main()
