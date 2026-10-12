"""Run from backend: python -m scripts.evaluate --output ../docs/evaluation/results.json."""
import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import platform
import json
from pathlib import Path
import re
import string
import time
from app.core.config import settings
from app.services.qa_service import Passage, answer_question, get_reader


def normalize(text):
    text = text.lower().translate(str.maketrans("", "", string.punctuation))
    return " ".join(re.sub(r"\b(a|an|the)\b", " ", text).split())


def f1(prediction, gold):
    predicted, expected = normalize(prediction).split(), normalize(gold).split()
    if not predicted or not expected:
        return float(predicted == expected)
    common = sum((Counter(predicted) & Counter(expected)).values())
    return 2 * common / (len(predicted) + len(expected))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", default="../docs/evaluation/sanity.json")
    parser.add_argument("--output", default="../docs/evaluation/results.json")
    args = parser.parse_args()
    dataset = json.loads(Path(args.dataset).read_text(encoding="utf-8-sig"))
    if not dataset or any(not item.get("answers") for item in dataset):
        raise ValueError("Evaluation requires cases with at least one gold answer (empty string for abstention).")
    started = time.perf_counter()
    reader = get_reader()
    load_seconds = time.perf_counter() - started
    rows = []
    for item in dataset:
        started = time.perf_counter()
        result = answer_question(item["question"], [Passage(item["context"])], reader)
        prediction = "" if result["no_answer"] else result["answer"]
        rows.append({"id": item["id"], "question": item["question"], "prediction": prediction,
                     "expected": item["answers"], "no_answer": result["no_answer"],
                     "exact_match": max(float(normalize(prediction) == normalize(gold)) for gold in item["answers"]),
                     "f1": max(f1(prediction, gold) for gold in item["answers"]),
                     "seconds": round(time.perf_counter() - started, 3)})
    report = {"model": settings.qa_model_name, "device": settings.qa_device,
              "model_revision": settings.qa_model_revision,
              "evaluated_at": datetime.now(timezone.utc).isoformat(),
              "python": platform.python_version(),
              "platform": platform.system(),
              "torch": reader.torch.__version__,
              "dataset_sha256": hashlib.sha256(Path(args.dataset).read_bytes()).hexdigest(),
              "notice": "Sanity evaluation, not a benchmark or evidence of general accuracy. Context is supplied; this does not measure book-scale retrieval recall.",
              "model_load_seconds": round(load_seconds, 3), "count": len(rows),
              "exact_match": sum(r["exact_match"] for r in rows) / len(rows),
              "f1": sum(r["f1"] for r in rows) / len(rows), "cases": rows}
    Path(args.output).write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
