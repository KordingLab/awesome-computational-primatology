# How the AI Paper Chat Works: A Guide for Primatologists

This guide explains how we built an AI-powered chat system that can answer questions about computational primatology papers. It's written for researchers who may want to apply similar tools to their own paper collections.

## Table of Contents
1. [What We Built](#what-we-built)
2. [The Big Picture](#the-big-picture)
3. [Key Concepts Explained Simply](#key-concepts-explained-simply)
4. [The Pipeline Step-by-Step](#the-pipeline-step-by-step)
5. [How a Question Gets Answered](#how-a-question-gets-answered)
6. [Adapting This for Your Own Papers](#adapting-this-for-your-own-papers)
7. [Tools and Requirements](#tools-and-requirements)

---

## What We Built

We created a chat interface where researchers can ask natural language questions like:

- "What methods exist for macaque face recognition?"
- "Which papers have open-source code for pose estimation?"
- "What datasets are available for chimpanzee behavior analysis?"

The system searches through 80+ papers and returns relevant answers with citations.

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│   You: "What's the best method for lemur face recognition?" │
│                                                             │
│   AI: "Based on the papers in my database, LemurFaceID     │
│        (Crouse et al., 2017) is the primary work on lemur  │
│        face recognition. In their Methods section, they    │
│        describe using..."                                   │
│                                                             │
│   Sources: [LemurFaceID (2017)] [Deb et al. (2018)]        │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## The Big Picture

The system has two main parts:

### Part 1: Building the Knowledge Base (done once)

```
┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│  PDFs    │───>│ Extract  │───>│  Split   │───>│ Convert  │
│ (papers) │    │  Text    │    │ (chunk)  │    │ to Math  │
└──────────┘    └──────────┘    └──────────┘    └──────────┘
                                                      │
     "We used a CNN         "We used a CNN..."       │
      architecture..."       (chunk 1)                │
                                                      ▼
                            "Training was done..."   ┌──────────┐
                             (chunk 2)               │ Database │
                                                     │ of paper │
                            "Results showed..."      │ meanings │
                             (chunk 3)               └──────────┘
```

### Part 2: Answering Questions (every time you ask)

```
┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│ Question │───>│ Convert  │───>│  Find    │───>│   AI     │
│          │    │ to Math  │    │ Similar  │    │ Answers  │
└──────────┘    └──────────┘    └──────────┘    └──────────┘
                                     │                │
"How do I track                      │                │
 macaque poses?"                     ▼                ▼
                              ┌────────────┐   ┌────────────┐
                              │ Top 5 most │   │ "Based on  │
                              │ relevant   │──>│ MacaquePose│
                              │ chunks     │   │ (2021)..." │
                              └────────────┘   └────────────┘
```

---

## Key Concepts Explained Simply

### What are "Embeddings"?

Think of embeddings as **GPS coordinates for meaning**. Just as GPS coordinates (latitude, longitude) describe a physical location, embeddings are numbers that describe what a piece of text is "about."

```
Physical World                    Meaning World
─────────────                    ─────────────

  Paris ──────> (48.8, 2.3)       "macaque face" ──> [0.2, 0.8, 0.1, ...]

  London ────> (51.5, -0.1)       "chimp pose" ────> [0.7, 0.2, 0.5, ...]

  NYC ───────> (40.7, -74.0)      "gibbon call" ───> [0.1, 0.3, 0.9, ...]


Cities close on map               Concepts close in meaning
= coordinates similar             = embeddings similar

  Paris ←→ London: close          "macaque face" ←→ "rhesus facial recognition"
  Paris ←→ NYC: far               "macaque face" ←→ "gibbon vocalization"
```

When you ask a question, we convert it to the same kind of coordinates, then find paper chunks with similar coordinates (= similar meaning).

### What is "Chunking"?

Papers are long. If we tried to match your question against entire papers, the matching would be imprecise. Instead, we split papers into smaller pieces called "chunks."

```
┌─────────────────────────────────────────────────────────────┐
│                     FULL PAPER (30 pages)                   │
│                                                             │
│  Abstract | Introduction | Methods | Results | Discussion  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
                            │
                            │ Split by section
                            ▼
┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐
│ Abstract │ │  Intro   │ │ Methods  │ │ Results  │ │  Disc.   │
│  chunk   │ │  chunk   │ │ chunk 1  │ │ chunk 1  │ │  chunk   │
│          │ │          │ │          │ │          │ │          │
│ ~300     │ │ ~300     │ │ Methods  │ │ Results  │ │ ~300     │
│ words    │ │ words    │ │ chunk 2  │ │ chunk 2  │ │ words    │
└──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────┘

Each chunk is small enough to be precisely relevant to a specific question.
```

We also include **references** as chunks, so users can discover foundational methods cited across papers.

### What is "RAG" (Retrieval-Augmented Generation)?

RAG is a technique that combines search with AI. Instead of asking an AI to answer from memory (which can be wrong or outdated), we:

1. **Retrieve** relevant text from our papers
2. **Augment** the AI's prompt with this text
3. Let the AI **Generate** an answer based on the evidence

```
Without RAG (risky):
┌─────────────┐                      ┌─────────────┐
│  Question   │─────────────────────>│     AI      │
└─────────────┘                      │  (guesses)  │
                                     └─────────────┘
                                           │
                                           ▼
                                     "I think maybe..."
                                     (might be wrong!)


With RAG (reliable):
┌─────────────┐      ┌─────────────┐      ┌─────────────┐
│  Question   │─────>│   Search    │─────>│     AI      │
└─────────────┘      │   Papers    │      │ (with proof)│
                     └─────────────┘      └─────────────┘
                           │                    │
                           ▼                    ▼
                    "Here are 5           "According to
                     relevant chunks"      Smith et al..."
                                          (cites sources!)
```

---

## The Pipeline Step-by-Step

Here's what we actually do to build the system:

### Step 1: Download PDFs

```
┌─────────────────────────────────────────────────────────────┐
│                     PDF SOURCES                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  arXiv.org ──────────────> Free preprints                   │
│                            (19 papers)                      │
│                                                             │
│  bioRxiv.org ────────────> Free preprints                   │
│                            (4 papers)                       │
│                                                             │
│  Semantic Scholar ───────> Finds open-access versions       │
│                            (11 papers)                      │
│                                                             │
│  Unpaywall API ─────────> Legal free versions of            │
│                           paywalled papers (3 papers)       │
│                                                             │
│  Manual download ────────> Papers behind paywalls           │
│                            (need institution access)        │
│                                                             │
└─────────────────────────────────────────────────────────────┘

Total: 42 papers downloaded (53% of collection)
```

### Step 2: Extract Text from PDFs

```
┌─────────────┐          ┌─────────────────────────────────┐
│             │          │ Extracted Text                  │
│   PDF       │  ──────> │                                 │
│   File      │  PyMuPDF │ Page 1: "Abstract: We present..." │
│             │          │ Page 2: "Introduction: Face..."  │
│             │          │ Page 3: "Methods: We trained..." │
└─────────────┘          └─────────────────────────────────┘
```

### Step 3: Detect Sections and Create Chunks

```
Raw Text                              Detected Sections
─────────                             ─────────────────

"Abstract                             ABSTRACT ────────> chunk_001
We present a method...
                                      INTRODUCTION ───> chunk_002
1. Introduction                                         chunk_003
Face recognition in primates...
                                      METHODS ────────> chunk_004
2. Methods                                              chunk_005
2.1 Dataset                                             chunk_006
We collected 10,000 images...
                                      RESULTS ────────> chunk_007
3. Results                                              chunk_008
Our model achieved 95%...
                                      REFERENCES ─────> chunk_009
References                                              chunk_010
[1] Smith et al. 2020..."
```

### Step 4: Generate Embeddings (the "meaning coordinates")

```
Each chunk gets converted to a list of 384 numbers:

chunk_001 (abstract)     ──> [0.23, -0.15, 0.78, ..., 0.42]
chunk_002 (intro)        ──> [0.11, 0.45, -0.33, ..., 0.19]
chunk_003 (methods)      ──> [0.67, 0.22, 0.14, ..., -0.28]
...

These numbers capture meaning:
- Similar concepts = similar numbers
- Different concepts = different numbers

Model used: "all-MiniLM-L6-v2" (free, runs locally)
```

### Step 5: Store Everything in a Searchable Database

```
┌─────────────────────────────────────────────────────────────┐
│                    KNOWLEDGE BASE                           │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  chunks.json (3.3 MB)                                       │
│  ├── 1,849 chunks from 42 papers                            │
│  ├── Each chunk has: text, paper_id, section, metadata      │
│  └── Sections: methods, results, references, etc.           │
│                                                             │
│  chunk_embeddings.json (15 MB)                              │
│  ├── 1,849 embedding vectors                                │
│  └── Each vector: 384 numbers                               │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## How a Question Gets Answered

When you type a question, here's what happens:

```
┌─────────────────────────────────────────────────────────────┐
│ Step 1: Convert your question to an embedding               │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ "What neural networks work best for macaque pose?"          │
│                           │                                 │
│                           ▼                                 │
│         [0.45, 0.23, -0.12, 0.67, ..., 0.33]               │
│                                                             │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ Step 2: Find chunks with similar embeddings                 │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Compare question embedding to all 1,849 chunk embeddings   │
│                                                             │
│  Similarity scores:                                         │
│    MacaquePose methods chunk    ──> 0.89 (very similar!)    │
│    OpenMonkeyStudio results     ──> 0.84                    │
│    SIPEC methods chunk          ──> 0.81                    │
│    LemurFaceID abstract         ──> 0.23 (not relevant)     │
│                                                             │
│  Return top 10 chunks                                       │
│                                                             │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ Step 3: Give chunks to AI with instructions                 │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  "You are an expert on computational primatology.           │
│   Answer based ONLY on these paper excerpts:                │
│                                                             │
│   Paper: MacaquePose (2021)                                 │
│   [METHODS] We used a ResNet-50 backbone pretrained...      │
│                                                             │
│   Paper: OpenMonkeyStudio (2020)                            │
│   [RESULTS] Our multi-camera system achieved...             │
│                                                             │
│   User question: What neural networks work best..."         │
│                                                             │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ Step 4: AI generates answer with citations                  │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  "For macaque pose estimation, the Methods section of       │
│   MacaquePose (Labuguen et al., 2021) describes using       │
│   a ResNet-50 backbone. OpenMonkeyStudio (Bala et al.,      │
│   2020) reports that their multi-camera approach..."        │
│                                                             │
│  Sources: [MacaquePose (2021)] [OpenMonkeyStudio (2020)]    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Adapting This for Your Own Papers

Want to build something similar for your own paper collection? Here's a roadmap:

### What You Need

```
┌─────────────────────────────────────────────────────────────┐
│                     REQUIREMENTS                            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. Papers (PDFs)                                           │
│     - At least 20-30 for useful results                     │
│     - Can start smaller to test                             │
│                                                             │
│  2. A computer with Python                                  │
│     - Any modern laptop works                               │
│     - No GPU required for our approach                      │
│                                                             │
│  3. Cloud account (for hosting the chat)                    │
│     - Google Cloud (we used this)                           │
│     - Or: AWS, Azure, Vercel, etc.                          │
│     - Cost: ~$5-10/month for light usage                    │
│                                                             │
│  4. Basic command-line comfort                              │
│     - Or a collaborator who has it                          │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Simplified Steps

```
Step 1: Collect Your PDFs
        └── Put all PDFs in a folder

Step 2: Run Our Scripts
        ├── pdf_extractor.py    (extracts text)
        ├── section_chunker.py  (splits into chunks)
        └── generate_embeddings.py (creates embeddings)

Step 3: Deploy the Backend
        └── Upload to Google Cloud Run (or similar)

Step 4: Add Chat Widget to Your Website
        └── Copy our HTML/JavaScript code
```

### Estimated Effort

| Task | Time | Technical Level |
|------|------|-----------------|
| Collecting PDFs | 2-4 hours | Low |
| Running extraction scripts | 1 hour | Medium |
| Setting up cloud hosting | 2-3 hours | Medium-High |
| Customizing for your field | 2-4 hours | Medium |
| **Total** | **~1-2 days** | |

---

## Tools and Requirements

### Software We Used

| Tool | Purpose | Why We Chose It |
|------|---------|-----------------|
| **PyMuPDF** | Extract text from PDFs | Fast, handles scientific papers well |
| **Sentence-Transformers** | Generate embeddings | Free, runs locally, good quality |
| **FastAPI** | Web server | Python-based, easy to deploy |
| **Google Gemini** | AI for generating answers | Low cost ($0.10/1M tokens) |
| **Google Cloud Run** | Hosting | Serverless, scales automatically |

### File Structure

```
awesome-computational-primatology/
│
├── data/
│   ├── pdfs/                    # Downloaded papers
│   │   ├── arxiv/
│   │   ├── biorxiv/
│   │   └── open_access/
│   ├── extracted/               # Text from each paper
│   ├── chunks.json              # All chunks with metadata
│   └── chunk_embeddings.json    # Embeddings for search
│
├── scripts/rag/
│   ├── pdf_downloader.py        # Download PDFs
│   ├── pdf_extractor.py         # Extract text
│   ├── section_chunker.py       # Split into chunks
│   └── build_chunk_index.py     # Run full pipeline
│
├── backend/
│   ├── main.py                  # Web server
│   ├── prompts.py               # AI instructions
│   └── data/                    # Copy of chunks for server
│
└── docs/
    └── HOW_THE_AI_CHAT_WORKS.md # This file!
```

### Running the Pipeline

```bash
# 1. Download PDFs (what we can get legally)
python scripts/rag/pdf_downloader.py --phase1

# 2. Extract text from PDFs
python scripts/rag/pdf_extractor.py

# 3. Split into chunks (includes references now!)
python scripts/rag/section_chunker.py

# 4. Generate embeddings
python scripts/rag/build_chunk_index.py --embed

# 5. Sync to backend
python scripts/rag/build_chunk_index.py --sync-backend

# Check status anytime:
python scripts/rag/build_chunk_index.py --stats
```

---

## Glossary

| Term | Simple Explanation |
|------|-------------------|
| **Chunk** | A small piece of a paper (e.g., one paragraph from Methods) |
| **Embedding** | Numbers that represent the meaning of text (like GPS for concepts) |
| **RAG** | Retrieval-Augmented Generation: search + AI answering |
| **LLM** | Large Language Model: the AI that writes answers (e.g., GPT, Gemini) |
| **Vector** | A list of numbers (our embeddings are vectors of 384 numbers) |
| **Cosine Similarity** | Math that measures how similar two embeddings are (0=different, 1=identical) |
| **Token** | Roughly a word or word-piece; AI pricing is per token |

---

## Questions?

If you're a primatologist interested in building something similar for your research area, feel free to:

1. Open an issue on our GitHub repository
2. Fork the code and adapt it
3. Reach out to the maintainers

The code is open-source and designed to be adaptable to other paper collections!

---

*Last updated: December 2025*
