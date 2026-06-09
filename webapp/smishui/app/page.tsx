"use client";

import { onAuthStateChanged, signOut } from "firebase/auth";
import { FormEvent, useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { auth, hasFirebaseConfig } from "@/lib/firebase";

type ClassifyResponse = {
  label: "benign" | "smishing";
  y_pred: 0 | 1;
  risk_percent_smishing: number | null;
  verdict_plain: string;
  signals_toward_smishing: string[];
  signals_toward_benign: string[];
  explanation_note?: string;
};

export default function Home() {
  const router = useRouter();
  const [text, setText] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<ClassifyResponse | null>(null);
  const [loggedInUser, setLoggedInUser] = useState<string | null>(null);
  const [checkingAuth, setCheckingAuth] = useState(hasFirebaseConfig);
  const [loggingOut, setLoggingOut] = useState(false);

  useEffect(() => {
    if (!auth || !hasFirebaseConfig) return;

    const unsub = onAuthStateChanged(auth, (user) => {
      if (!user) {
        setLoggedInUser(null);
        setCheckingAuth(false);
        router.replace("/login");
        return;
      }

      setLoggedInUser(user.email ?? "Authenticated user");
      setCheckingAuth(false);
    });

    return () => unsub();
  }, [router]);

  const riskLine = useMemo(() => {
    if (!result || result.risk_percent_smishing === null || Number.isNaN(result.risk_percent_smishing)) {
      return null;
    }
    const r = result.risk_percent_smishing;
    if (result.label === "smishing") {
      return `Estimated smishing likelihood: about ${r}% (model flags it when this score is high enough).`;
    }
    return `Estimated smishing-like score: about ${r}% (the model still labels this as benign overall).`;
  }, [result]);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setResult(null);

    const cleanText = text.trim();
    if (!cleanText) {
      setError("Please enter an SMS message.");
      return;
    }

    setLoading(true);
    try {
      const res = await fetch("/api/classify", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: cleanText, top_k: 8 }),
      });
      const body = await res.json();
      if (!res.ok) {
        const detail = typeof body?.details === "string" ? body.details : "Classification failed.";
        throw new Error(detail);
      }
      setResult(body as ClassifyResponse);
    } catch (err) {
      const message = err instanceof Error ? err.message : "Unexpected error occurred.";
      setError(message);
    } finally {
      setLoading(false);
    }
  }

  async function onLogout() {
    if (!auth || !hasFirebaseConfig) {
      router.replace("/login");
      return;
    }

    setError(null);
    setLoggingOut(true);
    try {
      await signOut(auth);
      router.replace("/login");
    } catch {
      setError("Failed to log out. Please try again.");
      setLoggingOut(false);
    }
  }

  if (checkingAuth) {
    return (
      <div className="min-h-screen bg-slate-950 text-slate-100 flex items-center justify-center">
        <p className="text-sm text-slate-300">Checking session...</p>
      </div>
    );
  }

  if (!hasFirebaseConfig || !auth) {
    return (
      <div className="min-h-screen bg-slate-950 text-slate-100 flex items-center justify-center px-4">
        <main className="w-full max-w-xl rounded-2xl border border-amber-300/30 bg-amber-500/10 p-5">
          <h1 className="text-lg font-semibold text-amber-200">Firebase setup pending</h1>
          <p className="mt-2 text-sm text-amber-100/90">
            Add your Firebase credentials in `.env.local` based on `.env.example`, then restart the app.
          </p>
        </main>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-indigo-950 to-slate-900 px-4 py-10 text-slate-100">
      <main className="mx-auto w-full max-w-3xl rounded-3xl border border-white/15 bg-white/10 p-6 shadow-2xl backdrop-blur md:p-8">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <h1 className="text-2xl font-semibold tracking-tight md:text-3xl">Smishing Detection</h1>
          <button
            type="button"
            onClick={onLogout}
            disabled={loggingOut}
            className="rounded-full border border-white/25 bg-white/10 px-4 py-2 text-xs font-semibold uppercase tracking-wide text-slate-100 transition hover:bg-white/20 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {loggingOut ? "Signing out..." : "Logout"}
          </button>
        </div>
        <p className="mt-2 text-sm text-slate-300 md:text-base">
          Paste an SMS below to predict if it is benign or smishing.
        </p>
        {loggedInUser ? (
          <p className="mt-2 text-xs text-emerald-300">Logged in as: {loggedInUser}</p>
        ) : null}

        <form onSubmit={onSubmit} className="mt-6 space-y-4">
          <textarea
            value={text}
            onChange={(e) => setText(e.target.value)}
            placeholder="Example: URGENT! Verify your account now at ..."
            className="h-36 w-full resize-none rounded-2xl border border-white/20 bg-slate-950/50 px-4 py-3 text-sm outline-none ring-indigo-300/50 transition focus:ring-2"
          />
          <button
            type="submit"
            disabled={loading}
            className="rounded-full bg-gradient-to-r from-indigo-500 to-cyan-400 px-6 py-3 text-sm font-semibold text-slate-950 transition hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {loading ? "Analyzing..." : "Analyze Message"}
          </button>
        </form>

        {error ? (
          <div className="mt-5 rounded-2xl border border-rose-300/40 bg-rose-500/15 px-4 py-3 text-sm text-rose-200">
            {error}
          </div>
        ) : null}

        {result ? (
          <section className="mt-6 space-y-5 rounded-2xl border border-white/15 bg-slate-950/40 p-5">
            <div className="flex flex-wrap items-center gap-3">
              <span
                className={`rounded-full px-4 py-1 text-xs font-semibold uppercase tracking-wide ${
                  result.label === "smishing"
                    ? "bg-rose-500/20 text-rose-200"
                    : "bg-emerald-500/20 text-emerald-200"
                }`}
              >
                {result.label}
              </span>
              {riskLine ? <span className="text-sm text-slate-300">{riskLine}</span> : null}
            </div>

            <p className="text-sm leading-relaxed text-slate-200 md:text-base">{result.verdict_plain}</p>

            {result.signals_toward_smishing.length > 0 ? (
              <div>
                <h2 className="text-sm font-semibold text-rose-200">What leaned toward smishing</h2>
                <ul className="mt-2 list-disc space-y-2 pl-5 text-sm leading-relaxed text-slate-200">
                  {result.signals_toward_smishing.map((line, i) => (
                    <li key={`s-${i}`}>{line}</li>
                  ))}
                </ul>
              </div>
            ) : null}

            {result.signals_toward_benign.length > 0 ? (
              <div>
                <h2 className="text-sm font-semibold text-emerald-200">What leaned toward benign</h2>
                <ul className="mt-2 list-disc space-y-2 pl-5 text-sm leading-relaxed text-slate-200">
                  {result.signals_toward_benign.map((line, i) => (
                    <li key={`b-${i}`}>{line}</li>
                  ))}
                </ul>
              </div>
            ) : null}

            {result.explanation_note ? (
              <p className="text-xs leading-relaxed text-slate-500">{result.explanation_note}</p>
            ) : null}
          </section>
        ) : null}
      </main>
    </div>
  );
}
