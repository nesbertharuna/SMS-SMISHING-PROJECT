import React, { useEffect, useMemo, useState } from "react";
import {
  ActivityIndicator,
  Pressable,
  SafeAreaView,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
} from "react-native";
import { onAuthStateChanged, type User } from "firebase/auth";
import { ref, push, query, orderByChild, limitToLast, onValue } from "firebase/database";
import { auth, db, hasFirebaseConfig } from "../lib/firebase";

const API_BASE_URL = process.env.EXPO_PUBLIC_API_URL ?? "http://10.0.2.2:3000";

type AnalysisStatus = "idle" | "loading" | "error" | "safe" | "smishing";

type ClassifyResult = {
  label: string;
  risk_percent_smishing: number | null;
  verdict_plain: string;
  signals_toward_smishing: string[];
  signals_toward_benign: string[];
} | null;

type ScanRecord = {
  id: string;
  text: string;
  label: string;
  risk_percent: number | null;
  verdict: string;
  scanned_at: string;
  source: "web" | "mobile";
};

export default function HomeScreen() {
  const [message, setMessage] = useState<string>("");
  const [status, setStatus] = useState<AnalysisStatus>("idle");
  const [result, setResult] = useState<ClassifyResult>(null);
  const [errorMsg, setErrorMsg] = useState<string>("");
  const [currentUser, setCurrentUser] = useState<User | null>(null);
  const [history, setHistory] = useState<ScanRecord[]>([]);

  useEffect(() => {
    if (!auth || !hasFirebaseConfig) return;
    const unsub = onAuthStateChanged(auth, (user) => setCurrentUser(user));
    return () => unsub();
  }, []);

  useEffect(() => {
    if (!db || !currentUser) {
      setHistory([]);
      return;
    }
    const scansRef = query(
      ref(db, `scans/${currentUser.uid}`),
      orderByChild("scanned_at"),
      limitToLast(10),
    );
    const unsub = onValue(scansRef, (snapshot) => {
      const records: ScanRecord[] = [];
      snapshot.forEach((child) => {
        records.push({ id: child.key!, ...child.val() });
      });
      records.reverse();
      setHistory(records);
    });
    return () => unsub();
  }, [currentUser]);

  const resultText = useMemo(() => {
    switch (status) {
      case "error":
        return errorMsg || "Something went wrong. Please try again.";
      case "loading":
        return "Analyzing...";
      case "smishing":
        return "⚠ Smishing Detected";
      case "safe":
        return "✓ Safe Message";
      default:
        return "Enter an SMS message to analyze.";
    }
  }, [status, errorMsg]);

  const resultTone = useMemo(() => {
    switch (status) {
      case "error":
        return styles.resultError;
      case "smishing":
        return styles.resultDanger;
      case "safe":
        return styles.resultSafe;
      default:
        return styles.resultNeutral;
    }
  }, [status]);

  const onAnalyze = async () => {
    const trimmed = message.trim();
    if (!trimmed) {
      setErrorMsg("Please enter an SMS message.");
      setStatus("error");
      return;
    }

    setStatus("loading");
    setResult(null);
    setErrorMsg("");

    try {
      const res = await fetch(`${API_BASE_URL}/api/classify`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: trimmed, top_k: 5 }),
      });

      if (!res.ok) {
        const body = await res.json().catch(() => null);
        const detail = body?.details ?? body?.error ?? `Server error (${res.status})`;
        setErrorMsg(typeof detail === "string" ? detail : JSON.stringify(detail));
        setStatus("error");
        return;
      }

      const data = await res.json();
      setResult(data);
      setStatus(data.label === "smishing" ? "smishing" : "safe");

      if (db && currentUser) {
        const scanEntry = {
          text: trimmed,
          label: data.label as string,
          risk_percent: data.risk_percent_smishing ?? null,
          verdict: data.verdict_plain as string,
          scanned_at: new Date().toISOString(),
          source: "mobile" as const,
        };
        push(ref(db, `scans/${currentUser.uid}`), scanEntry).catch(() => {});
      }
    } catch (e) {
      setErrorMsg(
        e instanceof TypeError
          ? "Cannot reach the server. Make sure the webapp is running."
          : e instanceof Error
            ? e.message
            : "Unknown error",
      );
      setStatus("error");
    }
  };

  return (
    <SafeAreaView style={styles.safeArea}>
      <ScrollView style={styles.container} contentContainerStyle={{ gap: 14, paddingBottom: 32 }}>
        <Text style={styles.title}>Smishing Detection</Text>
        <Text style={styles.subtitle}>Paste an SMS message below and run a quick risk check.</Text>

        <View style={styles.card}>
          <Text style={styles.label}>SMS Message</Text>
          <TextInput
            value={message}
            onChangeText={(text) => {
              setMessage(text);
              if (status !== "idle" && status !== "loading") {
                setStatus("idle");
                setResult(null);
              }
            }}
            placeholder='e.g. "Your account is locked. Click here to verify."'
            placeholderTextColor="#6b7280"
            multiline
            textAlignVertical="top"
            style={styles.input}
            autoCapitalize="none"
            autoCorrect={false}
            spellCheck={false}
            editable={status !== "loading"}
          />

          <Pressable
            onPress={onAnalyze}
            disabled={status === "loading"}
            style={({ pressed }) => [
              styles.button,
              pressed && styles.buttonPressed,
              status === "loading" && styles.buttonDisabled,
            ]}
            accessibilityRole="button"
            accessibilityLabel="Analyze SMS"
          >
            {status === "loading" ? (
              <ActivityIndicator color="#ffffff" size="small" />
            ) : (
              <Text style={styles.buttonText}>Analyze SMS</Text>
            )}
          </Pressable>
        </View>

        <View style={styles.resultCard} accessibilityRole="summary">
          <Text style={styles.resultLabel}>Result</Text>
          <Text style={[styles.resultText, resultTone]}>{resultText}</Text>

          {result?.risk_percent_smishing != null && (
            <Text style={styles.riskPercent}>
              Risk score: {result.risk_percent_smishing}%
            </Text>
          )}

          {result?.verdict_plain ? (
            <Text style={styles.verdict}>{result.verdict_plain}</Text>
          ) : null}

          {result?.signals_toward_smishing && result.signals_toward_smishing.length > 0 && (
            <View style={styles.signalSection}>
              <Text style={styles.signalHeader}>Smishing signals</Text>
              {result.signals_toward_smishing.map((s, i) => (
                <Text key={i} style={styles.signalItem}>• {s}</Text>
              ))}
            </View>
          )}
        </View>

        {history.length > 0 && (
          <View style={styles.historySection}>
            <Text style={styles.historyTitle}>Scan History</Text>
            <Text style={styles.historySubtitle}>Last {history.length} scans (synced in real time)</Text>
            {history.map((rec) => (
              <View key={rec.id} style={styles.historyCard}>
                <View style={styles.historyRow}>
                  <View
                    style={[
                      styles.historyBadge,
                      rec.label === "smishing" ? styles.badgeSmishing : styles.badgeSafe,
                    ]}
                  >
                    <Text
                      style={[
                        styles.historyBadgeText,
                        rec.label === "smishing" ? styles.badgeTextSmishing : styles.badgeTextSafe,
                      ]}
                    >
                      {rec.label.toUpperCase()}
                    </Text>
                  </View>
                  {rec.risk_percent != null && (
                    <Text style={styles.historyRisk}>{rec.risk_percent}% risk</Text>
                  )}
                  <Text style={styles.historyMeta}>{rec.source}</Text>
                </View>
                <Text style={styles.historyText} numberOfLines={2}>{rec.text}</Text>
                <Text style={styles.historyDate}>{new Date(rec.scanned_at).toLocaleString()}</Text>
              </View>
            ))}
          </View>
        )}
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: "#0b1220",
  },
  container: {
    flex: 1,
    paddingHorizontal: 16,
    paddingTop: 20,
  },
  title: {
    color: "#ffffff",
    fontSize: 26,
    fontWeight: "700",
    letterSpacing: 0.2,
  },
  subtitle: {
    color: "#cbd5e1",
    fontSize: 14,
    lineHeight: 20,
  },
  card: {
    backgroundColor: "#0f1b33",
    borderWidth: 1,
    borderColor: "#1f2a44",
    borderRadius: 14,
    padding: 14,
    gap: 10,
  },
  label: {
    color: "#e5e7eb",
    fontSize: 13,
    fontWeight: "600",
  },
  input: {
    minHeight: 140,
    maxHeight: 240,
    borderWidth: 1,
    borderColor: "#253252",
    backgroundColor: "#0b1220",
    borderRadius: 12,
    paddingHorizontal: 12,
    paddingVertical: 12,
    color: "#ffffff",
    fontSize: 14,
    lineHeight: 20,
  },
  button: {
    backgroundColor: "#2563eb",
    borderRadius: 12,
    paddingVertical: 12,
    alignItems: "center",
  },
  buttonPressed: {
    opacity: 0.9,
  },
  buttonDisabled: {
    opacity: 0.5,
  },
  buttonText: {
    color: "#ffffff",
    fontSize: 15,
    fontWeight: "700",
    letterSpacing: 0.2,
  },
  resultCard: {
    backgroundColor: "#0f1b33",
    borderWidth: 1,
    borderColor: "#1f2a44",
    borderRadius: 14,
    padding: 14,
    gap: 8,
  },
  resultLabel: {
    color: "#e5e7eb",
    fontSize: 13,
    fontWeight: "600",
  },
  resultText: {
    fontSize: 16,
    fontWeight: "700",
  },
  resultNeutral: {
    color: "#cbd5e1",
  },
  resultError: {
    color: "#fbbf24",
  },
  resultDanger: {
    color: "#fb7185",
  },
  resultSafe: {
    color: "#34d399",
  },
  riskPercent: {
    color: "#94a3b8",
    fontSize: 13,
    fontWeight: "600",
  },
  verdict: {
    color: "#cbd5e1",
    fontSize: 13,
    lineHeight: 19,
  },
  signalSection: {
    marginTop: 4,
    gap: 4,
  },
  signalHeader: {
    color: "#e5e7eb",
    fontSize: 13,
    fontWeight: "700",
  },
  signalItem: {
    color: "#94a3b8",
    fontSize: 12,
    lineHeight: 17,
    paddingLeft: 4,
  },
  historySection: {
    marginTop: 10,
    gap: 8,
  },
  historyTitle: {
    color: "#ffffff",
    fontSize: 18,
    fontWeight: "700",
  },
  historySubtitle: {
    color: "#94a3b8",
    fontSize: 12,
  },
  historyCard: {
    backgroundColor: "#0f1b33",
    borderWidth: 1,
    borderColor: "#1f2a44",
    borderRadius: 12,
    padding: 12,
    gap: 6,
  },
  historyRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: 8,
  },
  historyBadge: {
    borderRadius: 10,
    paddingHorizontal: 8,
    paddingVertical: 2,
  },
  badgeSmishing: {
    backgroundColor: "rgba(251,113,133,0.2)",
  },
  badgeSafe: {
    backgroundColor: "rgba(52,211,153,0.2)",
  },
  historyBadgeText: {
    fontSize: 10,
    fontWeight: "700",
    letterSpacing: 0.5,
  },
  badgeTextSmishing: {
    color: "#fb7185",
  },
  badgeTextSafe: {
    color: "#34d399",
  },
  historyRisk: {
    color: "#94a3b8",
    fontSize: 11,
  },
  historyMeta: {
    color: "#64748b",
    fontSize: 10,
    marginLeft: "auto",
  },
  historyText: {
    color: "#cbd5e1",
    fontSize: 13,
    lineHeight: 18,
  },
  historyDate: {
    color: "#64748b",
    fontSize: 10,
  },
});

