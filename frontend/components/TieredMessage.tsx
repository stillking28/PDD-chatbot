import { useState } from "react";

type ChatResponse = {
  short_answer: string;
  simple_explanation: string;
  source_clause_id: string;
  source_url: string;
  source_raw_text?: string | null;
  diagram_url?: string | null;
  blocked_by_guardrail: boolean;
  guardrail_reason?: string | null;
};

export function TieredMessage({ result }: { result: ChatResponse }) {
  const [isSourceOpen, setIsSourceOpen] = useState(false);
  const showRephraseTips =
    result.blocked_by_guardrail &&
    (result.guardrail_reason === "no_retrieval_context" || result.source_clause_id === "N/A");
  const canShowSource = Boolean(result.source_clause_id && result.source_clause_id !== "N/A");

  return (
    <section className="space-y-3">
      <p className="text-lg font-semibold text-gray-900">{result.short_answer}</p>
      <p className="text-base text-gray-700">{result.simple_explanation}</p>
      {showRephraseTips ? (
        <article className="rounded-xl border border-purple-200 bg-purple-50 p-3 text-sm text-purple-900">
          <p className="font-medium">Как уточнить вопрос</p>
          <p className="mt-1">Добавьте тип перекрестка, знаки/светофор и участников движения.</p>
        </article>
      ) : null}

      {canShowSource ? (
        <article className="rounded-xl border border-gray-200 bg-gray-50/90 transition-colors">
          <button
            type="button"
            onClick={() => setIsSourceOpen((prev) => !prev)}
            className="flex w-full items-center justify-between px-3 py-2 text-left text-sm font-medium text-gray-700 hover:bg-gray-100/80 rounded-xl transition-colors"
          >
            <span>📖 Official Clause {result.source_clause_id}</span>
            <span className={`transition-transform ${isSourceOpen ? "rotate-180" : ""}`}>⌄</span>
          </button>

          <div
            className={`grid transition-all duration-300 ease-out ${
              isSourceOpen ? "grid-rows-[1fr] opacity-100" : "grid-rows-[0fr] opacity-0"
            }`}
          >
            <div className="overflow-hidden">
              <div className="space-y-2 px-3 pb-3 text-sm text-gray-700">
                {result.source_raw_text ? <p className="leading-relaxed">{result.source_raw_text}</p> : null}
                {result.source_url ? (
                  <a href={result.source_url} target="_blank" rel="noreferrer" className="inline-block text-blue-600 hover:text-blue-700">
                    Open official source
                  </a>
                ) : null}
                {result.diagram_url ? <p className="text-gray-500">Static diagram: {result.diagram_url}</p> : null}
              </div>
            </div>
          </div>
        </article>
      ) : null}
    </section>
  );
}
