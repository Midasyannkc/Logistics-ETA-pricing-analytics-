const pptxgen = require("pptxgenjs");

const NAVY = "1F2A44";
const ORANGE = "E4832A";
const GRAY = "5A5A5A";
const WHITE = "FFFFFF";

const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE";

function titleSlide() {
  const s = pres.addSlide();
  s.background = { color: NAVY };
  s.addText("Logistics ETA &\nDynamic Pricing Analytics", {
    x: 0.8, y: 2.0, w: 11.7, h: 2.2,
    fontSize: 40, bold: true, color: WHITE, fontFace: "Arial",
    lineSpacingMultiple: 1.05,
  });
  s.addText("KPI Walkthrough  |  Databricks + BigQuery + Go + Tableau + Omni", {
    x: 0.8, y: 4.2, w: 11.7, h: 0.5,
    fontSize: 16, color: "F0C199", fontFace: "Arial",
  });
  s.addText("Christian Kouadio Kouassi", {
    x: 0.8, y: 6.6, w: 6, h: 0.4,
    fontSize: 12, color: "C79A6E", fontFace: "Arial",
  });
}

function sectionHeader(title, kicker) {
  const s = pres.addSlide();
  s.background = { color: WHITE };
  s.addText(kicker.toUpperCase(), {
    x: 0.8, y: 0.6, w: 8, h: 0.4,
    fontSize: 13, color: ORANGE, bold: true, fontFace: "Arial", charSpacing: 1,
  });
  s.addText(title, {
    x: 0.8, y: 1.0, w: 11.5, h: 0.9,
    fontSize: 30, bold: true, color: NAVY, fontFace: "Arial",
  });
  return s;
}

function bulletBlock(s, items, opts) {
  const o = Object.assign({ x: 0.8, y: 2.1, w: 11.5, h: 4.5, fontSize: 16 }, opts);
  s.addText(
    items.map((t, i) => ({
      text: t,
      options: { bullet: { code: "2022" }, breakLine: i !== items.length - 1, paraSpaceAfter: 14 },
    })),
    { x: o.x, y: o.y, w: o.w, h: o.h, fontSize: o.fontSize, color: NAVY, fontFace: "Arial", valign: "top", margin: 0 }
  );
}

// 1. Title
titleSlide();

// 2. Problem & Context
{
  const s = sectionHeader("The Problem", "Context");
  bulletBlock(s, [
    "A logistics platform needs to predict delivery ETAs and adjust pricing in real time, on the request hot path.",
    "Engineering and business teams both need visibility into model performance and pricing outcomes, without waiting on data eng for every new report.",
    "Legacy BI (Tableau) is entrenched with execs; a newer semantic-layer tool (Omni) is being adopted for self-serve analytics during the transition.",
  ]);
}

// 3. Data Source
{
  const s = sectionHeader("Where the Data Comes From", "Data Source");
  bulletBlock(s, [
    "Simulated trip request events: pickup distance, regional demand index, surge multiplier, predicted vs. actual ETA, conversion outcome.",
    "Generated to mirror real peak-hour demand and congestion patterns (morning/evening commute spikes).",
    "20,000 synthetic trip requests across 5 regions over a 60-day window.",
  ]);
}

// 4. What We're Testing For
{
  const s = sectionHeader("What We're Testing For", "Hypothesis");
  bulletBlock(s, [
    "Whether a correction model trained on regional demand and time-of-day context meaningfully improves ETA accuracy over the raw prediction.",
    "Whether surge pricing changes correlate with reduced conversion, the tradeoff a pricing engine has to balance against revenue.",
    "Whether driver/dasher availability or raw demand is the binding constraint on conversion.",
  ]);
}

// 5. Stack & Rationale
{
  const s = sectionHeader("Stack & Why It Fits", "Architecture");
  const rows = [
    ["Layer", "Tool", "Why"],
    ["Feature engineering / ML", "Databricks", "Streaming ingestion + ETA model training together (medallion architecture)"],
    ["Serving warehouse", "BigQuery", "Fast, cheap for aggregated KPI queries"],
    ["Real-time serving", "Go", "Request hot path, target p99 < 50ms, matches real dispatch/pricing services"],
    ["Legacy/exec BI", "Tableau", "Existing exec-facing dashboard tooling"],
    ["Self-serve BI", "Omni", "Semantic layer, no duplicated metric logic across teams"],
  ];
  s.addTable(rows, {
    x: 0.8, y: 2.0, w: 11.5, h: 4.0,
    fontSize: 13, fontFace: "Arial",
    border: { type: "solid", color: "DDDDDD", pt: 1 },
    autoPage: false,
    color: NAVY,
    fill: { color: WHITE },
    valign: "middle",
    rowH: 0.6,
  });
}

// 6. Task
{
  const s = sectionHeader("The Task", "Scope");
  bulletBlock(s, [
    "Build streaming ingestion and the Bronze/Silver/Gold feature table on Databricks.",
    "Train an ETA correction model and evaluate it against the raw prediction baseline.",
    "Implement the Go real-time quote service for ETA + surge pricing.",
    "Expose gold KPI views in BigQuery to both Tableau and Omni, and validate they return identical numbers.",
  ]);
}

// 7. Results - charts
{
  const s = sectionHeader("Results", "KPI Snapshot");
  s.addImage({ path: "../charts/eta_error_comparison.png", x: 0.6, y: 1.9, w: 3.9, h: 2.79 });
  s.addImage({ path: "../charts/pricing_elasticity.png", x: 4.7, y: 1.9, w: 4.3, h: 2.69 });
  s.addImage({ path: "../charts/utilization_by_region.png", x: 9.15, y: 1.9, w: 3.55, h: 2.54 });
  bulletBlock(s, [
    "ETA MAE improves from 2.00 to 1.63 minutes (RMSE 2.53 to 2.04) with the demand-aware correction model.",
    "Conversion drops from 87.6% at low surge (1.0-1.1x) to 59.9% at high surge (2.0-2.5x), a clear elasticity signal.",
    "Driver availability holds steady (~80-82%) across regions and tracks closely with conversion (~72-74%), pointing to utilization as the binding constraint.",
  ], { y: 4.85, h: 2.3, fontSize: 13 });
}

pres.writeFile({ fileName: "kpi_walkthrough.pptx" }).then(() => {
  console.log("Deck written: kpi_walkthrough.pptx");
});
