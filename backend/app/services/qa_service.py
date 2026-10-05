from __future__ import annotations

from dataclasses import dataclass
from threading import Lock
import math

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from app.core.config import settings
from app.services.chunking_service import get_tokenizer


@dataclass
class Passage:
    text: str
    page: int = 1
    title: str = "Document"
    url: str | None = None


def retrieve(question: str, passages: list[Passage], top_k: int = 5):
    if not passages:
        return []
    vectorizer = TfidfVectorizer(strip_accents="unicode", ngram_range=(1, 2), sublinear_tf=True)
    try:
        matrix = vectorizer.fit_transform([p.text for p in passages])
    except ValueError:
        return []
    scores = cosine_similarity(vectorizer.transform([question]), matrix).ravel()
    return [(passages[i], float(scores[i])) for i in np.argsort(-scores, kind="stable")[:top_k]
            if scores[i] > 0]


class BertReader:
    def __init__(self):
        import torch
        from transformers import AutoModelForQuestionAnswering
        self.torch = torch
        self.tokenizer = get_tokenizer()
        if settings.qa_device == "cuda" and not torch.cuda.is_available():
            raise RuntimeError("CUDA was requested but this PyTorch installation cannot access it.")
        self.device = settings.qa_device
        self.model = AutoModelForQuestionAnswering.from_pretrained(
            settings.qa_model_name, use_safetensors=True).to(self.device).eval()
        self.lock = Lock()

    def read(self, question: str, context: str):
        # Sliding windows also cover longer web snippets. Offsets refer to original context.
        encoded = self.tokenizer(question, context, truncation="only_second", max_length=512,
                                 stride=96, return_overflowing_tokens=True,
                                 return_offsets_mapping=True, padding=True, return_tensors="pt")
        offsets = encoded.pop("offset_mapping").tolist()
        encoded.pop("overflow_to_sample_mapping")
        sequence_ids = [encoded.sequence_ids(i) for i in range(len(offsets))]
        with self.lock, self.torch.inference_mode():
            output = self.model(**{k: v.to(self.device) for k, v in encoded.items()})
        best = {"answer": "", "score": 0.0, "start": 0, "end": 0}
        for row, mapping in enumerate(offsets):
            start = output.start_logits[row].cpu().numpy()
            end = output.end_logits[row].cpu().numpy()
            null_score = float(start[0] + end[0])
            valid = [i for i, segment in enumerate(sequence_ids[row])
                     if segment == 1 and mapping[i][1] > mapping[i][0]]
            if not valid:
                continue
            starts = sorted(valid, key=lambda i: float(start[i]), reverse=True)[:20]
            ends = sorted(valid, key=lambda i: float(end[i]), reverse=True)[:20]
            # Confidence is a model score, not a calibrated probability of correctness.
            sprob = self.torch.softmax(output.start_logits[row], dim=-1).cpu().numpy()
            eprob = self.torch.softmax(output.end_logits[row], dim=-1).cpu().numpy()
            for i in starts:
                for j in ends:
                    if j < i or j - i + 1 > 40 or float(start[i] + end[j]) <= null_score:
                        continue
                    score = float(math.sqrt(float(sprob[i]) * float(eprob[j])))
                    if score > best["score"]:
                        a, b = mapping[i][0], mapping[j][1]
                        best = {"answer": context[a:b], "score": score, "start": a, "end": b}
        return best


_reader = None
_reader_lock = Lock()


def get_reader():
    global _reader
    with _reader_lock:
        if _reader is None:
            _reader = BertReader()
        return _reader


def answer_question(question: str, passages: list[Passage], reader=None):
    ranked = retrieve(question, passages, settings.top_k)
    result = {"answer": "I could not find a reliable answer in the available evidence.",
              "no_answer": True, "score": 0.0, "sources": [], "model": settings.qa_model_name}
    if not ranked:
        return result
    reader = reader or get_reader()
    candidates = []
    for passage, similarity in ranked:
        answer = reader.read(question, passage.text)
        # Never return an answer which is not an exact span of its cited passage.
        if (answer["answer"] and answer["score"] >= settings.qa_threshold
                and passage.text[answer["start"]:answer["end"]] == answer["answer"]):
            candidates.append((answer["score"] * (0.8 + 0.2 * similarity), answer, passage, similarity))
    if not candidates:
        return result
    _, best, passage, similarity = max(candidates, key=lambda item: item[0])
    result.update(answer=best["answer"], no_answer=False, score=best["score"], sources=[{
        "title": passage.title, "page": passage.page, "url": passage.url,
        "text": passage.text, "start": best["start"], "end": best["end"],
        "retrieval_score": similarity,
    }])
    return result
