export default function Home() {
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
              Ask questions about a whole PDF.
            </h2>
            <p className="mt-5 max-w-xl text-lg text-slate-600">
              BookWorm finds the most relevant passages, then uses a pretrained BERT model to extract the answer from the document with page and evidence support.
            </p>

            <div className="mt-8 flex flex-wrap gap-4">
              <button className="rounded-xl bg-emerald-600 px-6 py-3 font-semibold text-white shadow-sm transition hover:bg-emerald-700">
                Upload PDF
              </button>
              <button className="rounded-xl border border-slate-300 bg-white px-6 py-3 font-semibold text-slate-700 transition hover:border-slate-400 hover:bg-slate-50">
                Learn more
              </button>
            </div>
          </div>

          <div className="rounded-3xl border border-emerald-100 bg-white p-6 shadow-lg shadow-emerald-100/50">
            <div className="flex flex-col items-center text-center">
              <div className="mb-4 flex h-24 w-24 items-center justify-center rounded-full bg-gradient-to-br from-emerald-100 to-lime-100 text-6xl">
                🐛
              </div>
              <h3 className="text-xl font-semibold text-slate-800">Wormy is ready</h3>
              <p className="mt-2 text-sm text-slate-600">
                Upload a PDF and start asking grounded questions from the document.
              </p>
            </div>
          </div>
        </section>
      </div>
    </main>
  );
}
