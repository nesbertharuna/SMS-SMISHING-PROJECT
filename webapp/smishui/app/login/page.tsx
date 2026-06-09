"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useEffect, useState } from "react";
import { onAuthStateChanged, signInWithEmailAndPassword } from "firebase/auth";
import { auth, hasFirebaseConfig } from "@/lib/firebase";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [checkingAuth, setCheckingAuth] = useState(hasFirebaseConfig);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!auth || !hasFirebaseConfig) return;

    const unsub = onAuthStateChanged(auth, (user) => {
      if (user) {
        router.replace("/");
        return;
      }
      setCheckingAuth(false);
    });

    return () => unsub();
  }, [router]);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);

    const cleanEmail = email.trim();
    if (!cleanEmail || !password) {
      setError("Please enter both email and password.");
      return;
    }
    if (!auth || !hasFirebaseConfig) {
      setError("Firebase is not configured. Add env values from .env.example and restart dev server.");
      return;
    }

    setLoading(true);
    try {
      await signInWithEmailAndPassword(auth, cleanEmail, password);
      router.replace("/");
    } catch {
      setError("Invalid credentials. Please try again.");
    } finally {
      setLoading(false);
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
        <main className="w-full max-w-lg rounded-2xl border border-amber-300/30 bg-amber-500/10 p-5">
          <h1 className="text-lg font-semibold text-amber-200">Firebase config required</h1>
          <p className="mt-2 text-sm text-amber-100/90">
            Add Firebase values to `.env.local` using `.env.example`, then restart `npm run dev`.
          </p>
        </main>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-indigo-950 to-slate-900 px-4 py-10 text-slate-100">
      <main className="mx-auto w-full max-w-md rounded-3xl border border-white/15 bg-white/10 p-6 shadow-2xl backdrop-blur md:p-8">
        <h1 className="text-2xl font-semibold tracking-tight md:text-3xl">Sign in</h1>
        <p className="mt-2 text-sm text-slate-300">Use your Firebase Auth email and password.</p>

        <form onSubmit={onSubmit} className="mt-6 space-y-4">
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="Email"
            autoComplete="email"
            className="w-full rounded-2xl border border-white/20 bg-slate-950/50 px-4 py-3 text-sm outline-none ring-indigo-300/50 transition focus:ring-2"
          />
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="Password"
            autoComplete="current-password"
            className="w-full rounded-2xl border border-white/20 bg-slate-950/50 px-4 py-3 text-sm outline-none ring-indigo-300/50 transition focus:ring-2"
          />
          <button
            type="submit"
            disabled={loading}
            className="w-full rounded-full bg-gradient-to-r from-indigo-500 to-cyan-400 px-6 py-3 text-sm font-semibold text-slate-950 transition hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {loading ? "Signing in..." : "Sign in"}
          </button>
        </form>

        {error ? (
          <div className="mt-4 rounded-2xl border border-rose-300/40 bg-rose-500/15 px-4 py-3 text-sm text-rose-200">
            {error}
          </div>
        ) : null}

        <p className="mt-5 text-xs text-slate-400">
          No account? Create one in Firebase Console or add sign-up flow later.{" "}
          <Link href="/" className="text-cyan-300 hover:text-cyan-200">
            Back to app
          </Link>
        </p>
      </main>
    </div>
  );
}
