# 🔍 DocsQA: RAG with an Evaluation Harness

A retrieval-augmented generation (RAG) system that answers questions over documentation **with citations**, and ships with an **evaluation harness** so every change to the pipeline is measured, not guessed.

> **Why this project?** Building a RAG demo is easy. Knowing whether it's *good*, and proving a change made it better, is the hard part. This repo focuses on that.

It runs **fully offline with zero API keys** (lexical embeddings + extractive answers) and upgrades to real semantic search and LLM answers by swapping a config line.

---

## ✨ Features

- **Hybrid retrieval**: dense vectors + BM25 (written from scratch), merged with Reciprocal Rank Fusion
- **Optional cross-encoder reranking** for better top-k precision
- **Grounded answers with citations**: every answer links back to its source chunk
- **Evaluation harness**: Recall@k and MRR on a golden question set, plus optional LLM-as-judge faithfulness
- **Config-driven experiments**: compare chunk sizes, retrieval modes, and models side by side from YAML
- **Tracing**: per-request latency, token usage, and estimated cost
- **CI quality gate**: GitHub Actions fails the build if retrieval recall regresses
- **FastAPI service**, **Streamlit UI**, **Dockerfile**
- Pluggable LLM: Anthropic, OpenAI, or none

---

## 🏗️ Architecture

```
Docs ──▶ Ingest: clean → chunk (overlap) → embed ──▶ Index (numpy + BM25)
                                                         │
Question ──▶ Dense search ─┐                             ▼
                           ├─▶ RRF fusion ─▶ (Reranker) ─▶ LLM + citations ─▶ Answer
             BM25 search ──┘                                   │
                                                               ▼
                                                  Trace: latency / tokens / cost
```

---

## 🚀 Quickstart

```bash
git clone https://github.com/<your-username>/docsqa.git
cd docsqa
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# 1. Build the index from the sample docs in data/docs
python -m docsqa.ingest --config configs/hybrid.yaml

# 2. Ask from the command line
python -c "from docsqa.pipeline import DocsQA; print(DocsQA.from_index('index').ask('What is the default rate limit?')['answer'])"

# 3. Or run the API
uvicorn docsqa.api:app --reload
curl -X POST localhost:8000/ask -H "Content-Type: application/json" \
  -d '{"question": "How do I verify a webhook signature?"}'

# 4. Or the web UI
streamlit run app.py
```

**Use your own docs:** put `.md` / `.txt` files in a folder and run `python -m docsqa.ingest --path ./my_docs`.

**Turn on LLM answers:** `cp .env.example .env`, add `ANTHROPIC_API_KEY` or `OPENAI_API_KEY`, and export it (`export $(cat .env | xargs)`).

**Docker:** `docker compose up --build`

---

## 📊 Evaluation

```bash
# Compare configs side by side
python -m docsqa.eval --config configs/baseline.yaml configs/hybrid.yaml

# Add answer-quality scoring with an LLM judge (needs an API key)
python -m docsqa.eval --config configs/hybrid.yaml --judge
```

A chunk counts as **relevant** if it contains every string in the question's `must_contain` list (see `eval/golden_set.jsonl`). This makes the metric sensitive to chunking choices, since a bad split can cut an answer in half.

### Results

Measured with the offline `hashing` embedder on the 14-question golden set over the bundled sample docs:

| Config | Retrieval | Chunking | Recall@1 | Recall@3 | Recall@5 | MRR |
|--------|-----------|----------|----------|----------|----------|-----|
| baseline | dense | 200 words, no overlap | 0.57 | 1.00 | 1.00 | 0.77 |
| hybrid | dense + BM25 (RRF) | 100 words, 20 overlap | 1.00 | 1.00 | 1.00 | 1.00 |

**Honest caveats**
- These two configs differ in *both* retrieval mode and chunking, so the gain is not attributable to one change. Isolating each change is the next experiment (see below).
- 14 questions over 4 short docs is a small set, and the hashing embedder is lexical. Results on larger corpora with `sentence-transformers` will be lower and more informative.

### Run it yourself with real embeddings

```bash
pip install sentence-transformers
python -m docsqa.eval --config configs/baseline.yaml configs/hybrid.yaml configs/hybrid_rerank.yaml
```

Paste your numbers into the table above.

---

## 🗂️ Project Structure

```
docsqa/
├── docsqa/
│   ├── config.py        # YAML-driven experiment config
│   ├── embeddings.py    # hashing (offline) + sentence-transformers
│   ├── ingest.py        # load, chunk with overlap, embed, save index
│   ├── retrieval.py     # BM25, dense search, Reciprocal Rank Fusion
│   ├── rerank.py        # optional cross-encoder reranker
│   ├── generate.py      # prompts, LLM clients, extractive fallback, citations
│   ├── pipeline.py      # end-to-end retrieve → generate
│   ├── eval.py          # metrics, LLM judge, CLI, CI gate
│   ├── tracing.py       # latency / token / cost tracking
│   └── api.py           # FastAPI service
├── app.py               # Streamlit UI
├── configs/             # baseline / hybrid / hybrid_rerank
├── data/docs/           # sample documentation corpus
├── eval/golden_set.jsonl
├── tests/
├── Dockerfile · docker-compose.yml
└── .github/workflows/ci.yml
```

---

## 🧠 Design Decisions

| Decision | Choice | Reasoning |
|----------|--------|-----------|
| Vector store | In-memory numpy matrix | Cosine search over a few thousand chunks is instant; avoids an external DB until scale requires one |
| BM25 | Implemented from scratch | Dense search misses exact tokens like error codes and function names; BM25 catches them |
| Fusion | Reciprocal Rank Fusion | Needs no score normalization across retrievers |
| Embeddings | Pluggable, offline default | Anyone can clone and run it with no keys or downloads |
| Prompting | "Answer only from context" + cite | Reduces hallucination and makes answers checkable |
| Eval | Golden set + `must_contain` relevance | Fast, deterministic regression testing on every PR |
| CI | `--min-recall` gate | Quality regressions fail the build like any other bug |

---

## 🔭 Next Steps

- [ ] Ablations that change one variable at a time (chunk size, overlap, retrieval mode)
- [ ] Larger golden set with human-written questions
- [ ] Validate the LLM judge against human labels
- [ ] PDF and HTML ingestion
- [ ] Query rewriting for multi-hop questions
- [ ] Swap numpy for pgvector once the corpus outgrows memory

---

## 🧪 Tests

```bash
pip install -r requirements-dev.txt
pytest -q
```

## 🛠️ Tech Stack

Python · NumPy · FastAPI · Streamlit · sentence-transformers (optional) · Anthropic / OpenAI APIs (optional) · Docker · GitHub Actions

## 📄 License

MIT

## 👤 Author

**Your Name** · [LinkedIn](https://linkedin.com/in/your-profile) · [Portfolio](https://your-site.com)
