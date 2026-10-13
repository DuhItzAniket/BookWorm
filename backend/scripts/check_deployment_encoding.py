"""Reject UTF-8 BOMs that break deployment parsers and dotenv variable names."""

from pathlib import Path


def main() -> None:
    root = Path(__file__).resolve().parents[2]
    paths = [
        *sorted((root / "backend").glob("requirements*.txt")),
        root / ".env.example",
        root / "frontend" / ".env.example",
    ]
    for path in paths:
        content = path.read_bytes()
        content.decode("utf-8")
        if content.startswith(b"\xef\xbb\xbf"):
            raise SystemExit(f"Remove the UTF-8 BOM from {path.relative_to(root)}")
    print(f"Deployment encoding OK: {len(paths)} UTF-8 files without BOM")


if __name__ == "__main__":
    main()
