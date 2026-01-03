"""
FastAPI backend for Primatology RAG Chat.

Usage:
    uvicorn main:app --reload --port 8080
"""

import asyncio
import hashlib
import json
import os
import time
from collections import defaultdict, OrderedDict
from pathlib import Path
from typing import Optional

import numpy as np
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

# Import prompts
from prompts import SYSTEM_PROMPT, create_rag_prompt

# Initialize FastAPI app
app = FastAPI(
    title="Primatology RAG Chat API",
    description="Chat with papers about computational primatology",
    version="1.0.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://kordinglab.com",
        "https://kordinglab.github.io",
        "http://localhost:8000",
        "http://localhost:3000",
        "http://127.0.0.1:8000",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

# Rate limiting
RATE_LIMIT = 20  # requests per hour per IP
DAILY_LIMIT = 100  # requests per day per IP
GLOBAL_DAILY_LIMIT = 500  # total requests per day across all users (cost protection)
request_counts: dict[str, list[float]] = defaultdict(list)
global_request_times: list[float] = []  # timestamps of all requests today

# Allowed origins (for referer/origin validation)
ALLOWED_ORIGINS = [
    "https://kordinglab.com",
    "https://www.kordinglab.com",
    "https://kordinglab.github.io",
    "http://localhost:8000",
    "http://localhost:3000",
    "http://127.0.0.1:8000",
]

# Embedding cache (LRU-style, max 100 queries)
EMBEDDING_CACHE_SIZE = 100
embedding_cache: OrderedDict[str, list[float]] = OrderedDict()

# Data paths - check both Docker (/app/data) and local dev (../data) locations
_docker_data = Path(__file__).parent / "data"
_local_data = Path(__file__).parent.parent / "data"
DATA_DIR = _docker_data if _docker_data.exists() else _local_data
PAPERS_PATH = DATA_DIR / "papers_with_abstracts.json"
EMBEDDINGS_PATH = DATA_DIR / "embeddings.json"
CHUNKS_PATH = DATA_DIR / "chunks.json"
CHUNK_EMBEDDINGS_PATH = DATA_DIR / "chunk_embeddings.json"

# Global state
papers_data: list[dict] = []
embeddings_data: dict = {}
papers_lookup: dict[str, dict] = {}
dataset_stats: dict = {}

# Chunk-based RAG state
chunks_data: list[dict] = []
chunk_embeddings: dict = {}
chunk_lookup: dict[str, dict] = {}
use_chunks: bool = False  # Flag to use chunk-based search if available

# Keywords that indicate meta/analytical questions about the dataset
META_KEYWORDS = [
    "how many", "statistics", "underrepresented", "gaps", "trends",
    "most common", "least common", "overview", "summary", "distribution",
    "breakdown", "total", "count", "popular", "rare", "missing",
    "what species", "which species", "all papers", "dataset"
]


class ChatRequest(BaseModel):
    question: str
    history: Optional[list[dict]] = None


class ChatResponse(BaseModel):
    answer: str
    sources: list[dict]
    remaining_requests: int


class HealthResponse(BaseModel):
    status: str
    papers_loaded: int
    embeddings_loaded: int


def load_data():
    """Load papers and embeddings on startup."""
    global papers_data, embeddings_data, papers_lookup
    global chunks_data, chunk_embeddings, chunk_lookup, use_chunks

    # Load papers
    if PAPERS_PATH.exists():
        with open(PAPERS_PATH) as f:
            papers_data = json.load(f)
        papers_lookup = {p['id']: p for p in papers_data}
        print(f"Loaded {len(papers_data)} papers")
    else:
        print(f"Warning: Papers file not found at {PAPERS_PATH}")

    # Load embeddings (paper-level, fallback)
    if EMBEDDINGS_PATH.exists():
        with open(EMBEDDINGS_PATH) as f:
            embeddings_data = json.load(f)
        print(f"Loaded embeddings for {len(embeddings_data.get('papers', []))} papers")
    else:
        print(f"Warning: Embeddings file not found at {EMBEDDINGS_PATH}")

    # Load chunks (preferred for better accuracy)
    if CHUNKS_PATH.exists():
        with open(CHUNKS_PATH) as f:
            chunks_file = json.load(f)
            chunks_data = chunks_file.get('chunks', [])
        chunk_lookup = {c['chunk_id']: c for c in chunks_data}
        print(f"Loaded {len(chunks_data)} chunks")

    # Load chunk embeddings
    if CHUNK_EMBEDDINGS_PATH.exists():
        with open(CHUNK_EMBEDDINGS_PATH) as f:
            chunk_embeddings = json.load(f)
        use_chunks = True
        print(f"Loaded {len(chunk_embeddings.get('embeddings', []))} chunk embeddings (using chunk-based search)")
    else:
        print("Chunk embeddings not found, using paper-level search")

    # Compute dataset statistics
    compute_dataset_stats()


def compute_dataset_stats():
    """Compute statistics about the dataset for meta-questions."""
    global dataset_stats

    if not papers_data:
        return

    # Count by species
    species_counts: dict[str, int] = defaultdict(int)
    for p in papers_data:
        animal = p.get('animal', 'Unknown')
        if animal:
            # Handle comma-separated species
            for species in str(animal).split(','):
                species = species.strip()
                if species:
                    species_counts[species] += 1

    # Count by topic
    topic_counts: dict[str, int] = defaultdict(int)
    for p in papers_data:
        topics = p.get('topics', '')
        if topics:
            for topic in str(topics).split(','):
                topic = topic.strip()
                if topic:
                    topic_counts[topic] += 1

    # Count by year
    year_counts: dict[str, int] = defaultdict(int)
    for p in papers_data:
        year = p.get('year')
        if year:
            year_counts[str(year)] += 1

    # Papers with code
    papers_with_code = sum(1 for p in papers_data if p.get('code'))

    # Papers with abstracts
    papers_with_abstracts = sum(1 for p in papers_data if p.get('abstract'))

    # Sort and identify under/over-represented
    sorted_species = sorted(species_counts.items(), key=lambda x: x[1], reverse=True)
    sorted_topics = sorted(topic_counts.items(), key=lambda x: x[1], reverse=True)
    sorted_years = sorted(year_counts.items(), key=lambda x: x[0], reverse=True)

    dataset_stats = {
        "total_papers": len(papers_data),
        "papers_with_code": papers_with_code,
        "papers_with_abstracts": papers_with_abstracts,
        "by_species": dict(sorted_species),
        "by_topic": dict(sorted_topics),
        "by_year": dict(sorted_years),
        "most_studied_species": sorted_species[:5] if sorted_species else [],
        "least_studied_species": sorted_species[-5:] if len(sorted_species) >= 5 else sorted_species,
        "most_common_topics": sorted_topics[:5] if sorted_topics else [],
    }

    print(f"Computed stats: {dataset_stats['total_papers']} papers, "
          f"{len(species_counts)} species, {len(topic_counts)} topics")


def is_meta_question(question: str) -> bool:
    """Check if the question is about the dataset as a whole (meta-question)."""
    q_lower = question.lower()
    return any(kw in q_lower for kw in META_KEYWORDS)


def format_stats_context() -> str:
    """Format dataset statistics as context for meta-questions."""
    if not dataset_stats:
        return ""

    lines = [
        "=== DATASET STATISTICS ===",
        f"Total papers in database: {dataset_stats['total_papers']}",
        f"Papers with source code available: {dataset_stats['papers_with_code']}",
        f"Papers with abstracts: {dataset_stats['papers_with_abstracts']}",
        "",
        "Papers by species (most to least studied):",
    ]

    for species, count in dataset_stats['by_species'].items():
        lines.append(f"  - {species}: {count} papers")

    lines.append("")
    lines.append("Papers by topic:")
    for topic, count in dataset_stats['by_topic'].items():
        lines.append(f"  - {topic}: {count} papers")

    lines.append("")
    lines.append("Papers by year:")
    for year, count in list(dataset_stats['by_year'].items())[:10]:
        lines.append(f"  - {year}: {count} papers")

    return "\n".join(lines)


def get_client_ip(request: Request) -> str:
    """Get client IP from request headers."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def validate_origin(request: Request) -> bool:
    """Validate request origin/referer to prevent unauthorized API access."""
    # Check Origin header first (set by browsers for CORS requests)
    origin = request.headers.get("Origin", "")
    if origin and any(origin.startswith(allowed) for allowed in ALLOWED_ORIGINS):
        return True

    # Fall back to Referer header
    referer = request.headers.get("Referer", "")
    if referer and any(referer.startswith(allowed) for allowed in ALLOWED_ORIGINS):
        return True

    # Allow requests with no origin/referer in development (curl, etc.)
    # In production, you might want to be stricter
    if not origin and not referer:
        # Check if it's a local/development request
        client_ip = get_client_ip(request)
        if client_ip in ("127.0.0.1", "::1", "localhost"):
            return True

    return False


def check_rate_limit(ip: str) -> tuple[bool, int, str]:
    """Check if IP is within rate limits. Returns (allowed, remaining, reason)."""
    global global_request_times

    now = time.time()
    hour_ago = now - 3600
    day_ago = now - 86400

    # Clean old global entries
    global_request_times = [t for t in global_request_times if t > day_ago]

    # Check global daily limit first (cost protection)
    if len(global_request_times) >= GLOBAL_DAILY_LIMIT:
        return False, 0, "global_limit"

    # Clean old entries for this IP
    request_counts[ip] = [t for t in request_counts[ip] if t > day_ago]

    # Count requests for this IP
    hourly = sum(1 for t in request_counts[ip] if t > hour_ago)
    daily = len(request_counts[ip])

    if hourly >= RATE_LIMIT:
        return False, 0, "hourly_limit"
    if daily >= DAILY_LIMIT:
        return False, 0, "daily_limit"

    return True, min(RATE_LIMIT - hourly, DAILY_LIMIT - daily), "ok"


def cosine_similarity(a: list[float], b: list[float]) -> float:
    """Compute cosine similarity between two vectors."""
    a = np.array(a)
    b = np.array(b)
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))


def get_query_embedding(query: str) -> list[float]:
    """Get embedding for a query with LRU caching."""
    global embedding_cache

    # Normalize query for cache key
    cache_key = hashlib.md5(query.lower().strip().encode()).hexdigest()

    # Check cache first
    if cache_key in embedding_cache:
        # Move to end (most recently used)
        embedding_cache.move_to_end(cache_key)
        return embedding_cache[cache_key]

    # Generate new embedding
    try:
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer('all-MiniLM-L6-v2')
        embedding = model.encode([query])[0].tolist()

        # Add to cache
        embedding_cache[cache_key] = embedding

        # Evict oldest if cache is full
        while len(embedding_cache) > EMBEDDING_CACHE_SIZE:
            embedding_cache.popitem(last=False)

        return embedding
    except Exception as e:
        print(f"Error generating embedding: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate query embedding")


def search_papers(query: str, top_k: int = 5) -> list[dict]:
    """Search for relevant papers using vector similarity."""
    if not embeddings_data.get('papers'):
        return []

    # Get query embedding
    query_embedding = get_query_embedding(query)

    # Calculate similarities
    similarities = []
    for paper_emb in embeddings_data['papers']:
        paper_id = paper_emb['id']
        embedding = paper_emb['embedding']
        similarity = cosine_similarity(query_embedding, embedding)
        similarities.append((paper_id, similarity))

    # Sort by similarity
    similarities.sort(key=lambda x: x[1], reverse=True)

    # Get top-k papers
    results = []
    for paper_id, score in similarities[:top_k]:
        paper = papers_lookup.get(paper_id)
        if paper:
            results.append({
                **paper,
                'relevance_score': score
            })

    return results


def search_chunks(query: str, top_k: int = 6, max_per_paper: int = 2) -> list[dict]:
    """Search for relevant chunks using vector similarity.

    Args:
        query: Search query
        top_k: Maximum chunks to return
        max_per_paper: Maximum chunks per paper (for diversity)
    """
    if not chunk_embeddings.get('embeddings'):
        return []

    # Get query embedding
    query_embedding = get_query_embedding(query)

    # Calculate similarities
    similarities = []
    for emb_data in chunk_embeddings['embeddings']:
        chunk_id = emb_data['chunk_id']
        embedding = emb_data['embedding']
        similarity = cosine_similarity(query_embedding, embedding)
        similarities.append((chunk_id, emb_data['paper_id'], similarity))

    # Sort by similarity
    similarities.sort(key=lambda x: x[2], reverse=True)

    # Get top chunks with diversity (max N per paper)
    results = []
    paper_counts: dict[str, int] = defaultdict(int)

    for chunk_id, paper_id, score in similarities:
        if paper_counts[paper_id] >= max_per_paper:
            continue

        chunk = chunk_lookup.get(chunk_id)
        if chunk:
            results.append({
                **chunk,
                'relevance_score': score
            })
            paper_counts[paper_id] += 1

        if len(results) >= top_k:
            break

    return results


def format_chunk_context(chunks: list[dict]) -> str:
    """Format chunks as context for the LLM, grouped by paper."""
    # Group by paper
    by_paper: dict[str, list[dict]] = defaultdict(list)
    for chunk in chunks:
        by_paper[chunk['paper_id']].append(chunk)

    context_parts = []
    for paper_id, paper_chunks in by_paper.items():
        meta = paper_chunks[0].get('metadata', {})
        parts = [
            f"Paper: {meta.get('title', 'Unknown')} ({meta.get('year', '')})",
            f"Authors: {meta.get('authors', 'Unknown')}",
        ]
        if meta.get('animal'):
            parts.append(f"Species: {meta['animal']}")
        if meta.get('topics'):
            parts.append(f"Topics: {meta['topics']}")

        # Add sections
        for chunk in paper_chunks:
            section = chunk.get('section', 'body').upper()
            text = chunk.get('text', '')
            parts.append(f"\n[{section}]\n{text}")

        context_parts.append('\n'.join(parts))

    return '\n\n---\n\n'.join(context_parts)


def format_context(papers: list[dict]) -> str:
    """Format papers as context for the LLM."""
    context_parts = []
    for i, paper in enumerate(papers, 1):
        parts = [f"Paper {i}: {paper.get('title') or paper.get('name')} ({paper.get('year')})"]

        if paper.get('authors'):
            parts.append(f"Authors: {paper['authors']}")

        if paper.get('topics'):
            parts.append(f"Topics: {paper['topics']}")

        if paper.get('animal'):
            parts.append(f"Species: {paper['animal']}")

        if paper.get('abstract'):
            parts.append(f"Abstract: {paper['abstract']}")

        if paper.get('url'):
            parts.append(f"URL: {paper['url']}")

        context_parts.append('\n'.join(parts))

    return '\n\n---\n\n'.join(context_parts)


def generate_response(question: str, context: str, history: list[dict] | None = None, is_meta: bool = False) -> str:
    """Generate response using Gemini or local model."""
    # Try Vertex AI first
    project_id = os.environ.get('PROJECT_ID') or os.environ.get('GOOGLE_CLOUD_PROJECT')

    if project_id:
        try:
            import vertexai
            from vertexai.generative_models import GenerativeModel

            vertexai.init(project=project_id, location="us-central1")
            model = GenerativeModel("gemini-2.0-flash-lite")

            # Create prompt
            messages = create_rag_prompt(context, question, history, is_meta=is_meta)

            # Convert to Gemini format
            prompt = messages[0]['content'] + "\n\n"  # System prompt
            for msg in messages[1:]:
                role = "User" if msg['role'] == 'user' else "Assistant"
                prompt += f"{role}: {msg['content']}\n\n"

            response = model.generate_content(prompt)
            return response.text

        except Exception as e:
            print(f"Vertex AI error: {e}")
            # Fall through to local model

    # Fallback: Return a structured response based on context
    # This is for local testing without cloud credentials
    if context.strip():
        return f"""Based on the papers in my database, here's what I found relevant to your question:

{context[:2000]}...

Note: This is a local preview. In production, this would use Gemini for a more natural response."""
    else:
        return "I don't have papers about that in my database. Try asking about topics like face recognition, pose estimation, or behavior analysis in primates."


async def generate_response_stream(question: str, context: str, history: list[dict] | None = None, is_meta: bool = False):
    """Generate streaming response using Gemini."""
    project_id = os.environ.get('PROJECT_ID') or os.environ.get('GOOGLE_CLOUD_PROJECT')

    if project_id:
        try:
            import vertexai
            from vertexai.generative_models import GenerativeModel

            vertexai.init(project=project_id, location="us-central1")
            model = GenerativeModel("gemini-2.0-flash-lite")

            # Create prompt
            messages = create_rag_prompt(context, question, history, is_meta=is_meta)

            # Convert to Gemini format
            prompt = messages[0]['content'] + "\n\n"  # System prompt
            for msg in messages[1:]:
                role = "User" if msg['role'] == 'user' else "Assistant"
                prompt += f"{role}: {msg['content']}\n\n"

            # Stream the response
            response = model.generate_content(prompt, stream=True)
            for chunk in response:
                if chunk.text:
                    yield f"data: {json.dumps({'text': chunk.text})}\n\n"
                    await asyncio.sleep(0)  # Allow other tasks to run

            yield f"data: {json.dumps({'done': True})}\n\n"

        except Exception as e:
            print(f"Vertex AI streaming error: {e}")
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
    else:
        # Fallback for local testing - simulate streaming
        fallback_text = "This is a local preview. In production, this would stream from Gemini."
        for word in fallback_text.split():
            yield f"data: {json.dumps({'text': word + ' '})}\n\n"
            await asyncio.sleep(0.05)
        yield f"data: {json.dumps({'done': True})}\n\n"


@app.on_event("startup")
async def startup_event():
    """Load data on startup."""
    load_data()


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        papers_loaded=len(papers_data),
        embeddings_loaded=len(embeddings_data.get('papers', []))
    )


@app.post("/chat", response_model=ChatResponse)
async def chat(request: Request, chat_request: ChatRequest):
    """Main chat endpoint."""
    global global_request_times

    # Validate origin (anti-scraping measure)
    if not validate_origin(request):
        raise HTTPException(
            status_code=403,
            detail="Unauthorized origin. This API is only accessible from the official website."
        )

    # Check rate limits
    client_ip = get_client_ip(request)
    allowed, remaining, reason = check_rate_limit(client_ip)

    if not allowed:
        if reason == "global_limit":
            raise HTTPException(
                status_code=503,
                detail="Daily limit reached. The service will reset at midnight UTC. Please try again tomorrow."
            )
        else:
            raise HTTPException(
                status_code=429,
                detail="Rate limit exceeded. Please try again later."
            )

    # Record this request (both per-IP and global)
    now = time.time()
    request_counts[client_ip].append(now)
    global_request_times.append(now)

    # Check if this is a meta-question about the dataset
    meta_question = is_meta_question(chat_request.question)

    # Search for relevant content (chunks or papers)
    if use_chunks and not meta_question:
        # Use chunk-based search for better accuracy
        relevant_chunks = search_chunks(chat_request.question, top_k=6, max_per_paper=2)
        context = format_chunk_context(relevant_chunks)
        # Extract paper info for sources
        seen_papers = set()
        relevant_papers = []
        for chunk in relevant_chunks:
            paper_id = chunk['paper_id']
            if paper_id not in seen_papers:
                seen_papers.add(paper_id)
                meta = chunk.get('metadata', {})
                relevant_papers.append({
                    'id': paper_id,
                    'title': meta.get('title'),
                    'name': meta.get('title'),
                    'year': meta.get('year'),
                    'authors': meta.get('authors'),
                    'url': meta.get('url'),
                    'relevance_score': chunk.get('relevance_score', 0)
                })
    else:
        # Fallback to paper-level search
        relevant_papers = search_papers(chat_request.question, top_k=5)
        context = format_context(relevant_papers)

    # For meta-questions, include stats
    if meta_question:
        stats_context = format_stats_context()
        context = f"{stats_context}\n\n=== SAMPLE RELEVANT PAPERS ===\n\n{context}"

    # Generate response
    answer = generate_response(
        chat_request.question,
        context,
        chat_request.history,
        is_meta=meta_question
    )

    # Prepare sources
    sources = [
        {
            "title": p.get('title') or p.get('name'),
            "year": p.get('year'),
            "authors": p.get('authors'),
            "url": p.get('url'),
            "relevance": round(p.get('relevance_score', 0), 3)
        }
        for p in relevant_papers
    ]

    return ChatResponse(
        answer=answer,
        sources=sources,
        remaining_requests=remaining - 1
    )


@app.post("/chat/stream")
async def chat_stream(request: Request, chat_request: ChatRequest):
    """Streaming chat endpoint using Server-Sent Events."""
    global global_request_times

    # Validate origin (anti-scraping measure)
    if not validate_origin(request):
        raise HTTPException(
            status_code=403,
            detail="Unauthorized origin."
        )

    # Check rate limits
    client_ip = get_client_ip(request)
    allowed, remaining, reason = check_rate_limit(client_ip)

    if not allowed:
        if reason == "global_limit":
            raise HTTPException(status_code=503, detail="Daily limit reached.")
        else:
            raise HTTPException(status_code=429, detail="Rate limit exceeded.")

    # Record this request
    now = time.time()
    request_counts[client_ip].append(now)
    global_request_times.append(now)

    # Check if meta-question
    meta_question = is_meta_question(chat_request.question)

    # Search for relevant content
    if use_chunks and not meta_question:
        relevant_chunks = search_chunks(chat_request.question, top_k=6, max_per_paper=2)
        context = format_chunk_context(relevant_chunks)
        seen_papers = set()
        relevant_papers = []
        for chunk in relevant_chunks:
            paper_id = chunk['paper_id']
            if paper_id not in seen_papers:
                seen_papers.add(paper_id)
                meta = chunk.get('metadata', {})
                relevant_papers.append({
                    'title': meta.get('title'),
                    'year': meta.get('year'),
                    'url': meta.get('url'),
                })
    else:
        relevant_papers = search_papers(chat_request.question, top_k=5)
        context = format_context(relevant_papers)

    if meta_question:
        stats_context = format_stats_context()
        context = f"{stats_context}\n\n=== SAMPLE RELEVANT PAPERS ===\n\n{context}"

    # Prepare sources to send at the start
    sources = [
        {"title": p.get('title'), "year": p.get('year'), "url": p.get('url')}
        for p in relevant_papers[:3]
    ]

    async def event_stream():
        # Send sources first
        yield f"data: {json.dumps({'sources': sources})}\n\n"

        # Stream the response
        async for chunk in generate_response_stream(
            chat_request.question, context, chat_request.history, is_meta=meta_question
        ):
            yield chunk

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )


@app.get("/papers")
async def list_papers():
    """List all papers (for debugging)."""
    return {
        "count": len(papers_data),
        "papers": [
            {
                "id": p.get('id'),
                "name": p.get('name'),
                "title": p.get('title'),
                "year": p.get('year'),
                "topics": p.get('topics'),
                "has_abstract": bool(p.get('abstract'))
            }
            for p in papers_data
        ]
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
