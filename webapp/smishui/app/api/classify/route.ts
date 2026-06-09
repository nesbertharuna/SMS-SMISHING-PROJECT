import { NextResponse } from "next/server";
import os from "os";
import path from "path";
import fs from "fs";
import { spawn } from "child_process";

type ClassifyRequest = {
  text: string;
  top_k?: number;
};

function findPythonExe(repoRoot: string): string {
  const isWindows = os.platform() === "win32";
  const venvPython = isWindows
    ? path.join(repoRoot, ".venv", "Scripts", "python.exe")
    : path.join(repoRoot, ".venv", "bin", "python");

  if (fs.existsSync(venvPython)) return venvPython;

  // Fallback: system python
  return isWindows ? "python" : "python3";
}

export async function POST(req: Request) {
  try {
    const body = (await req.json()) as ClassifyRequest;
    const text = (body.text ?? "").toString().trim();
    const topK = Number.isFinite(body.top_k) ? Number(body.top_k) : 10;

    if (!text) {
      return NextResponse.json({ error: "text is required" }, { status: 400 });
    }

    // Next dev server runs from webapp/smishui. Repo root is two levels up.
    const repoRoot = path.resolve(process.cwd(), "..", "..");
    const pythonExe = findPythonExe(repoRoot);
    const scriptPath = path.join(repoRoot, "ml-backend", "api", "classify.py");

    const artifactRel = "ml-backend/artifacts/pipeline_lr_tfidf.joblib";
    const artifactAbs = path.join(repoRoot, artifactRel);
    if (!fs.existsSync(artifactAbs)) {
      return NextResponse.json(
        {
          error: "model_not_trained",
          details:
            "The ML model artifact was not found. Please run the training pipeline first " +
            "(see RUN_PIPELINE.md) to generate the model before classifying messages.",
        },
        { status: 503 },
      );
    }

    const payload = JSON.stringify({
      text,
      top_k: topK,
      artifact: "ml-backend/artifacts/pipeline_lr_tfidf.joblib",
    });

    const result = await new Promise<{ stdout: string; stderr: string; code: number }>((resolve) => {
      const child = spawn(pythonExe, [scriptPath], {
        cwd: repoRoot,
        windowsHide: true,
        stdio: ["pipe", "pipe", "pipe"],
      });

      let stdout = "";
      let stderr = "";

      child.stdout.on("data", (d) => {
        stdout += d.toString();
      });
      child.stderr.on("data", (d) => {
        stderr += d.toString();
      });

      child.on("close", (code) => resolve({ stdout, stderr, code: code ?? 0 }));
      child.stdin.write(payload);
      child.stdin.end();
    });

    if (result.code !== 0) {
      return NextResponse.json(
        { error: "python_classify_failed", details: result.stderr || result.stdout },
        { status: 500 },
      );
    }

    const json = JSON.parse(result.stdout);
    return NextResponse.json(json);
  } catch (e) {
    const msg = e instanceof Error ? e.message : "Unknown error";
    return NextResponse.json({ error: "request_failed", details: msg }, { status: 500 });
  }
}

