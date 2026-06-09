"use client";

export type PdfClassifyResult = {
  label: "benign" | "smishing";
  risk_percent_smishing: number | null;
  verdict_plain: string;
  signals_toward_smishing: string[];
  signals_toward_benign: string[];
  explanation_note?: string;
};

type PdfReportInput = {
  submittedText: string;
  result: PdfClassifyResult;
  exportedAt?: Date;
};

type JsPdfDoc = import("jspdf").jsPDF & {
  lastAutoTable?: {
    finalY: number;
  };
};

const PAGE_MARGIN_X = 40;
const CONTENT_WIDTH = 515;
const PAGE_BOTTOM_BUFFER = 80;

function formatDisplayTimestamp(date: Date): string {
  return date.toLocaleString();
}

function formatFilenameTimestamp(date: Date): string {
  const pad = (value: number) => value.toString().padStart(2, "0");
  return [
    date.getFullYear(),
    pad(date.getMonth() + 1),
    pad(date.getDate()),
    "-",
    pad(date.getHours()),
    pad(date.getMinutes()),
    pad(date.getSeconds()),
  ].join("");
}

function getRiskText(result: PdfClassifyResult): string {
  if (result.risk_percent_smishing === null || Number.isNaN(result.risk_percent_smishing)) {
    return "Not available";
  }
  return `${result.risk_percent_smishing}%`;
}

function normalizePdfText(text: string): string {
  return text
    .replace(/\r\n/g, "\n")
    .replace(/\u2018|\u2019/g, "'")
    .replace(/\u201C|\u201D/g, '"')
    .replace(/\u2013|\u2014/g, "-")
    .replace(/\u2026/g, "...")
    .replace(/\u00A0/g, " ")
    .replace(/[^\x09\x0A\x0D\x20-\x7E]/g, " ");
}

function softenLongTokens(text: string, maxChunkLength = 32): string {
  return text
    .split(/\s+/)
    .map((token) => {
      if (token.length <= maxChunkLength) return token;

      const urlFriendly = token.replace(/([/?&=_#%-])/g, "$1 ");
      if (urlFriendly !== token) return urlFriendly;

      const chunks: string[] = [];
      for (let i = 0; i < token.length; i += maxChunkLength) {
        chunks.push(token.slice(i, i + maxChunkLength));
      }
      return chunks.join(" ");
    })
    .join(" ");
}

function preparePdfText(text: string): string {
  return softenLongTokens(normalizePdfText(text)).replace(/\s+\n/g, "\n").trim();
}

function ensureRoom(doc: JsPdfDoc, y: number): number {
  const pageHeight = doc.internal.pageSize.getHeight();
  if (y > pageHeight - PAGE_BOTTOM_BUFFER) {
    doc.addPage();
    return 40;
  }
  return y;
}

function appendWrappedText(
  doc: JsPdfDoc,
  title: string,
  text: string,
  startY: number,
  maxWidth: number,
  fontName: "helvetica" | "courier" = "helvetica",
): number {
  let y = ensureRoom(doc, startY);
  const cleanText = preparePdfText(text) || "None.";

  doc.setFont("helvetica", "bold");
  doc.setFontSize(12);
  doc.text(title, PAGE_MARGIN_X, y);
  y += 18;

  doc.setFont(fontName, "normal");
  doc.setFontSize(11);
  const wrappedLines = doc.splitTextToSize(cleanText, maxWidth);
  doc.text(wrappedLines, PAGE_MARGIN_X, y);

  return y + wrappedLines.length * 15 + 12;
}

function appendBulletSection(
  doc: JsPdfDoc,
  title: string,
  rows: string[],
  startY: number,
): number {
  let y = ensureRoom(doc, startY);
  if (rows.length === 0) {
    return appendWrappedText(doc, title, "None.", y, CONTENT_WIDTH);
  }

  doc.setFont("helvetica", "bold");
  doc.setFontSize(12);
  doc.text(title, PAGE_MARGIN_X, y);
  y += 18;

  doc.setFont("helvetica", "normal");
  doc.setFontSize(10);

  for (const row of rows) {
    y = ensureRoom(doc, y);
    const wrappedLines = doc.splitTextToSize(`- ${preparePdfText(row)}`, CONTENT_WIDTH);
    doc.text(wrappedLines, PAGE_MARGIN_X, y);
    y += wrappedLines.length * 13 + 6;
  }

  return y + 6;
}

export async function downloadSmishingReportPdf(input: PdfReportInput): Promise<void> {
  const { jsPDF } = await import("jspdf");
  const autoTable = (await import("jspdf-autotable")).default;

  const exportedAt = input.exportedAt ?? new Date();
  const doc = new jsPDF({ unit: "pt", format: "a4" }) as JsPdfDoc;
  const filename = `smishing-report-${formatFilenameTimestamp(exportedAt)}.pdf`;

  doc.setFont("helvetica", "bold");
  doc.setFontSize(18);
  doc.text("Smishing Analysis Report", PAGE_MARGIN_X, 48);

  doc.setFont("helvetica", "normal");
  doc.setFontSize(11);
  doc.setTextColor(80);
  doc.text(`Generated: ${formatDisplayTimestamp(exportedAt)}`, PAGE_MARGIN_X, 68);
  doc.setTextColor(0);

  autoTable(doc, {
    startY: 88,
    theme: "grid",
    margin: { left: PAGE_MARGIN_X, right: PAGE_MARGIN_X },
    head: [["Field", "Value"]],
    body: [
      ["Predicted label", input.result.label],
      ["Risk score", getRiskText(input.result)],
      ["Verdict summary", input.result.verdict_plain],
    ],
    styles: {
      font: "helvetica",
      fontSize: 10,
      cellPadding: 5,
      overflow: "linebreak",
    },
    headStyles: {
      fontStyle: "bold",
    },
    columnStyles: {
      0: { cellWidth: 130 },
      1: { cellWidth: 385 },
    },
  });

  let currentY = (doc.lastAutoTable?.finalY ?? 120) + 18;

  currentY = appendWrappedText(
    doc,
    "Submitted SMS",
    input.submittedText || "No SMS text provided.",
    currentY,
    CONTENT_WIDTH,
    "courier",
  );
  currentY = appendBulletSection(
    doc,
    "Signals toward smishing",
    input.result.signals_toward_smishing,
    currentY,
  );
  currentY = appendBulletSection(
    doc,
    "Signals toward benign",
    input.result.signals_toward_benign,
    currentY,
  );

  appendWrappedText(
    doc,
    "Disclaimer",
    input.result.explanation_note ||
      "This report reflects a model-generated assessment and should be interpreted as decision support, not proof.",
    currentY,
    CONTENT_WIDTH,
  );

  doc.save(filename);
}
