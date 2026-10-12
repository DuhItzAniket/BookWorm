# Decisions and tradeoffs

| Decision | Reason | Consequence |
|---|---|---|
| Genuine BERT SQuAD 2.0 checkpoint | Meets the assignment and models unanswerable questions | Extractive answers only; not summaries or conversation reasoning |
| TF-IDF baseline | Explainable, inexpensive and easy to evaluate | Lexical mismatch can miss the right passage; dense retrieval needs a measured comparison |
| Exact text windows and offsets | Evidence can be inspected | Normalized text differs from original visual layout |
| Separate document/web modes | Evidence origins and external requests are explicit | Search answers use snippets, not complete webpages |
| Separate Vercel frontend and persistent Python service | Fits current SQLite/files and warm model process | Two deployment services and CORS configuration |
| Shared-token demo | Small academic deployment without account infrastructure | Every token holder accesses the same library; not multi-tenant isolation |
| No generated answer fallback | Avoid replacing the required reader with an unrelated chatbot | The system abstains or returns short spans instead of polished prose |
| Optional Glypharis bridge | User owns a separate CPU-first OCR project still in development | Prepared adapter, disabled feature, real-model release gate |
| Additive OCR provenance table | Preserve native-text databases while tracing recognized text | Future schema changes still require explicit migrations |
| Plain CSS reading-room UI | Tailored typography/layout without unused style frameworks | UI styles live in the application stylesheet |

The earlier baseline documents described an empty repository; that description is historical and no longer valid. Current implementation and verification are tracked in [phase status](PHASE_STATUS.md), [architecture](ARCHITECTURE.md) and [the plan](IMPLEMENTATION_PLAN.md).

RoBERTa and ALBERT are potential extractive QA comparisons, using QA-fine-tuned checkpoints under the same retrieval conditions. T5 is a separate generative experiment. GPT-2 is not an instruction-following QA model out of the box; a GPT-3-family hosted baseline would involve a separate provider and evaluation protocol. None of these comparisons is currently implemented or represented as a working model selector.
