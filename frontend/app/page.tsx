"use client";

import Link from "next/link";
import { FormEvent, useEffect, useRef, useState } from "react";

const API = (
  process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000"
).replace(/\/$/, "");
type Document = {
  id: number;
  filename: string;
  page_count: number;
  size: number;
  status: string;
};
type Source = {
  title: string;
  text: string;
  page: number;
  url: string | null;
  start: number;
  end: number;
  ocr_review_required?: boolean;
  ocr_model_version?: string;
};
type Answer = {
  answer: string;
  no_answer: boolean;
  score: number;
  sources: Source[];
  mode: string;
  model: string;
};
type Turn = { question: string; result: Answer };
type Capabilities = { web_search: boolean; model: string };

async function apiRequest(path: string, token: string, init: RequestInit = {}) {
  const response = await fetch(`${API}${path}`, {
    ...init,
    headers: {
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...init.headers,
    },
    signal: init.signal || AbortSignal.timeout(180000),
  });
  const payload = await response.json().catch(() => null);
  if (!response.ok) {
    throw new Error(
      typeof payload?.detail === "string"
        ? payload.detail
        : `The server returned an error (${response.status}). Please try again.`,
    );
  }
  if (payload === null)
    throw new Error("The server returned an invalid response.");
  return payload;
}

async function loadWorkspace(
  token: string,
  signal?: AbortSignal,
): Promise<[Document[], Capabilities]> {
  return Promise.all([
    apiRequest("/documents", token, { signal }),
    apiRequest("/capabilities", token, { signal }),
  ]);
}

function connectionError(error: unknown) {
  return error instanceof Error && error.message !== "Failed to fetch"
    ? error.message
    : "Cannot reach the BookWorm server. Start the backend or check its address, then reconnect.";
}

function BookIcon({ small = false }: { small?: boolean }) {
  return (
    <svg
      width={small ? 20 : 30}
      height={small ? 20 : 30}
      viewBox="0 0 32 32"
      fill="none"
      aria-hidden="true"
    >
      <path
        d="M16 8C12 4 6 5 3 6v21c5-2 9-1 13 2 4-3 8-4 13-2V6c-3-1-9-2-13 2Zm0 0v21"
        stroke="currentColor"
        strokeWidth="1.6"
        strokeLinejoin="round"
      />
      <path
        d="M8 11h3m-3 5h3m10-5h3m-3 5h3"
        stroke="currentColor"
        strokeLinecap="round"
      />
    </svg>
  );
}

