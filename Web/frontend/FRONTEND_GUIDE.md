# Frontend Build Guide — Hate Speech Dashboard

## Cấu trúc thư mục

```
frontend/
├── package.json                 ← dependencies (Next.js 14, Recharts, Tailwind)
├── next.config.js               ← cấu hình API base URL
├── tailwind.config.js           ← design tokens, màu sắc, font
├── postcss.config.js
│
└── src/
    ├── app/                     ← Next.js App Router (pages)
    │   ├── globals.css          ← Tailwind base + font import + custom styles
    │   ├── layout.js            ← Root layout (HTML wrapper)
    │   ├── page.js              ← /          → Dashboard
    │   ├── dataset/
    │   │   └── page.js          ← /dataset   → Quản lý Dataset
    │   └── models/
    │       └── page.js          ← /models    → Đánh giá Mô hình
    │
    ├── components/
    │   ├── ui/
    │   │   └── index.js         ← StatCard, Card, Badge, Loader, ProgressBar, ChartTooltip...
    │   ├── charts/
    │   │   └── ConfusionMatrix.js ← Component ma trận nhầm lẫn
    │   └── layout/
    │       ├── Sidebar.js       ← Thanh điều hướng trái
    │       └── AppShell.js      ← Layout wrapper (sidebar + main)
    │
    └── lib/
        └── api.js               ← API fetch functions + mock data + utilities
```

---

## Cài đặt & Chạy

### Bước 1 — Cài Node.js
Yêu cầu Node.js >= 18. Kiểm tra:
```bash
node -v   # >= 18.x
npm -v    # >= 9.x
```

Nếu chưa có, tải tại: https://nodejs.org

### Bước 2 — Cài dependencies
```bash
cd frontend
npm install
```

### Bước 3 — Cấu hình API (tuỳ chọn)
Tạo file `.env.local` nếu backend chạy ở địa chỉ khác:
```
NEXT_PUBLIC_API_BASE=http://localhost:8000/api/v1
```
Mặc định đã trỏ đến `http://localhost:8000/api/v1`.
Nếu backend chưa chạy, hệ thống tự dùng **mock data** — không cần Hadoop.

### Bước 4 — Chạy dev server
```bash
npm run dev
```
Mở trình duyệt: **http://localhost:3000**

### Bước 5 — Build production
```bash
npm run build
npm start
```

---

## Các trang

| URL       | Trang               | Nội dung                                           |
|-----------|---------------------|----------------------------------------------------|
| `/`       | Dashboard           | KPI cards, Pie chart, Bar chart, Line chart timeline, Platform cards |
| `/dataset`| Quản lý Dataset     | Train/Test split, label distribution, platform breakdown, detail table |
| `/models` | Đánh giá Mô hình   | Comparison table, Bar chart, Radar chart, Confusion Matrix |

---

## Biểu đồ sử dụng (Recharts)

| Trang    | Biểu đồ                          |
|----------|----------------------------------|
| Dashboard | PieChart, BarChart, LineChart, PieChart (label donut) |
| Dataset   | PieChart (split), BarChart (platform), BarChart (label) |
| Models    | BarChart (comparison), RadarChart, ConfusionMatrix (custom HTML) |

---

## Kết nối với Backend

Sửa `src/lib/api.js` để thêm endpoint thực:

```js
// Ví dụ lấy dữ liệu thật từ Hive qua FastAPI
export async function getDashboardSummary() {
  const data = await apiFetch("/dashboard/summary");
  return data ?? MOCK.summary;   // fallback mock nếu API lỗi
}
```

---

## Mock Data vs Real API

Không cần thay đổi gì — hàm `apiFetch()` tự fallback:
- ✅ API trả về → dùng data thật
- ✅ API lỗi / chưa chạy → tự dùng `MOCK.*` trong `src/lib/api.js`

Để buộc dùng mock (offline dev):
```js
// src/lib/api.js — đổi hàm apiFetch:
async function apiFetch(path) {
  return null; // luôn trả null → trigger mock
}
```
