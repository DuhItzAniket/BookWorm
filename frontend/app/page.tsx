"use client";

import { ChangeEvent, DragEvent, FormEvent, useState } from "react";

const SUPPORTED_TYPES = ".pdf,.txt,.md,.csv,.rtf,.doc,.docx,.epub,.html,.htm";
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

export default function Home() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [isDragging, setIsDragging] = useState(false);
  const [status, setStatus] = useState<string | null>(null);
  const [documentMeta, setDocumentMeta] = useState<Record<string, unknown> | null>(null);

  const handleFileChange = (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0] ?? null;
    setSelectedFile(file);
    setStatus(null);
    setDocumentMeta(null);
  };

  const handleDrop = (event: DragEvent<HTMLLabelElement>) => {
    event.preventDefault();
    setIsDragging(false);

    const file = event.dataTransfer.files?.[0] ?? null;
    if (!file) {
      setStatus("No file was dropped.");
      return;
    }

    setSelectedFile(file);
    setStatus(null);
    setDocumentMeta(null);
  };

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    if (!selectedFile) {
      setStatus("Please choose a document before uploading.");
      return;
    }

    setIsUploading(true);
    setStatus(null);

    const formData = new FormData();
    formData.append("file", selectedFile);

    try {
      const response = await fetch(`${API_BASE_URL}/documents`, {
        method: "POST",
        body: formData,
      });

      const payload = await response.json();

      if (!response.ok) {
        throw new Error(payload.detail || "The upload failed.");
      }

      setDocumentMeta(payload);
      setStatus(`Uploaded successfully: ${payload.filename}`);
    } catch (error) {
      const message = error instanceof Error ? error.message : "Upload failed.";
      setStatus(message);
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <main className="min-h-screen bg-gradient-to-b from-emerald-50 via-white to-slate-50 px-6 py-10">
      <div className="mx-auto max-w-5xl">
        <header className="mb-10 flex items-center justify-between border-b border-emerald-100 pb-4">
          <div>
            <p className="text-sm font-medium uppercase tracking-[0.2em] text-emerald-700">BookWorm</p>
            <h1 className="mt-2 text-3xl font-bold text-slate-900">Document QA with Wormy</h1>
          </div>
          <div className="flex h-14 w-14 items-center justify-center rounded-full border-2 border-emerald-200 bg-emerald-100 text-2xl">
            🐛
          </div>
        </header>

        <section className="grid gap-8 lg:grid-cols-[1.2fr_0.8fr] lg:items-center">
          <div>
            <p className="mb-4 inline-flex rounded-full border border-emerald-200 bg-emerald-50 px-3 py-1 text-sm font-medium text-emerald-700">
              Retrieval + BERT Question Answering
            </p>
            <h2 className="text-5xl font-bold tracking-tight text-slate-900">
              Ask questions about a whole book or document.
            </h2>
            <p className="mt-5 max-w-xl text-lg text-slate-600">
              BookWorm supports PDFs, text files, DOCX, EPUB, and other readable document formats before retrieving the most relevant passages and extracting grounded answers.
            </p>

            <form onSubmit={handleSubmit} className="mt-8 space-y-4">
              <label
                onDragOver={(event) => {
                  event.preventDefault();
                  setIsDragging(true);
                }}
                onDragEnter={(event) => {
                  event.preventDefault();
                  setIsDragging(true);
                }}
                onDragLeave={(event) => {
                  event.preventDefault();
                  setIsDragging(false);
                }}
                onDrop={handleDrop}
                className={`flex cursor-pointer flex-col rounded-2xl border border-dashed bg-white p-4 text-sm text-slate-700 shadow-sm transition ${
                  isDragging ? "border-emerald-500 bg-emerald-50" : "border-emerald-300"
                }`}
              >
                <span className="mb-2 font-medium text-slate-800">
                  {selectedFile ? `Selected: ${selectedFile.name}` : "Choose a file or drag it here"}
                </span>
                <input
                  type="file"
                  accept={SUPPORTED_TYPES}
                  onChange={handleFileChange}
                  className="block w-full text-sm text-slate-500 file:mr-4 file:rounded-full file:border-0 file:bg-emerald-100 file:px-4 file:py-2 file:text-sm file:font-semibold file:text-emerald-700 hover:file:bg-emerald-200"
                />
              </label>

              <button
                type="submit"
                disabled={!selectedFile || isUploading}
                className="rounded-xl bg-emerald-600 px-6 py-3 font-semibold text-white shadow-sm transition hover:bg-emerald-700 disabled:cursor-not-allowed disabled:bg-emerald-300"
              >
                {isUploading ? "Uploading..." : "Upload document"}
              </button>
            </form>

            {status && (
              <p className="mt-4 rounded-xl border border-emerald-100 bg-emerald-50 px-4 py-3 text-sm text-emerald-800">
                {status}
              </p>
            )}

            {documentMeta && (
              <div className="mt-4 rounded-2xl border border-slate-200 bg-slate-50 p-4 text-sm text-slate-700">
                <p className="font-semibold text-slate-800">Document ready</p>
                <ul className="mt-2 space-y-1">
                  <li>Filename: {String(documentMeta.filename)}</li>
                  <li>Pages: {String(documentMeta.page_count)}</li>
                  <li>Status: {String(documentMeta.status)}</li>
                </ul>
              </div>
            )}
          </div>

          <div className="rounded-3xl border border-emerald-100 bg-white p-6 shadow-lg shadow-emerald-100/50">
            <div className="flex flex-col items-center text-center">
              <div className="mb-4 flex h-24 w-24 items-center justify-center rounded-full bg-gradient-to-br from-emerald-100 to-lime-100 text-6xl">
                🐛
              </div>
              <h3 className="text-xl font-semibold text-slate-800">Wormy is ready</h3>
              <p className="mt-2 text-sm text-slate-600">
                Upload a PDF, text document, EPUB, or DOCX and start asking grounded questions from the document.
              </p>
            </div>
          </div>
        </section>
      </div>
    </main>
  );
}
