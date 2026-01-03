#!/usr/bin/env python3
"""
Generate embeddings for papers using either local model or Vertex AI.

Usage:
    # Using local model (for testing, no cloud credentials needed)
    python generate_embeddings.py --local

    # Using Vertex AI (requires Google Cloud credentials)
    python generate_embeddings.py --project YOUR_PROJECT_ID
"""

import argparse
import json
from pathlib import Path
from typing import Optional
import numpy as np


def load_papers(input_path: Path) -> list[dict]:
    """Load papers from JSON file."""
    with open(input_path, 'r') as f:
        return json.load(f)


def create_embedding_text(paper: dict) -> str:
    """Create text to embed from paper metadata."""
    parts = []

    # Title or name
    title = paper.get('title') or paper.get('name', '')
    if title:
        parts.append(f"Title: {title}")

    # Authors
    if paper.get('authors'):
        parts.append(f"Authors: {paper['authors']}")

    # Year
    if paper.get('year'):
        parts.append(f"Year: {paper['year']}")

    # Topics
    if paper.get('topics'):
        parts.append(f"Topics: {paper['topics']}")

    # Species/Animal
    if paper.get('animal'):
        parts.append(f"Species: {paper['animal']}")

    # Abstract (most important!)
    if paper.get('abstract'):
        parts.append(f"Abstract: {paper['abstract']}")

    return '\n'.join(parts)


def generate_local_embeddings(texts: list[str]) -> list[list[float]]:
    """Generate embeddings using local sentence-transformers model."""
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError:
        print("Installing sentence-transformers...")
        import subprocess
        subprocess.check_call(['pip', 'install', 'sentence-transformers'])
        from sentence_transformers import SentenceTransformer

    print("Loading local embedding model (all-MiniLM-L6-v2)...")
    model = SentenceTransformer('all-MiniLM-L6-v2')

    print(f"Generating embeddings for {len(texts)} texts...")
    embeddings = model.encode(texts, show_progress_bar=True)

    return embeddings.tolist()


def generate_vertex_embeddings(texts: list[str], project_id: str) -> list[list[float]]:
    """Generate embeddings using Vertex AI."""
    try:
        from google.cloud import aiplatform
        from vertexai.language_models import TextEmbeddingModel
    except ImportError:
        print("Installing google-cloud-aiplatform...")
        import subprocess
        subprocess.check_call(['pip', 'install', 'google-cloud-aiplatform'])
        from google.cloud import aiplatform
        from vertexai.language_models import TextEmbeddingModel

    # Initialize Vertex AI
    aiplatform.init(project=project_id, location="us-central1")

    print("Loading Vertex AI embedding model...")
    model = TextEmbeddingModel.from_pretrained("text-embedding-005")

    embeddings = []
    batch_size = 5  # Vertex AI has limits on batch size

    print(f"Generating embeddings for {len(texts)} texts...")
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        print(f"  Processing batch {i // batch_size + 1}/{(len(texts) + batch_size - 1) // batch_size}")

        # Generate embeddings
        batch_embeddings = model.get_embeddings(batch)
        for emb in batch_embeddings:
            embeddings.append(emb.values)

    return embeddings


def main():
    parser = argparse.ArgumentParser(description='Generate embeddings for papers')
    parser.add_argument('--input', '-i', default='data/papers_with_abstracts.json',
                        help='Input JSON file with papers')
    parser.add_argument('--output', '-o', default='data/embeddings.json',
                        help='Output JSON file with embeddings')
    parser.add_argument('--local', action='store_true',
                        help='Use local model (sentence-transformers) instead of Vertex AI')
    parser.add_argument('--project', '-p', type=str,
                        help='Google Cloud project ID (required for Vertex AI)')
    args = parser.parse_args()

    # Resolve paths
    script_dir = Path(__file__).parent
    repo_root = script_dir.parent.parent

    input_path = repo_root / args.input
    output_path = repo_root / args.output

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Load papers
    print(f"Loading papers from {input_path}")
    papers = load_papers(input_path)
    print(f"Loaded {len(papers)} papers")

    # Create embedding texts
    print("Creating embedding texts...")
    embedding_texts = []
    paper_ids = []
    for paper in papers:
        text = create_embedding_text(paper)
        if text.strip():
            embedding_texts.append(text)
            paper_ids.append(paper['id'])
        else:
            print(f"  Skipping paper {paper['id']} - no text to embed")

    print(f"Will generate embeddings for {len(embedding_texts)} papers")

    # Generate embeddings
    if args.local:
        print("\nUsing LOCAL embedding model (sentence-transformers)")
        embeddings = generate_local_embeddings(embedding_texts)
    else:
        if not args.project:
            print("\nERROR: --project is required for Vertex AI. Use --local for local testing.")
            print("Example: python generate_embeddings.py --project my-gcp-project")
            return
        print(f"\nUsing VERTEX AI embedding model (project: {args.project})")
        embeddings = generate_vertex_embeddings(embedding_texts, args.project)

    # Create output data
    output_data = {
        'model': 'all-MiniLM-L6-v2' if args.local else 'text-embedding-005',
        'dimension': len(embeddings[0]) if embeddings else 0,
        'papers': []
    }

    for paper_id, text, embedding in zip(paper_ids, embedding_texts, embeddings):
        output_data['papers'].append({
            'id': paper_id,
            'text_preview': text[:200] + '...' if len(text) > 200 else text,
            'embedding': embedding
        })

    # Save output
    print(f"\nSaving embeddings to {output_path}")
    with open(output_path, 'w') as f:
        json.dump(output_data, f)

    # Print summary
    print(f"\nSummary:")
    print(f"  Papers embedded: {len(output_data['papers'])}")
    print(f"  Embedding dimension: {output_data['dimension']}")
    print(f"  Model: {output_data['model']}")

    # Calculate file size
    file_size = output_path.stat().st_size / 1024 / 1024
    print(f"  File size: {file_size:.2f} MB")


if __name__ == '__main__':
    main()
