"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useEffect, useState } from "react";
import {
  onAuthStateChanged,
  createUserWithEmailAndPassword,
  updateProfile,
} from "firebase/auth";
import { ref, set, serverTimestamp } from "firebase/database";
import { auth, db, hasFirebaseConfig } from "@/lib/firebase";

function friendlyError(code: string): string {
  switch (code) {
    case "auth/email-already-in-use":
      return "An account with this email already exists. Try signing in.";
    case "auth/invalid-email":
      return "Invalid email address.";
    case "auth/weak-password":
      return "Password is too weak. Use at least 6 characters.";
    case "auth/too-many-requests":
      return "Too many attempts. Please try again later.";
    default:
      return `Sign-up failed (${code}).`;
  }
}

export default function SignUpPage() {
  const router = useRouter();
  const [displayName, setDisplayName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
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
    const cleanName = displayName.trim();

    if (!cleanEmail || !password) {
      setError("Please enter both email and password.");
      return;
    }
    if (password.length < 6) {
      setError("Password must be at least 6 characters.");
      return;
    }
    if (password !== confirmPassword) {
      setError("Passwords do not match.");
      return;
    }
    if (!auth || !hasFirebaseConfig) {
      setError("Firebase is not configured. Add env values from .env.example and restart dev server.");
      return;
    }

    setLoading(true);
    try {
      const cred = await createUserWithEmailAndPassword(auth, cleanEmail, password);

      if (cleanName) {
        await updateProfile(cred.user, { displayName: cleanName });
      }

      if (db) {
        await set(ref(db, `users/${cred.user.uid}`), {
          email: cred.user.email,
          displayName: cleanName || null,
          createdAt: serverTimestamp(),
          lastLoginAt: serverTimestamp(),
          source: "web",
        });
      }

      router.replace("/");
    } catch (err: any) {
      const code = err?.code ?? "";
      setError(friendlyError(code));
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
        <h1 className="text-2xl font-semibold tracking-tight md:text-3xl">Create account</h1>
        <p className="mt-2 text-sm text-slate-300">Sign up to start detecting smishing messages.</p>

        <form onSubmit={onSubmit} className="mt-6 space-y-4">
          <input
            type="text"
            value={displayName}
            onChange={(e) => setDisplayName(e.target.value)}
            placeholder="Display name (optional)"
            autoComplete="name"
            className="w-full rounded-2xl border border-white/20 bg-slate-950/50 px-4 py-3 text-sm outline-none ring-indigo-300/50 transition focus:ring-2"
          />
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
            placeholder="Password (min 6 characters)"
            autoComplete="new-password"
            className="w-full rounded-2xl border border-white/20 bg-slate-950/50 px-4 py-3 text-sm outline-none ring-indigo-300/50 transition focus:ring-2"
          />
          <input
            type="password"
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            placeholder="Confirm password"
            autoComplete="new-password"
            className="w-full rounded-2xl border border-white/20 bg-slate-950/50 px-4 py-3 text-sm outline-none ring-indigo-300/50 transition focus:ring-2"
          />
          <button
            type="submit"
            disabled={loading}
            className="w-full rounded-full bg-gradient-to-r from-indigo-500 to-cyan-400 px-6 py-3 text-sm font-semibold text-slate-950 transition hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {loading ? "Creating account..." : "Create account"}
          </button>
        </form>

        {error ? (
          <div className="mt-4 rounded-2xl border border-rose-300/40 bg-rose-500/15 px-4 py-3 text-sm text-rose-200">
            {error}
          </div>
        ) : null}

        <p className="mt-5 text-xs text-slate-400">
          Already have an account?{" "}
          <Link href="/login" className="text-cyan-300 hover:text-cyan-200">
            Sign in
          </Link>
        </p>
      </main>
    </div>
  );
}
