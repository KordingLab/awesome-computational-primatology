#!/usr/bin/env python3
"""
PDF Text Extractor for Computational Primatology Papers.

Extracts text from PDFs using PyMuPDF, with section detection.

Usage:
    python pdf_extractor.py                    # Extract all PDFs
    python pdf_extractor.py --paper paper_2    # Extract specific paper
"""

import argparse
import json
import re
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Optional

import fitz  # PyMuPDF

# Paths
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
PDFS_DIR = DATA_DIR / "pdfs"
EXTRACTED_DIR = DATA_DIR / "extracted"
PAPERS_FILE = DATA_DIR / "papers_with_abstracts.json"


@dataclass
class ExtractedSection:
    """A section extracted from a PDF."""
    name: str
    text: str
    page_start: int
    page_end: int
    confidence: float = 1.0


@dataclass
class ExtractedDocument:
    """Full extracted document."""
    paper_id: str
    pdf_path: str
    extraction_method: str = "pymupdf"
    extraction_date: str = ""
    total_pages: int = 0
    total_chars: int = 0
    sections: list = field(default_factory=list)
    raw_text: str = ""
    is_scanned: bool = False
    error: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "paper_id": self.paper_id,
            "pdf_path": self.pdf_path,
            "extraction_method": self.extraction_method,
            "extraction_date": self.extraction_date,
            "total_pages": self.total_pages,
            "total_chars": self.total_chars,
            "sections": [asdict(s) if isinstance(s, ExtractedSection) else s for s in self.sections],
            "raw_text": self.raw_text,
            "is_scanned": self.is_scanned,
            "error": self.error
        }


# Section detection patterns (case-insensitive)
SECTION_PATTERNS = {
    'abstract': [
        r'^abstract\s*$',
        r'^abstract\s*[:\.]',
        r'^\d+\.?\s*abstract\b',
    ],
    'introduction': [
        r'^introduction\s*$',
        r'^\d+\.?\s*introduction\b',
        r'^1\.?\s+introduction\b',
    ],
    'related_work': [
        r'^related\s+work\b',
        r'^\d+\.?\s*related\s+work\b',
        r'^background\b',
        r'^literature\s+review\b',
    ],
    'methods': [
        r'^methods?\s*$',
        r'^materials?\s*(and|&)\s*methods?\b',
        r'^\d+\.?\s*methods?\b',
        r'^experimental\s+(setup|procedures?|methods?)\b',
        r'^methodology\b',
    ],
    'results': [
        r'^results?\s*$',
        r'^\d+\.?\s*results?\b',
        r'^results?\s*(and|&)\s*discussion\b',
        r'^experiments?\b',
    ],
    'discussion': [
        r'^discussion\s*$',
        r'^\d+\.?\s*discussion\b',
        r'^discussion\s*(and|&)\s*conclusions?\b',
    ],
    'conclusion': [
        r'^conclusions?\s*$',
        r'^\d+\.?\s*conclusions?\b',
        r'^summary\s*(and|&)?\s*conclusions?\b',
    ],
    'acknowledgments': [
        r'^acknowledgm?ents?\s*$',
    ],
    'references': [
        r'^references?\s*$',
        r'^bibliography\s*$',
        r'^literature\s+cited\b',
    ],
    'appendix': [
        r'^appendix\b',
        r'^supplementary\b',
        r'^supporting\s+information\b',
    ],
}


def detect_section(line: str) -> Optional[tuple[str, float]]:
    """
    Detect if a line is a section header.

    Returns: (section_name, confidence) or None
    """
    line_clean = line.strip()

    # Skip very short or very long lines
    if len(line_clean) < 3 or len(line_clean) > 100:
        return None

    # Skip lines that are likely not headers
    if line_clean.endswith('.') and not line_clean.endswith('..'):
        # Sentences usually end with periods, headers don't
        if len(line_clean) > 50:
            return None

    for section_name, patterns in SECTION_PATTERNS.items():
        for pattern in patterns:
            if re.match(pattern, line_clean, re.IGNORECASE):
                return (section_name, 0.9)

    return None


def is_scanned_pdf(doc: fitz.Document) -> bool:
    """
    Check if a PDF is scanned (image-based with little text).

    Heuristic: If average text per page is very low, likely scanned.
    """
    if doc.page_count == 0:
        return True

    total_text_len = 0
    sample_pages = min(5, doc.page_count)

    for i in range(sample_pages):
        page = doc[i]
        text = page.get_text()
        total_text_len += len(text)

    avg_chars_per_page = total_text_len / sample_pages

    # Scientific papers typically have 3000+ chars per page
    # Scanned PDFs with OCR issues might have <500
    return avg_chars_per_page < 500


def extract_text_with_pages(doc: fitz.Document) -> list[tuple[int, str]]:
    """
    Extract text from each page.

    Returns: List of (page_number, text) tuples
    """
    pages = []
    for page_num in range(doc.page_count):
        page = doc[page_num]
        text = page.get_text("text")
        pages.append((page_num + 1, text))  # 1-indexed
    return pages


