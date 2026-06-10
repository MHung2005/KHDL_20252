/**
 * src/lib/api.js
 * Axios client + mock data fallback khi backend chưa sẵn sàng
 */

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000/api/v1";

// ─── MOCK DATA ──────────────────────────────────────────────────
export const MOCK = {
  summary: {
    total_records: 36450,
    total_platforms: 3,
    total_labeled: 10000,
    total_models: 3,
    platform_stats: [
      { platform: "tiktok",   total_records: 12450, vietnamese_records: 11200, avg_char_count: 128 },
      { platform: "threads",  total_records: 8320,  vietnamese_records: 7890,  avg_char_count: 215 },
      { platform: "facebook", total_records: 15680, vietnamese_records: 14900, avg_char_count: 342 },
    ],
    crawl_timeline: [
      { month: "T1/24", tiktok: 1200, threads: 0,    facebook: 1800 },
      { month: "T2/24", tiktok: 2100, threads: 1200, facebook: 2400 },
      { month: "T3/24", tiktok: 2800, threads: 1800, facebook: 3100 },
      { month: "T4/24", tiktok: 2500, threads: 2100, facebook: 3500 },
      { month: "T5/24", tiktok: 2400, threads: 1980, facebook: 3200 },
      { month: "T6/24", tiktok: 1450, threads: 1240, facebook: 1680 },
    ],
  },

  dataset: {
    total_labeled: 10000,
    data: [
      {
        split_set: "train", total_records: 8000, ratio: 0.80,
        platforms: { tiktok: 3000, threads: 2000, facebook: 3000 },
        labels: { normal: 4500, hate_speech: 2100, offensive: 1400 },
      },
      {
        split_set: "test", total_records: 2000, ratio: 0.20,
        platforms: { tiktok: 740, threads: 480, facebook: 780 },
        labels: { normal: 1130, hate_speech: 540, offensive: 330 },
      },
    ],
  },

  models: [
    {
      model_id: "model-001",
      model_display_name: "TF-IDF + SVM",
      model_type: "traditional",
      version: "v1.0",
      accuracy: 0.7823, macro_f1: 0.7615, weighted_f1: 0.7702,
      macro_precision: 0.7798, macro_recall: 0.7750,
      target_hate_f1: 0.7221, target_offensive_f1: 0.6805, target_normal_f1: 0.8122,
      confusion_matrix: [[1254,178,88],[52,228,32],[28,24,116]],
      train_ratio: 0.80, test_ratio: 0.20, total_samples: 10000,
      evaluated_at: "2024-06-01T10:00:00",
    },
    {
      model_id: "model-002",
      model_display_name: "TF-IDF + LR",
      model_type: "traditional",
      version: "v1.0",
      accuracy: 0.8015, macro_f1: 0.7832, weighted_f1: 0.7910,
      macro_precision: 0.8034, macro_recall: 0.7978,
      target_hate_f1: 0.7370, target_offensive_f1: 0.6973, target_normal_f1: 0.8344,
      confusion_matrix: [[1252,180,88],[45,234,33],[22,30,116]],
      train_ratio: 0.80, test_ratio: 0.20, total_samples: 10000,
      evaluated_at: "2024-06-01T10:30:00",
    },
    {
      model_id: "model-003",
      model_display_name: "PhoBERT",
      model_type: "deep_learning",
      version: "v1.0",
      accuracy: 0.8934, macro_f1: 0.8823, weighted_f1: 0.8876,
      macro_precision: 0.8945, macro_recall: 0.8890,
      target_hate_f1: 0.8732, target_offensive_f1: 0.8612, target_normal_f1: 0.9122,
      confusion_matrix: [[1370,98,52],[22,276,14],[12,14,142]],
      train_ratio: 0.80, test_ratio: 0.20, total_samples: 10000,
      evaluated_at: "2024-06-01T11:00:00",
    },
  ],
};

// ─── FETCH HELPER ───────────────────────────────────────────────
async function apiFetch(path) {
  try {
    const res = await fetch(`${API_BASE}${path}`, {
      next: { revalidate: 30 },
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const json = await res.json();
    return json.data ?? json;
  } catch (err) {
    console.warn(`[API] ${path} failed, using mock data:`, err.message);
    return null;
  }
}

// ─── API FUNCTIONS ──────────────────────────────────────────────
export async function getDashboardSummary() {
  const data = await apiFetch("/dashboard/summary");
  return data ?? MOCK.summary;
}

export async function getPlatformStats() {
  const data = await apiFetch("/dashboard/platform-stats");
  return data ?? MOCK.summary.platform_stats;
}

export async function getCrawlTimeline() {
  const data = await apiFetch("/dashboard/crawl-timeline");
  return data ?? MOCK.summary.crawl_timeline;
}

export async function getLabelDistribution(platform = "") {
  const qs = platform ? `?platform=${platform}` : "";
  const data = await apiFetch(`/dashboard/label-distribution${qs}`);
  return data ?? [
    { label: "normal",      count: 5630 },
    { label: "hate_speech", count: 2640 },
    { label: "offensive",   count: 1730 },
  ];
}

export async function getDatasetOverview() {
  const data = await apiFetch("/datasets/overview");
  return data ?? MOCK.dataset;
}

export async function getModelComparison() {
  const data = await apiFetch("/models/comparison");
  return data ?? MOCK.models;
}

// ─── UTILS ─────────────────────────────────────────────────────
export const fmt  = (n) => (n ?? 0).toLocaleString("vi-VN");
export const pct  = (v) => `${((v ?? 0) * 100).toFixed(1)}%`;
export const pctN = (v) => `${(v ?? 0).toFixed(1)}%`;

export const PLATFORM_COLORS = {
  tiktok:   "#00f2ea",
  threads:  "#a78bfa",
  facebook: "#60a5fa",
};
export const PLATFORM_ICONS = {
  tiktok: "TK", threads: "@", facebook: "fb",
};
export const LABEL_COLORS = {
  normal:      "#34d399",
  hate_speech: "#f87171",
  offensive:   "#fb923c",
};
export const MODEL_COLORS = ["#38bdf8", "#a78bfa", "#f472b6"];
