import type { WeeklyReport } from "./mock-data";

export function buildMarkdown(report: WeeklyReport): string {
  const lines: string[] = [];
  lines.push(`# BrokerWeeklyIntel — ${report.week}`);
  lines.push(`_${report.week_start} → ${report.week_end} · Report v${report.report_version}_`);
  lines.push("");

  lines.push(`## Broker Leaderboard`);
  lines.push("");
  lines.push("| # | Broker | Rating | Trend | Δ |");
  lines.push("|---|--------|-------:|-------|--:|");
  [...report.brokers]
    .sort((a, b) => b.overall_rating - a.overall_rating)
    .forEach((b, i) => {
      const d = b.previous_rating ? +(b.overall_rating - b.previous_rating).toFixed(1) : 0;
      lines.push(
        `| ${i + 1} | ${b.broker} | ${b.overall_rating.toFixed(1)} | ${b.trend} | ${d > 0 ? "+" : ""}${d.toFixed(1)} |`,
      );
    });
  lines.push("");

  lines.push(`## New Features Launched This Week`);
  lines.push("");
  lines.push("| Broker | Feature/Update | Approx. Launch | User Reaction | Key Evidence/Link |");
  lines.push("|--------|----------------|----------------|---------------|-------------------|");
  report.brokers.forEach((b) =>
    b.new_features.forEach((f) => {
      const link = f.evidence_links[0] ? `[source](${f.evidence_links[0]})` : "—";
      lines.push(
        `| ${b.broker} | ${f.feature_name} | ${f.launch_date} | ${f.user_reaction} | ${link} |`,
      );
    }),
  );
  lines.push("");

  lines.push(`## Technical Issues`);
  lines.push("");
  lines.push("| Broker | Description | Severity | Type | Volume |");
  lines.push("|--------|-------------|----------|------|-------:|");
  report.brokers.forEach((b) =>
    b.technical_issues.forEach((i) => {
      lines.push(
        `| ${b.broker} | ${i.description} | ${i.severity} | ${i.issue_type.replace("_", " ")} | ${i.volume} |`,
      );
    }),
  );
  lines.push("");

  lines.push(`## Industry Themes`);
  lines.push(`**Positive**`);
  report.industry_themes.positive.forEach((t) => lines.push(`- ${t}`));
  lines.push(`\n**Negative**`);
  report.industry_themes.negative.forEach((t) => lines.push(`- ${t}`));
  lines.push(`\n**Emerging**`);
  report.industry_themes.emerging.forEach((t) => lines.push(`- ${t}`));
  if (report.industry_themes.implications_for_socialcoffee) {
    lines.push(`\n## Implications for SocialCoffee\n`);
    lines.push(report.industry_themes.implications_for_socialcoffee);
  }

  return lines.join("\n");
}

export function downloadMarkdown(report: WeeklyReport) {
  const md = buildMarkdown(report);
  const blob = new Blob([md], { type: "text/markdown;charset=utf-8" });
  triggerDownload(blob, `BrokerWeeklyIntel-${report.week}.md`);
}

export async function downloadPDF(report: WeeklyReport) {
  const [{ default: jsPDF }, autoTableMod] = await Promise.all([
    import("jspdf"),
    import("jspdf-autotable"),
  ]);
  const autoTable = (autoTableMod as { default: (doc: unknown, opts: unknown) => void }).default;
  const doc = new jsPDF({ unit: "pt", format: "a4" });
  const margin = 40;

  doc.setFontSize(18);
  doc.text(`BrokerWeeklyIntel — ${report.week}`, margin, 50);
  doc.setFontSize(10);
  doc.setTextColor(120);
  doc.text(
    `${report.week_start} → ${report.week_end}  ·  Report v${report.report_version}`,
    margin,
    66,
  );
  doc.setTextColor(0);

  autoTable(doc, {
    startY: 90,
    head: [["#", "Broker", "Rating", "Trend", "Δ"]],
    body: [...report.brokers]
      .sort((a, b) => b.overall_rating - a.overall_rating)
      .map((b, i) => {
        const d = b.previous_rating ? +(b.overall_rating - b.previous_rating).toFixed(1) : 0;
        return [
          String(i + 1),
          b.broker,
          b.overall_rating.toFixed(1),
          b.trend,
          `${d > 0 ? "+" : ""}${d.toFixed(1)}`,
        ];
      }),
    theme: "striped",
    headStyles: { fillColor: [30, 30, 35] },
    styles: { fontSize: 9 },
  });

  autoTable(doc, {
    head: [["Broker", "Feature / Update", "Launch", "Reaction", "Evidence"]],
    body: report.brokers.flatMap((b) =>
      b.new_features.map((f) => [
        b.broker,
        f.feature_name,
        f.launch_date,
        f.user_reaction,
        f.evidence_links[0] ?? "—",
      ]),
    ),
    theme: "striped",
    headStyles: { fillColor: [30, 30, 35] },
    styles: { fontSize: 8, cellWidth: "wrap" },
    columnStyles: { 4: { cellWidth: 140 } },
    didDrawPage: (data: { settings: { startY: number } }) => {
      if (data.settings.startY === 90) return;
      doc.setFontSize(12);
      doc.text("New Features Launched This Week", margin, 30);
    },
  });

  autoTable(doc, {
    head: [["Broker", "Issue", "Severity", "Type", "Vol"]],
    body: report.brokers.flatMap((b) =>
      b.technical_issues.map((i) => [
        b.broker,
        i.description,
        i.severity,
        i.issue_type.replace("_", " "),
        String(i.volume),
      ]),
    ),
    theme: "striped",
    headStyles: { fillColor: [30, 30, 35] },
    styles: { fontSize: 8 },
  });

  doc.save(`BrokerWeeklyIntel-${report.week}.pdf`);
}

