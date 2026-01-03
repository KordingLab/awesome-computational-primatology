#!/usr/bin/env python3
"""
Build Chunk Index - Orchestration script for the PDF RAG pipeline.

Runs the full pipeline: download -> extract -> chunk -> embed

Usage:
    python build_chunk_index.py --all --email your@email.com  # Full pipeline
    python build_chunk_index.py --download-phase1              # Just Phase 1 downloads
    python build_chunk_index.py --download-phase2 --email X    # Just Phase 2 (Unpaywall)
    python build_chunk_index.py --extract                      # Just extraction
    python build_chunk_index.py --chunk                        # Just chunking
    python build_chunk_index.py --embed                        # Just embedding
    python build_chunk_index.py --sync-backend                 # Sync to backend
    python build_chunk_index.py --stats                        # Show pipeline stats
"""

import argparse
import asyncio
import json
import shutil
from pathlib import Path

# Paths
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
BACKEND_DATA_DIR = PROJECT_ROOT / "backend" / "data"
PDFS_DIR = DATA_DIR / "pdfs"
EXTRACTED_DIR = DATA_DIR / "extracted"
CHUNKS_FILE = DATA_DIR / "chunks.json"
CHUNK_EMBEDDINGS_FILE = DATA_DIR / "chunk_embeddings.json"


def print_header(title: str):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")


async def run_download_phase1():
    """Run Phase 1 PDF downloads."""
    print_header("PHASE 1: Direct PDF Downloads")

    from pdf_downloader import PDFDownloader, load_papers

    papers = load_papers()
    print(f"Loaded {len(papers)} papers\n")

    async with PDFDownloader() as downloader:
        stats = await downloader.download_phase1(papers)

    print(f"\nPhase 1 Results:")
    print(f"  Attempted: {stats.attempted}")
    print(f"  Succeeded: {stats.succeeded}")
    print(f"  Failed: {stats.failed}")
    print(f"  Skipped: {stats.skipped}")

    return stats


async def run_download_phase2(email: str):
    """Run Phase 2 Unpaywall downloads."""
    print_header("PHASE 2: Unpaywall API Downloads")

    from pdf_downloader import PDFDownloader, load_papers

    papers = load_papers()

    async with PDFDownloader(email=email) as downloader:
        stats = await downloader.download_phase2(papers)

    print(f"\nPhase 2 Results:")
    print(f"  Attempted: {stats.attempted}")
    print(f"  Succeeded: {stats.succeeded}")
    print(f"  Failed: {stats.failed}")
    print(f"  Skipped: {stats.skipped}")

    return stats


def run_extraction():
    """Run PDF text extraction."""
    print_header("EXTRACTION: PDF Text Extraction")

    from pdf_extractor import extract_all_pdfs

    results = extract_all_pdfs()

    successful = sum(1 for r in results.values() if not r.error)
    print(f"\nExtraction Results:")
    print(f"  Total processed: {len(results)}")
    print(f"  Successful: {successful}")

    return results


def run_chunking():
    """Run document chunking."""
    print_header("CHUNKING: Section-Based Chunking")

    from section_chunker import chunk_all_documents, CHUNKS_FILE

    chunks = chunk_all_documents()

    # Save chunks
    chunks_data = {
        "total_chunks": len(chunks),
        "total_papers": len(set(c.paper_id for c in chunks)),
        "chunks": [c.to_dict() for c in chunks]
    }

    with open(CHUNKS_FILE, 'w') as f:
        json.dump(chunks_data, f, indent=2)

    print(f"\nChunking Results:")
    print(f"  Total chunks: {len(chunks)}")
    print(f"  Total papers: {len(set(c.paper_id for c in chunks))}")

    return chunks


def run_embedding():
    """Generate embeddings for chunks."""
    print_header("EMBEDDING: Generating Chunk Embeddings")

    # Load chunks
    if not CHUNKS_FILE.exists():
        print("Error: chunks.json not found. Run --chunk first.")
        return None

    with open(CHUNKS_FILE) as f:
        chunks_data = json.load(f)

    chunks = chunks_data['chunks']
    print(f"Loaded {len(chunks)} chunks\n")

    # Generate embeddings
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError:
        print("Error: sentence-transformers not installed.")
        print("Run: pip install sentence-transformers")
        return None

    model = SentenceTransformer('all-MiniLM-L6-v2')

    # Create texts with context
    texts = []
    for chunk in chunks:
        meta = chunk['metadata']
        text = (
            f"Title: {meta.get('title', 'Unknown')}\n"
            f"Section: {chunk['section']}\n\n"
            f"{chunk['text']}"
        )
        texts.append(text)

    print(f"Generating embeddings for {len(texts)} chunks...")
    embeddings = model.encode(texts, show_progress_bar=True)

    # Save embeddings
    embeddings_data = {
        "model": "all-MiniLM-L6-v2",
        "dimension": 384,
        "total_embeddings": len(embeddings),
        "embeddings": [
            {
                "chunk_id": chunk['chunk_id'],
                "paper_id": chunk['paper_id'],
                "embedding": emb.tolist()
            }
            for chunk, emb in zip(chunks, embeddings)
        ]
    }

    with open(CHUNK_EMBEDDINGS_FILE, 'w') as f:
        json.dump(embeddings_data, f)

    print(f"\nEmbedding Results:")
    print(f"  Total embeddings: {len(embeddings)}")
    print(f"  Dimension: {embeddings.shape[1]}")
    print(f"  Saved to: {CHUNK_EMBEDDINGS_FILE}")

    return embeddings_data


