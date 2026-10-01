# BookWorm Decisions Log

## Decision 01 — Repository baseline is empty

The workspace currently has no source code, no branch history, and no project files. The project will therefore begin from a clean repository baseline rather than trying to retrofit existing code.

## Decision 02 — Use a retrieval + extractive QA architecture

The academic requirement is explicit: the system must retain BERT as the core question-answering model. Retrieval is used only to solve the large-document context-size problem.

## Decision 03 — Use clear phase-based delivery

The project will be implemented in defined phases, with a mandatory test and documentation gate after each phase. This keeps the project maintainable and avoids building the final application without verifying each layer.

## Decision 04 — Separate frontend and backend

The frontend is a user-facing application while the ML pipeline remains in Python. This improves portability, testing, and deployment flexibility.

## Decision 05 — Use SQLite for development, PostgreSQL-ready architecture for production

SQLite is the simplest professional choice for local development and tests, while SQLAlchemy keeps the data layer compatible with PostgreSQL-like deployment environments later.

## Decision 06 — Prefer document-grounded no-answer behavior

If the document does not contain enough evidence, the application should return a clear “could not find a reliable answer” message instead of inventing information.

## Decision 07 — Keep the first implementation straightforward

The project should not overengineer the first version with Kubernetes, Redis, Kafka, vector databases, or complex orchestration when the core PDF + retrieval + BERT pipeline is still being built.