export default function Home() {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [active, setActive] = useState<number | null>(null);
  const [histories, setHistories] = useState<Record<string, Turn[]>>({});
  const [question, setQuestion] = useState("");
  const [web, setWeb] = useState(false);
  const [webAvailable, setWebAvailable] = useState(false);
  const [busy, setBusy] = useState<"upload" | "answer" | null>(null);
  const [error, setError] = useState("");
  const [connected, setConnected] = useState(false);
  const [token, setToken] = useState("");
  const [accessOpen, setAccessOpen] = useState(false);
  const [dragging, setDragging] = useState(false);
  const [model, setModel] = useState("deepset/bert-base-cased-squad2");
  const fileInput = useRef<HTMLInputElement>(null);
  const end = useRef<HTMLDivElement>(null);
  const selected = documents.find((d) => d.id === active);
  const conversationKey = web ? "web" : String(active);
  const turns = histories[conversationKey] || [];

  async function connect() {
    try {
      const [docs, capabilities] = await loadWorkspace(token);
      setError("");
      setDocuments(docs);
      setWebAvailable(capabilities.web_search);
      setModel(capabilities.model);
      setConnected(true);
      setAccessOpen(false);
    } catch (err) {
      setConnected(false);
      setAccessOpen(true);
      setError(connectionError(err));
    }
  }

  // The access token stays in memory; documents stay on the configured backend.
  useEffect(() => {
    const controller = new AbortController();
    loadWorkspace("", controller.signal)
      .then(([docs, capabilities]) => {
        if (controller.signal.aborted) return;
        setDocuments(docs);
        setWebAvailable(capabilities.web_search);
        setModel(capabilities.model);
        setConnected(true);
      })
      .catch((err) => {
        if (controller.signal.aborted) return;
        setAccessOpen(true);
        setError(connectionError(err));
      });
    return () => controller.abort();
  }, []);
  useEffect(() => {
    end.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [turns.length, busy]);

  async function upload(file?: File) {
    if (!file || busy) return;
    if (!/\.(pdf|docx|epub|txt|md|csv|html|htm)$/i.test(file.name)) {
      setError(
        "Choose a PDF, DOCX, EPUB, TXT, Markdown, CSV, or HTML file. Convert legacy .doc files to .docx first.",
      );
      return;
    }
    if (file.size > 20 * 1024 * 1024) {
      setError(
        "This file exceeds 20 MB. Please split it into smaller documents.",
      );
      return;
    }
    setBusy("upload");
    setError("");
    const body = new FormData();
    body.append("file", file);
    try {
      const doc = await apiRequest("/documents", token, {
        method: "POST",
        body,
      });
      setDocuments((prev) => [doc, ...prev]);
      setActive(doc.id);
      setWeb(false);
      setQuestion("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed.");
    } finally {
      setBusy(null);
      if (fileInput.current) fileInput.current.value = "";
    }
  }

  async function ask(event: FormEvent) {
    event.preventDefault();
    if (!question.trim() || busy || (!web && !selected)) return;
    const submitted = question.trim();
    const key = conversationKey;
    setBusy("answer");
    setError("");
    try {
      const result = await apiRequest("/questions", token, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          question: submitted,
          mode: web ? "web" : "document",
          document_id: active,
        }),
      });
      setHistories((prev) => ({
        ...prev,
        [key]: [...(prev[key] || []), { question: submitted, result }],
      }));
      setQuestion("");
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Question answering failed.",
      );
    } finally {
      setBusy(null);
    }
  }

  return (
    <div className="workspace">
      <aside className="shelf">
        <Link className="brand" href="/" aria-label="BookWorm home">
          <BookIcon />
          <span>
            BookWorm<span className="brand-dot">.</span>
          </span>
        </Link>
        <div className="shelf-heading">
          <span className="eyebrow">YOUR LIBRARY</span>
          <span className="count">
            {String(documents.length).padStart(2, "0")}
          </span>
        </div>
        <button
          className={`upload-zone ${dragging ? "dragging" : ""}`}
          disabled={!!busy || !connected}
          onClick={() => fileInput.current?.click()}
          onDragOver={(e) => {
            e.preventDefault();
            setDragging(true);
          }}
          onDragLeave={() => setDragging(false)}
          onDrop={(e) => {
            e.preventDefault();
            setDragging(false);
            if (connected) void upload(e.dataTransfer.files[0]);
          }}
        >
          <span className="upload-plus">+</span>
          <strong>
            {busy === "upload" ? "Reading your document…" : "Add a document"}
          </strong>
          <span>Choose a file or drop it here</span>
        </button>
        <input
          ref={fileInput}
          type="file"
          className="sr-only"
          aria-label="Upload a document"
          accept=".pdf,.docx,.epub,.txt,.md,.csv,.html,.htm"
          onChange={(e) => void upload(e.target.files?.[0])}
        />
        <p className="file-note">PDF, EPUB, DOCX & text · Up to 20 MB</p>
        <nav className="document-list" aria-label="Uploaded documents">
          {documents.map((doc) => (
            <button
              key={doc.id}
              className={`document ${active === doc.id && !web ? "selected" : ""}`}
              disabled={!!busy}
              onClick={() => {
                setActive(doc.id);
                setWeb(false);
                setError("");
                setQuestion("");
              }}
            >
              <span className="file-icon">
                <BookIcon small />
              </span>
              <span className="document-info">
                <strong>{doc.filename}</strong>
                <small>
                  {doc.filename.toLowerCase().endsWith(".pdf")
                    ? `${doc.page_count} pages`
                    : "Text document"}{" "}
                  · {Math.max(1, Math.round(doc.size / 1024))} KB
                </small>
              </span>
              {active === doc.id && !web && <span className="selection-dot" />}
            </button>
          ))}
          {!documents.length && (
            <p className="empty-shelf">
              A place for your books,
              <br />
              papers, and curious questions.
            </p>
          )}
        </nav>
        <div className="shelf-bottom">
          <div className="private-note">
            <span>↳</span>
            <p>
              A little more understanding.
              <br />
              <strong>One question at a time.</strong>
            </p>
          </div>
          <button
            className="connection"
            onClick={() => setAccessOpen(!accessOpen)}
          >
            <span className={`status-dot ${connected ? "online" : ""}`} />
            {connected ? "Server connected" : "Connect to server"}
            <span>⚙</span>
          </button>
          {accessOpen && (
            <form
              className="access-form"
              onSubmit={(e) => {
                e.preventDefault();
                void connect();
              }}
            >
              <label htmlFor="access-token">Demo access token</label>
              <input
                id="access-token"
                type="password"
                value={token}
                autoComplete="off"
                onChange={(e) => setToken(e.target.value)}
                placeholder="Provided by the server owner"
              />
              <button className="small-button">Reconnect</button>
              <p>Everyone using this token shares this library.</p>
            </form>
          )}
        </div>
      </aside>

      <main className="reading-room">
        <header className="topbar">
          <div className="breadcrumb">
            Workspace <span>/</span>{" "}
            <strong>
              {web
                ? "The wider world"
                : selected
                  ? selected.filename
                  : "A fresh page"}
            </strong>
          </div>
          <span className="model-tag">
            <span /> BERT · Extractive QA
          </span>
        </header>
        <div className="conversation">
          {!turns.length ? (
            <section className="welcome">
              <div className="edition">
                <span /> YOUR READING COMPANION <span />
              </div>
              <h1>
                {web ? (
                  <>
                    A question beyond
                    <br />
                    <em>the page.</em>
                  </>
                ) : selected ? (
                  <>
                    Every good book
                    <br />
                    invites <em>a question.</em>
                  </>
                ) : (
                  <>
                    Less searching.
                    <br />
                    <em>More understanding.</em>
                  </>
                )}
              </h1>
              <p className="intro">
                {web
                  ? "Search the web and let BERT find an answer in the results. Every answer comes with a source you can visit."
                  : selected
                    ? `You're reading ${selected.filename}. Ask a specific question and follow the answer back to the text.`
                    : "Bring a book, a research paper, or a few notes. Ask what’s on your mind. Find the answer in the words you brought."}
              </p>
              <div className="book-art" aria-hidden="true">
                <div className="book-spine spine-one">THE ART OF ASKING</div>
                <div className="book-spine spine-two">a little curiosity</div>
                <div className="book-spine spine-three">
                  BETWEEN THE LINES <span>✦</span>
                </div>
                <span className="art-caption">
                  GOOD QUESTIONS OPEN NEW CHAPTERS
                </span>
              </div>
              <div className="how-it-works">
                <div>
                  <span>01</span>
                  <strong>Bring your reading</strong>
                  <p>Upload a document to your library.</p>
                </div>
                <div>
                  <span>02</span>
                  <strong>Follow your curiosity</strong>
                  <p>Ask a clear, specific question.</p>
                </div>
                <div>
                  <span>03</span>
                  <strong>See it in context</strong>
                  <p>Read the answer and its source.</p>
                </div>
              </div>
            </section>
          ) : (
            <div className="turns">
              {turns.map((turn, i) => (
                <article className="turn" key={i}>
                  <div className="question">
                    <span className="eyebrow">YOU ASKED</span>
                    <h2>{turn.question}</h2>
                  </div>
                  <div className="answer">
                    <div className="answer-label">
                      <BookIcon small />
                      <span>BOOKWORM</span>
                      <span className="evidence-label">
                        {turn.result.mode === "web"
                          ? "WEB SEARCH"
                          : "FROM YOUR DOCUMENT"}
                      </span>
                    </div>
                    <p
                      className={`answer-text ${turn.result.no_answer ? "unanswered" : ""}`}
                    >
                      {turn.result.answer}
                    </p>
                    {turn.result.no_answer && (
                      <p className="answer-hint">
                        Try naming the person, place, or event explicitly, or
                        ask about another passage.
                      </p>
                    )}
                    {turn.result.sources.map((source, index) => (
                      <details className="evidence" key={index} open>
                        <summary>
                          <span>↳ &nbsp; {source.title}</span>
                          <span>
                            {source.url
                              ? "Web excerpt"
                              : /\.pdf$/i.test(source.title)
                                ? `Page ${source.page}`
                                : "Text section"}
                          </span>
                        </summary>
                        <blockquote>
                          {/* Python evidence offsets count Unicode code points, not UTF-16 units. */}
                          {Array.from(source.text)
                            .slice(0, source.start)
                            .join("")}
                          <mark>
                            {Array.from(source.text)
                              .slice(source.start, source.end)
                              .join("")}
                          </mark>
                          {Array.from(source.text).slice(source.end).join("")}
                        </blockquote>
                        {source.ocr_review_required && (
                          <p className="answer-hint">
                            Read with Glypharis {source.ocr_model_version}. OCR
                            can misread characters; check the original page.
                          </p>
                        )}
                        {source.url && (
                          <a
                            href={source.url}
                            target="_blank"
                            rel="noopener noreferrer"
                          >
                            Visit source ↗
                          </a>
                        )}
                      </details>
                    ))}
                    {!turn.result.no_answer && (
                      <div className="score-note">
                        Model score {turn.result.score.toFixed(2)} · An evidence
                        signal, not a guarantee of correctness
                      </div>
                    )}
                  </div>
                </article>
              ))}
            </div>
          )}
          {busy === "answer" && (
            <div className="working" role="status">
              <span className="pulse" />
              Finding the passages. Reading between the lines…
              <small>
                The first question may take longer while the model loads.
              </small>
            </div>
          )}
          <div ref={end} />
        </div>
        <footer className="composer-area">
          {error && (
            <div className="error" role="alert">
              <span>{error}</span>
              <button onClick={() => setError("")} aria-label="Dismiss error">
                ×
              </button>
            </div>
          )}
          <form onSubmit={ask} className="composer">
            <label className="sr-only" htmlFor="question">
              Your question
            </label>
            <textarea
              id="question"
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              maxLength={500}
              rows={2}
              disabled={!!busy}
              placeholder={
                web
                  ? "What would you like to find on the web?"
                  : selected
                    ? "What would you like to know about this document?"
                    : "Add a document to start a conversation…"
              }
              onKeyDown={(e) => {
                if (
                  e.key === "Enter" &&
                  !e.shiftKey &&
                  !e.nativeEvent.isComposing
                ) {
                  e.preventDefault();
                  e.currentTarget.form?.requestSubmit();
                }
              }}
            />
            <div className="composer-tools">
              <button
                type="button"
                className={`web-toggle ${web ? "active" : ""}`}
                aria-pressed={web}
                disabled={!webAvailable || !!busy}
                onClick={() => {
                  setWeb(!web);
                  setError("");
                }}
                title={
                  webAvailable
                    ? "Use public search snippets instead of your document"
                    : "The server owner must configure a Brave Search API key"
                }
              >
                <span>◎</span> Search the web{" "}
                {web && <span className="toggle-dot" />}
              </button>
              <button
                className="send"
                type="submit"
                disabled={
                  !connected ||
                  !!busy ||
                  question.trim().length < 3 ||
                  (!web && !selected)
                }
                aria-label="Ask question"
              >
                ↑
              </button>
            </div>
          </form>
          <p className="composer-note">
            {web
              ? "Your question is sent to Brave Search. Uploaded documents are not sent."
              : "Answers are extracted from your document. Ask each question with its own context."}
            <span title={model}>Powered by BERT</span>
          </p>
        </footer>
      </main>
    </div>
  );
}