def extract_sections(pages: list[tuple[int, str]]) -> list[ExtractedSection]:
    """
    Extract sections from page text.

    Uses regex patterns to detect section headers and split text.
    """
    sections = []
    current_section = None
    current_text = []
    current_page_start = 1

    for page_num, page_text in pages:
        lines = page_text.split('\n')

        for line in lines:
            section_match = detect_section(line)

            if section_match:
                # Save previous section
                if current_section and current_text:
                    sections.append(ExtractedSection(
                        name=current_section,
                        text='\n'.join(current_text).strip(),
                        page_start=current_page_start,
                        page_end=page_num,
                        confidence=0.9
                    ))

                # Start new section
                current_section = section_match[0]
                current_text = []
                current_page_start = page_num
            elif current_section:
                # Add to current section
                current_text.append(line)
            else:
                # Before first detected section - could be title/abstract
                current_text.append(line)

    # Don't forget the last section
    if current_section and current_text:
        sections.append(ExtractedSection(
            name=current_section,
            text='\n'.join(current_text).strip(),
            page_start=current_page_start,
            page_end=pages[-1][0] if pages else 1,
            confidence=0.9
        ))

    # If no sections detected, create a single "body" section
    if not sections and pages:
        all_text = '\n\n'.join(text for _, text in pages)
        sections.append(ExtractedSection(
            name='body',
            text=all_text.strip(),
            page_start=1,
            page_end=pages[-1][0],
            confidence=0.5
        ))

    return sections


def clean_text(text: str) -> str:
    """Clean extracted text."""
    # Remove excessive whitespace
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r' {2,}', ' ', text)

    # Remove common artifacts
    text = re.sub(r'-\n', '', text)  # Hyphenation at line breaks

    return text.strip()


def extract_pdf(pdf_path: Path, paper_id: str) -> ExtractedDocument:
    """
    Extract text and sections from a PDF.

    Args:
        pdf_path: Path to PDF file
        paper_id: Paper ID for reference

    Returns:
        ExtractedDocument with sections and raw text
    """
    doc = ExtractedDocument(
        paper_id=paper_id,
        pdf_path=str(pdf_path),
        extraction_date=datetime.now().isoformat()
    )

    try:
        pdf = fitz.open(pdf_path)
        doc.total_pages = pdf.page_count

        # Check if scanned
        doc.is_scanned = is_scanned_pdf(pdf)
        if doc.is_scanned:
            print(f"  Warning: {paper_id} appears to be a scanned PDF")

        # Extract text by page
        pages = extract_text_with_pages(pdf)

        # Get raw text
        raw_text = '\n\n'.join(text for _, text in pages)
        doc.raw_text = clean_text(raw_text)
        doc.total_chars = len(doc.raw_text)

        # Extract sections
        sections = extract_sections(pages)
        doc.sections = [asdict(s) for s in sections]

        pdf.close()

    except Exception as e:
        doc.error = str(e)
        print(f"  Error extracting {paper_id}: {e}")

    return doc


def find_pdf_for_paper(paper_id: str) -> Optional[Path]:
    """Find the PDF file for a paper ID."""
    for subdir in ['arxiv', 'biorxiv', 'open_access', 'manual']:
        pdf_path = PDFS_DIR / subdir / f"{paper_id}.pdf"
        if pdf_path.exists():
            return pdf_path
    return None


def extract_all_pdfs() -> dict[str, ExtractedDocument]:
    """Extract text from all downloaded PDFs."""
    results = {}

    # Find all PDFs
    pdf_files = list(PDFS_DIR.glob("*/*.pdf"))
    print(f"Found {len(pdf_files)} PDFs to extract\n")

    for pdf_path in sorted(pdf_files):
        paper_id = pdf_path.stem  # e.g., "paper_2" from "paper_2.pdf"
        print(f"Extracting {paper_id}...")

        doc = extract_pdf(pdf_path, paper_id)

        # Save individual extraction
        output_file = EXTRACTED_DIR / f"{paper_id}.json"
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, 'w') as f:
            json.dump(doc.to_dict(), f, indent=2)

        print(f"  -> {doc.total_pages} pages, {doc.total_chars} chars, {len(doc.sections)} sections")

        results[paper_id] = doc

    return results


def main():
    parser = argparse.ArgumentParser(description="Extract text from PDFs")
    parser.add_argument('--paper', type=str, help='Extract specific paper by ID')
    parser.add_argument('--list', action='store_true', help='List available PDFs')
    args = parser.parse_args()

    # Ensure output directory exists
    EXTRACTED_DIR.mkdir(parents=True, exist_ok=True)

    if args.list:
        pdfs = list(PDFS_DIR.glob("*/*.pdf"))
        print(f"Available PDFs ({len(pdfs)}):")
        for pdf in sorted(pdfs):
            print(f"  {pdf.stem}")
        return

    if args.paper:
        pdf_path = find_pdf_for_paper(args.paper)
        if not pdf_path:
            print(f"PDF not found for {args.paper}")
            return

        print(f"Extracting {args.paper}...")
        doc = extract_pdf(pdf_path, args.paper)

        output_file = EXTRACTED_DIR / f"{args.paper}.json"
        with open(output_file, 'w') as f:
            json.dump(doc.to_dict(), f, indent=2)

        print(f"\nExtraction complete:")
        print(f"  Pages: {doc.total_pages}")
        print(f"  Characters: {doc.total_chars}")
        print(f"  Sections: {len(doc.sections)}")
        if doc.sections:
            print(f"  Section names: {[s['name'] for s in doc.sections]}")
        print(f"  Output: {output_file}")
    else:
        # Extract all
        results = extract_all_pdfs()

        # Summary
        print(f"\n{'='*50}")
        print("Extraction Summary")
        print(f"{'='*50}")
        print(f"Total PDFs processed: {len(results)}")

        successful = [r for r in results.values() if not r.error]
        print(f"Successful: {len(successful)}")

        scanned = [r for r in successful if r.is_scanned]
        if scanned:
            print(f"Scanned PDFs (may have issues): {len(scanned)}")

        total_sections = sum(len(r.sections) for r in successful)
        print(f"Total sections extracted: {total_sections}")


if __name__ == "__main__":
    main()