function triggerDownload(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

// ============================================
// ZIP Export (uses custom ZpiIcon in UI)
// ============================================

export async function downloadZIP(report: WeeklyReport) {
  const JSZip = (await import("jszip")).default;
  const zip = new JSZip();

  // 1. Markdown
  const md = buildMarkdown(report);
  zip.file(`BrokerWeeklyIntel-${report.week}.md`, md);

  // 2. PDF (reuse existing logic)
  const pdfBlob = await generatePDFBlob(report);
  zip.file(`BrokerWeeklyIntel-${report.week}.pdf`, pdfBlob);

  // 3. Structured JSON snapshot (great for further analysis)
  zip.file(`BrokerWeeklyIntel-${report.week}.json`, JSON.stringify(report, null, 2));

  // 4. Helpful README
  const readme = `BrokerWeeklyIntel — ${report.week}
Generated: ${new Date().toISOString()}

This archive contains:
- BrokerWeeklyIntel-${report.week}.md — Full Markdown report (ready for Notion, Obsidian, etc.)
- BrokerWeeklyIntel-${report.week}.pdf — Professional PDF version
- BrokerWeeklyIntel-${report.week}.json — Complete structured data (v2.1 schema)

Source: BrokerWeeklyIntel real collection run (Z-Connect, Play Store, community signals)
Report version: ${report.report_version}
`;

  zip.file("README.txt", readme);

  // Generate and download
  const zipBlob = await zip.generateAsync({ type: "blob" });
  triggerDownload(zipBlob, `BrokerWeeklyIntel-${report.week}.zip`);
}

/**
 * Internal helper: generates PDF as Blob instead of directly triggering download.
 * Re-uses most of the downloadPDF logic.
 */
async function generatePDFBlob(report: WeeklyReport): Promise<Blob> {
  const [{ default: jsPDF }, autoTableMod] = await Promise.all([
    import("jspdf"),
    import("jspdf-autotable"),
  ]);
  const autoTable = (autoTableMod as { default: (doc: unknown, opts: unknown) => void }).default;
  const doc = new jsPDF({ unit: "pt", format: "a4" });
  const margin = 40;

  doc.setFontSize(18);
  doc.text(`BrokerWeeklyIntel — ${report.week}`, margin, 50);
  doc.setFontSize(10);
  doc.setTextColor(120);
  doc.text(
    `${report.week_start} → ${report.week_end}  ·  Report v${report.report_version}`,
    margin,
    66,
  );
  doc.setTextColor(0);

  autoTable(doc, {
    startY: 90,
    head: [["#", "Broker", "Rating", "Trend", "Δ"]],
    body: [...report.brokers]
      .sort((a, b) => b.overall_rating - a.overall_rating)
      .map((b, i) => {
        const d = b.previous_rating ? +(b.overall_rating - b.previous_rating).toFixed(1) : 0;
        return [
          String(i + 1),
          b.broker,
          b.overall_rating.toFixed(1),
          b.trend,
          `${d > 0 ? "+" : ""}${d.toFixed(1)}`,
        ];
      }),
    theme: "striped",
    headStyles: { fillColor: [30, 30, 35] },
    styles: { fontSize: 9 },
  });

  autoTable(doc, {
    head: [["Broker", "Feature / Update", "Launch", "Reaction", "Evidence"]],
    body: report.brokers.flatMap((b) =>
      b.new_features.map((f) => [
        b.broker,
        f.feature_name,
        f.launch_date,
        f.user_reaction,
        f.evidence_links[0] ?? "—",
      ]),
    ),
    theme: "striped",
    headStyles: { fillColor: [30, 30, 35] },
    styles: { fontSize: 8, cellWidth: "wrap" },
    columnStyles: { 4: { cellWidth: 140 } },
    didDrawPage: (data: { settings: { startY: number } }) => {
      if (data.settings.startY === 90) return;
      doc.setFontSize(12);
      doc.text("New Features Launched This Week", margin, 30);
    },
  });

  autoTable(doc, {
    head: [["Broker", "Issue", "Severity", "Type", "Vol"]],
    body: report.brokers.flatMap((b) =>
      b.technical_issues.map((i) => [
        b.broker,
        i.description,
        i.severity,
        i.issue_type.replace("_", " "),
        String(i.volume),
      ]),
    ),
    theme: "striped",
    headStyles: { fillColor: [30, 30, 35] },
    styles: { fontSize: 8 },
  });

  return doc.output("blob");
}
