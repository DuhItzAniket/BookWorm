# Evaluation: what has and has not been measured

[results.json](results.json) records an actual CPU run of the pinned BERT checkpoint over [six synthetic sanity cases](sanity.json): four answerable facts and two unanswerable questions. All six achieved normalized exact match and token F1 of 1.0 in that run. The report also includes per-case latency and model load time.

**This is a tiny sanity check, not a benchmark, held-out study, or claim of 100% real-world accuracy.** Each case supplies its own context. It does not evaluate retrieval across a book, difficult paraphrases, OCR accuracy, or live web search. The “no_overlap” case name is historical: stopword overlap can still enter retrieval; its expected outcome is abstention.

Run from `backend/`:

```bash
python -m scripts.evaluate --dataset ../docs/evaluation/sanity.json --output ../docs/evaluation/results.json
```

The script loads the real reader. It reports the maximum normalized exact match and token F1 across accepted gold answers. Normalization lowercases text, removes punctuation and English articles, and collapses whitespace. Abstention is represented as an empty prediction. The first load may include network/cache work; later latency is not a cloud performance estimate.

## Required academic study

1. Collect legally usable passages/documents with answer spans and page labels. Include answerable and unanswerable questions, simple facts, paraphrases and confusing near-matches.
2. Split by document into development and held-out test sets; deduplicate related versions. Tune chunk length, top-k and rejection threshold on development data only.
3. Measure retrieval recall@k with page/chunk gold labels, then end-to-end EM/F1, no-answer precision/recall, latency percentiles and memory. Report sample counts, hardware, versions and model revision.
4. Compare TF-IDF against a dense retriever, then BERT/RoBERTa/ALBERT readers with retrieval held fixed. Treat T5 generation as a separate condition and assess grounding.
5. For Glypharis, measure CER/WER and QA degradation on the same clean/scanned documents, with low-quality and multi-column subsets. Separate recognition mistakes from retrieval/reader mistakes. Real OCR testing waits for its release.
6. Retain errors, not just successful examples, and report uncertainty for a sufficiently sized held-out set.

Use [demo.txt](demo.txt) for a quick browser presentation. The fictional Riverbank Library facts are synthetic and do not describe an actual institution.
