#!/usr/bin/env python3
"""
Section-Based Chunker for Computational Primatology Papers.

Takes extracted PDF text and creates chunks suitable for embedding.
Prioritizes section-based chunking, falls back to fixed-size for unstructured docs.

Usage:
    python section_chunker.py                    # Chunk all extracted docs
    python section_chunker.py --paper paper_2    # Chunk specific paper
"""

import argparse
import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional

# Paths
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
EXTRACTED_DIR = DATA_DIR / "extracted"
PAPERS_FILE = DATA_DIR / "papers_with_abstracts.json"
CHUNKS_FILE = DATA_DIR / "chunks.json"

# Chunking parameters
MAX_CHUNK_SIZE = 1500  # characters (roughly 300-400 tokens)
MIN_CHUNK_SIZE = 200   # Don't create tiny chunks
OVERLAP_SIZE = 100     # Overlap between fixed-size chunks

# Sections to skip (not useful for RAG)
# Note: We now INCLUDE references so users can learn about cited methods
SKIP_SECTIONS = {'acknowledgments', 'appendix'}

# Sections to prioritize (most useful content)
PRIORITY_SECTIONS = {'abstract', 'introduction', 'methods', 'results', 'discussion', 'conclusion'}


@dataclass
class Chunk:
    """A chunk of text for embedding."""
    chunk_id: str
    paper_id: str
    section: str
    text: str
    char_count: int
    metadata: dict

    def to_dict(self) -> dict:
        return asdict(self)


def load_papers_metadata() -> dict[str, dict]:
    """Load paper metadata for enriching chunks."""
    if not PAPERS_FILE.exists():
        return {}

    with open(PAPERS_FILE) as f:
        papers = json.load(f)

    return {p['id']: p for p in papers}


def load_extracted_document(paper_id: str) -> Optional[dict]:
    """Load an extracted document."""
    doc_path = EXTRACTED_DIR / f"{paper_id}.json"
    if not doc_path.exists():
        return None

    with open(doc_path) as f:
        return json.load(f)


def split_text_fixed(text: str, max_size: int = MAX_CHUNK_SIZE,
                     overlap: int = OVERLAP_SIZE) -> list[str]:
    """
    Split text into fixed-size chunks with overlap.

    Tries to split on sentence boundaries when possible.
    """
    if len(text) <= max_size:
        return [text]

    chunks = []
    start = 0

    while start < len(text):
        # Get a chunk
        end = start + max_size

        if end >= len(text):
            # Last chunk
            chunk = text[start:]
            if chunk.strip():
                chunks.append(chunk.strip())
            break

        # Try to find a sentence boundary
        chunk = text[start:end]

        # Look for sentence endings near the end of the chunk
        best_break = -1
        for sep in ['. ', '.\n', '? ', '!\n']:
            pos = chunk.rfind(sep)
            if pos > max_size * 0.5:  # At least halfway through
                best_break = max(best_break, pos + 1)

        if best_break > 0:
            chunk = chunk[:best_break]

        if chunk.strip():
            chunks.append(chunk.strip())

        # Move start with overlap
        start = start + len(chunk) - overlap
        if start < 0:
            start = 0

    return chunks


def chunk_section(section: dict, paper_id: str, metadata: dict,
                  chunk_counter: int) -> tuple[list[Chunk], int]:
    """
    Chunk a single section.

    For sections < MAX_CHUNK_SIZE: keep as single chunk
    For larger sections: split with fixed-size chunking
    """
    section_name = section['name']
    text = section['text'].strip()

    # Skip empty or very short sections
    if len(text) < MIN_CHUNK_SIZE:
        return [], chunk_counter

    # Skip unwanted sections
    if section_name.lower() in SKIP_SECTIONS:
        return [], chunk_counter

    chunks = []

    if len(text) <= MAX_CHUNK_SIZE:
        # Single chunk for this section
        chunk_id = f"{paper_id}_{section_name}_{chunk_counter:03d}"
        chunks.append(Chunk(
            chunk_id=chunk_id,
            paper_id=paper_id,
            section=section_name,
            text=text,
            char_count=len(text),
            metadata=metadata
        ))
        chunk_counter += 1
    else:
        # Split into multiple chunks
        text_chunks = split_text_fixed(text)
        for i, chunk_text in enumerate(text_chunks):
            chunk_id = f"{paper_id}_{section_name}_{chunk_counter:03d}"
            chunks.append(Chunk(
                chunk_id=chunk_id,
                paper_id=paper_id,
                section=section_name,
                text=chunk_text,
                char_count=len(chunk_text),
                metadata=metadata
            ))
            chunk_counter += 1

    return chunks, chunk_counter


