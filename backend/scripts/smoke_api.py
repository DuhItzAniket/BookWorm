"""Exercise a running protected backend; creates a small, clearly named demo document."""
import argparse
import json
import os

import httpx


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://127.0.0.1:8000")
    parser.add_argument("--token-env", default="BOOKWORM_SMOKE_TOKEN")
    args = parser.parse_args()
    token = os.environ.get(args.token_env, "")
    if not token:
        parser.error(f"Set {args.token_env} to the protected backend's demo token.")
    with httpx.Client(base_url=args.url, timeout=180) as client:
        assert client.get("/api/health").json()["status"] == "ok"
        assert client.get("/documents").status_code == 401
        client.headers["Authorization"] = f"Bearer {token}"
        uploaded = client.post("/documents", files={"file": (
            "bookworm-smoke.txt",
            "📚 Harry Potter studies at Hogwarts School of Witchcraft and Wizardry.".encode(),
            "text/plain",
        )})
        uploaded.raise_for_status()
        document_id = uploaded.json()["id"]
        answered = client.post("/questions", json={"question": "Where does Harry Potter study?", "document_id": document_id})
        answered.raise_for_status()
        result = answered.json()
        assert not result["no_answer"] and "Hogwarts" in result["answer"]
        source = result["sources"][0]
        assert source["text"][source["start"]:source["end"]] == result["answer"]
        print(json.dumps({"document_id": document_id, "answer": result["answer"], "source_page": source["page"], "checks": "health, auth, upload, BERT, evidence offsets passed"}))


if __name__ == "__main__":
    main()