def sync_to_backend():
    """Sync chunks and embeddings to backend/data/."""
    print_header("SYNC: Copying data to backend")

    BACKEND_DATA_DIR.mkdir(parents=True, exist_ok=True)

    files_to_sync = [
        (CHUNKS_FILE, BACKEND_DATA_DIR / "chunks.json"),
        (CHUNK_EMBEDDINGS_FILE, BACKEND_DATA_DIR / "chunk_embeddings.json"),
    ]

    for src, dst in files_to_sync:
        if src.exists():
            shutil.copy2(src, dst)
            size_mb = src.stat().st_size / (1024 * 1024)
            print(f"  Copied: {src.name} ({size_mb:.2f} MB)")
        else:
            print(f"  Warning: {src.name} not found")

    print(f"\nSync complete to: {BACKEND_DATA_DIR}")


def show_stats():
    """Show pipeline statistics."""
    print_header("PIPELINE STATISTICS")

    # PDFs
    pdf_count = len(list(PDFS_DIR.glob("*/*.pdf")))
    print(f"PDFs downloaded: {pdf_count}")

    by_source = {}
    for subdir in PDFS_DIR.iterdir():
        if subdir.is_dir():
            count = len(list(subdir.glob("*.pdf")))
            if count > 0:
                by_source[subdir.name] = count
    for source, count in sorted(by_source.items()):
        print(f"  - {source}: {count}")

    # Extracted
    extracted_count = len(list(EXTRACTED_DIR.glob("*.json")))
    print(f"\nDocuments extracted: {extracted_count}")

    # Chunks
    if CHUNKS_FILE.exists():
        with open(CHUNKS_FILE) as f:
            chunks_data = json.load(f)
        print(f"\nChunks created: {chunks_data['total_chunks']}")
        print(f"Papers with chunks: {chunks_data['total_papers']}")

        # Section distribution
        from collections import Counter
        sections = Counter(c['section'] for c in chunks_data['chunks'])
        print("By section:")
        for section, count in sections.most_common():
            print(f"  - {section}: {count}")
    else:
        print("\nChunks: Not yet created")

    # Embeddings
    if CHUNK_EMBEDDINGS_FILE.exists():
        with open(CHUNK_EMBEDDINGS_FILE) as f:
            emb_data = json.load(f)
        print(f"\nChunk embeddings: {emb_data['total_embeddings']}")
        print(f"Model: {emb_data['model']}")
        print(f"Dimension: {emb_data['dimension']}")
    else:
        print("\nEmbeddings: Not yet created")

    # Backend sync status
    print(f"\nBackend sync status:")
    for fname in ['chunks.json', 'chunk_embeddings.json']:
        backend_file = BACKEND_DATA_DIR / fname
        data_file = DATA_DIR / fname
        if backend_file.exists() and data_file.exists():
            if backend_file.stat().st_mtime >= data_file.stat().st_mtime:
                print(f"  - {fname}: Synced")
            else:
                print(f"  - {fname}: Out of date")
        elif backend_file.exists():
            print(f"  - {fname}: Backend only")
        elif data_file.exists():
            print(f"  - {fname}: Not synced")
        else:
            print(f"  - {fname}: Not created")


async def run_all(email: str = None):
    """Run the full pipeline."""
    print_header("FULL PIPELINE")

    # Phase 1 downloads
    await run_download_phase1()

    # Phase 2 downloads (if email provided)
    if email:
        await run_download_phase2(email)
    else:
        print("\nSkipping Phase 2 (no email provided)")

    # Extraction
    run_extraction()

    # Chunking
    run_chunking()

    # Embedding
    run_embedding()

    # Sync to backend
    sync_to_backend()

    # Final stats
    show_stats()


def main():
    parser = argparse.ArgumentParser(description="Build chunk index for PDF RAG pipeline")
    parser.add_argument('--all', action='store_true', help='Run full pipeline')
    parser.add_argument('--download-phase1', action='store_true', help='Run Phase 1 downloads')
    parser.add_argument('--download-phase2', action='store_true', help='Run Phase 2 (Unpaywall)')
    parser.add_argument('--extract', action='store_true', help='Run PDF extraction')
    parser.add_argument('--chunk', action='store_true', help='Run chunking')
    parser.add_argument('--embed', action='store_true', help='Run embedding generation')
    parser.add_argument('--sync-backend', action='store_true', help='Sync to backend/data/')
    parser.add_argument('--stats', action='store_true', help='Show pipeline statistics')
    parser.add_argument('--email', type=str, help='Email for Unpaywall API')
    args = parser.parse_args()

    if not any([args.all, args.download_phase1, args.download_phase2,
                args.extract, args.chunk, args.embed, args.sync_backend, args.stats]):
        parser.print_help()
        return

    if args.stats:
        show_stats()
        return

    if args.all:
        asyncio.run(run_all(args.email))
        return

    if args.download_phase1:
        asyncio.run(run_download_phase1())

    if args.download_phase2:
        if not args.email:
            print("Error: --email required for Phase 2")
            return
        asyncio.run(run_download_phase2(args.email))

    if args.extract:
        run_extraction()

    if args.chunk:
        run_chunking()

    if args.embed:
        run_embedding()

    if args.sync_backend:
        sync_to_backend()


if __name__ == "__main__":
    main()
