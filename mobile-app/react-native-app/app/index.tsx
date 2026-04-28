import React, { useMemo, useState } from "react";
import { Pressable, SafeAreaView, StyleSheet, Text, TextInput, View } from "react-native";

type AnalysisStatus = "idle" | "error" | "safe" | "smishing";

function analyzeSmishing(message: string): AnalysisStatus {
  const trimmed = message.trim();
  if (!trimmed) return "error";

  const suspiciousKeywords = ["verify", "urgent", "account", "click here"];
  const lower = trimmed.toLowerCase();

  const isSmishing = suspiciousKeywords.some((k) => lower.includes(k));
  return isSmishing ? "smishing" : "safe";
}

export default function HomeScreen() {
  const [message, setMessage] = useState<string>("");
  const [status, setStatus] = useState<AnalysisStatus>("idle");

  const resultText = useMemo(() => {
    switch (status) {
      case "error":
        return "Please enter an SMS message";
      case "smishing":
        return "⚠ Smishing Detected";
      case "safe":
        return "✓ Safe Message";
      default:
        return "Enter an SMS message to analyze.";
    }
  }, [status]);

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

  const onAnalyze = () => {
    setStatus(analyzeSmishing(message));
  };

  return (
    <SafeAreaView style={styles.safeArea}>
      <View style={styles.container}>
        <Text style={styles.title}>Smishing Detection</Text>
        <Text style={styles.subtitle}>Paste an SMS message below and run a quick risk check.</Text>

        <View style={styles.card}>
          <Text style={styles.label}>SMS Message</Text>
          <TextInput
            value={message}
            onChangeText={(text) => {
              setMessage(text);
              if (status !== "idle") setStatus("idle");
            }}
            placeholder='e.g. "Your account is locked. Click here to verify."'
            placeholderTextColor="#6b7280"
            multiline
            textAlignVertical="top"
            style={styles.input}
            autoCapitalize="none"
            autoCorrect={false}
            spellCheck={false}
          />

          <Pressable
            onPress={onAnalyze}
            style={({ pressed }) => [styles.button, pressed && styles.buttonPressed]}
            accessibilityRole="button"
            accessibilityLabel="Analyze SMS"
          >
            <Text style={styles.buttonText}>Analyze SMS</Text>
          </Pressable>
        </View>

        <View style={styles.resultCard} accessibilityRole="summary">
          <Text style={styles.resultLabel}>Result</Text>
          <Text style={[styles.resultText, resultTone]}>{resultText}</Text>
        </View>
      </View>
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
    gap: 14,
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
});