def chunk_document(doc: dict, paper_metadata: dict) -> list[Chunk]:
    """
    Chunk an extracted document.

    Strategy:
    1. If sections detected: chunk by section
    2. If only 'body' section: use fixed-size chunking
    """
    paper_id = doc['paper_id']
    sections = doc.get('sections', [])

    # Build metadata for chunks
    metadata = {
        'title': paper_metadata.get('name') or paper_metadata.get('title', 'Unknown'),
        'year': paper_metadata.get('year', ''),
        'authors': paper_metadata.get('authors', ''),
        'animal': paper_metadata.get('animal', ''),
        'topics': paper_metadata.get('topics', ''),
        'url': paper_metadata.get('url', ''),
    }

    chunks = []
    chunk_counter = 0

    # Check if we have real sections or just 'body'
    section_names = [s['name'] for s in sections]
    has_real_sections = any(name in PRIORITY_SECTIONS for name in section_names)

    if has_real_sections:
        # Chunk by section
        for section in sections:
            section_chunks, chunk_counter = chunk_section(
                section, paper_id, metadata, chunk_counter
            )
            chunks.extend(section_chunks)
    else:
        # Fallback: fixed-size chunking on raw text
        raw_text = doc.get('raw_text', '')
        if raw_text:
            text_chunks = split_text_fixed(raw_text)
            for i, chunk_text in enumerate(text_chunks):
                chunk_id = f"{paper_id}_body_{i:03d}"
                chunks.append(Chunk(
                    chunk_id=chunk_id,
                    paper_id=paper_id,
                    section='body',
                    text=chunk_text,
                    char_count=len(chunk_text),
                    metadata=metadata
                ))

    return chunks


def chunk_all_documents() -> list[Chunk]:
    """Chunk all extracted documents."""
    papers_metadata = load_papers_metadata()
    all_chunks = []

    # Find all extracted documents
    extracted_files = list(EXTRACTED_DIR.glob("*.json"))
    print(f"Found {len(extracted_files)} extracted documents\n")

    for doc_path in sorted(extracted_files):
        paper_id = doc_path.stem
        print(f"Chunking {paper_id}...")

        # Load extracted document
        with open(doc_path) as f:
            doc = json.load(f)

        # Get paper metadata
        metadata = papers_metadata.get(paper_id, {'id': paper_id})

        # Chunk the document
        chunks = chunk_document(doc, metadata)

        print(f"  -> {len(chunks)} chunks")
        all_chunks.extend(chunks)

    return all_chunks


def main():
    parser = argparse.ArgumentParser(description="Chunk extracted documents")
    parser.add_argument('--paper', type=str, help='Chunk specific paper by ID')
    parser.add_argument('--stats', action='store_true', help='Show chunking statistics')
    args = parser.parse_args()

    if args.paper:
        # Chunk single paper
        papers_metadata = load_papers_metadata()
        doc = load_extracted_document(args.paper)

        if not doc:
            print(f"Extracted document not found for {args.paper}")
            return

        metadata = papers_metadata.get(args.paper, {'id': args.paper})
        chunks = chunk_document(doc, metadata)

        print(f"\nChunks for {args.paper}:")
        print(f"  Total chunks: {len(chunks)}")
        print(f"  Sections: {set(c.section for c in chunks)}")
        print(f"  Avg chunk size: {sum(c.char_count for c in chunks) / len(chunks):.0f} chars")

        if args.stats:
            print("\n  Chunks by section:")
            from collections import Counter
            section_counts = Counter(c.section for c in chunks)
            for section, count in section_counts.most_common():
                print(f"    {section}: {count}")
    else:
        # Chunk all documents
        all_chunks = chunk_all_documents()

        # Save chunks
        chunks_data = {
            "total_chunks": len(all_chunks),
            "total_papers": len(set(c.paper_id for c in all_chunks)),
            "chunks": [c.to_dict() for c in all_chunks]
        }

        with open(CHUNKS_FILE, 'w') as f:
            json.dump(chunks_data, f, indent=2)

        # Print summary
        print(f"\n{'='*50}")
        print("Chunking Summary")
        print(f"{'='*50}")
        print(f"Total chunks: {len(all_chunks)}")
        print(f"Total papers: {len(set(c.paper_id for c in all_chunks))}")
        print(f"Avg chunks per paper: {len(all_chunks) / len(set(c.paper_id for c in all_chunks)):.1f}")

        # Section distribution
        from collections import Counter
        section_counts = Counter(c.section for c in all_chunks)
        print(f"\nChunks by section:")
        for section, count in section_counts.most_common():
            print(f"  {section}: {count}")

        # Size stats
        sizes = [c.char_count for c in all_chunks]
        print(f"\nChunk sizes:")
        print(f"  Min: {min(sizes)} chars")
        print(f"  Max: {max(sizes)} chars")
        print(f"  Avg: {sum(sizes)/len(sizes):.0f} chars")

        print(f"\nSaved to: {CHUNKS_FILE}")


if __name__ == "__main__":
    main()
