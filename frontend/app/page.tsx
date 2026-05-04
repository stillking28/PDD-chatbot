"use client";

import { FormEvent, KeyboardEvent, useEffect, useMemo, useRef, useState } from "react";
import { TieredMessage } from "../components/TieredMessage";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

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

type ChatTurn = {
  id: string;
  question: string;
  answer: ChatResponse;
};

export default function Page() {
  const quickPrompts = [
    "Нужно ли уступать пешеходу на нерегулируемом переходе?",
    "Кому уступать при повороте налево на зеленый?",
    "Когда занимать крайнее положение перед поворотом?",
  ];
  const [question, setQuestion] = useState("");
  const [history, setHistory] = useState<ChatTurn[]>([]);
  const [loading, setLoading] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement | null>(null);
  const chatEndRef = useRef<HTMLDivElement | null>(null);

  const canAsk = useMemo(() => question.trim().length > 1 && !loading, [question, loading]);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [history, loading]);

  function resizeTextarea() {
    if (!textareaRef.current) return;
    textareaRef.current.style.height = "0px";
    textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 180)}px`;
  }

  function onComposerKeyDown(event: KeyboardEvent<HTMLTextAreaElement>) {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      if (canAsk) {
        event.currentTarget.form?.requestSubmit();
      }
    }
  }

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    if (!canAsk) return;
    setLoading(true);
    try {
      const response = await fetch(`${API_URL}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          question,
          language: "ru",
          show_source: true,
        }),
      });
      const data = (await response.json()) as ChatResponse;
      const turn: ChatTurn = {
        id: `${Date.now()}`,
        question: question.trim(),
        answer: data,
      };
      setHistory((prev) => [...prev, turn]);
      setQuestion("");
      requestAnimationFrame(resizeTextarea);
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="min-h-screen bg-gray-50">
      <section className="mx-auto max-w-3xl px-4 pb-4 pt-6">
        <h1 className="text-2xl font-semibold text-gray-900">PDD ChatBot</h1>
        <p className="mt-1 text-sm text-gray-600">Спокойный помощник по ПДД: просто, без осуждения, с официальным источником.</p>
      </section>

      <section className="mx-auto grid max-w-3xl gap-3 px-4 pb-40">
        {history.length === 0 ? (
          <article className="rounded-2xl border border-dashed border-gray-300 bg-white p-4 text-sm text-gray-600 shadow-sm">
            Задайте вопрос по ситуации на дороге, и я отвечу в 3 уровнях с официальной ссылкой.
          </article>
        ) : null}

        {history.map((turn) => (
          <div key={turn.id} className="space-y-2">
            <article className="ml-auto w-fit max-w-[85%] rounded-2xl bg-gray-900 px-4 py-2 text-sm text-white shadow-sm">
              <p>{turn.question}</p>
            </article>

            <article className="max-w-[90%] rounded-2xl border border-gray-200 bg-white px-4 py-3 shadow-sm">
              <TieredMessage result={turn.answer} />
            </article>
          </div>
        ))}
        {loading ? (
          <article className="w-fit rounded-2xl border border-gray-200 bg-white px-4 py-3 shadow-sm">
            <div className="flex gap-1.5">
              <span className="h-2 w-2 animate-bounce rounded-full bg-gray-400 [animation-delay:-0.2s]" />
              <span className="h-2 w-2 animate-bounce rounded-full bg-gray-400 [animation-delay:-0.1s]" />
              <span className="h-2 w-2 animate-bounce rounded-full bg-gray-400" />
            </div>
          </article>
        ) : null}
        <div ref={chatEndRef} />
      </section>

      <div className="fixed inset-x-0 bottom-0 border-t border-gray-200 bg-gray-50/95 backdrop-blur">
        <form onSubmit={onSubmit} className="mx-auto max-w-3xl px-4 py-3">
          <div className="mb-2 flex flex-wrap gap-2">
            {quickPrompts.map((prompt) => (
              <button
                key={prompt}
                type="button"
                className="rounded-full border border-gray-200 bg-white px-3 py-1.5 text-xs text-gray-700 shadow-sm transition hover:bg-gray-100"
                onClick={() => {
                  setQuestion(prompt);
                  requestAnimationFrame(() => {
                    resizeTextarea();
                    textareaRef.current?.focus();
                  });
                }}
              >
                {prompt}
              </button>
            ))}
          </div>

          <div className="flex items-end gap-2 rounded-2xl border border-gray-200 bg-white p-2 shadow-md">
            <textarea
              ref={textareaRef}
              className="max-h-44 min-h-10 w-full resize-none bg-transparent px-2 py-2 text-sm text-gray-800 outline-none placeholder:text-gray-400"
              value={question}
              onChange={(e) => {
                setQuestion(e.target.value);
                resizeTextarea();
              }}
              onKeyDown={onComposerKeyDown}
              rows={1}
              placeholder="Спросите про дорожную ситуацию..."
            />
            <button
              type="submit"
              disabled={!canAsk}
              aria-label="Send message"
              className="inline-flex h-9 w-9 items-center justify-center rounded-full bg-blue-600 text-white transition hover:bg-blue-700 disabled:cursor-not-allowed disabled:bg-blue-300"
            >
              <svg viewBox="0 0 24 24" className="h-4 w-4 fill-current" aria-hidden="true">
                <path d="M12 4l6 6h-4v10h-4V10H6l6-6z" />
              </svg>
            </button>
          </div>
        </form>
      </div>
    </main>
  );
}
