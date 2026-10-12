"""Download the exact configured checkpoint before serving the first question."""
from app.services.qa_service import get_reader

if __name__ == "__main__":
    reader = get_reader()
    print(f"Ready: {reader.model.config.model_type} on {reader.device}")
