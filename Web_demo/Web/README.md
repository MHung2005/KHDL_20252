# Hate Speech Detection — Management System

Hệ thống Website quản lý dữ liệu và kết quả huấn luyện mô hình Hate Speech Detection,
sử dụng hệ sinh thái Hadoop (HDFS + Hive) làm storage layer.

---

## 📁 Cấu trúc thư mục

```
hate-speech-system/
│
├── hive/                               # Hive DDL & SQL Scripts
│   └── schema.sql                      ✅ DDL tất cả bảng + views + seed data
│
├── backend/                            # FastAPI Python Backend
│   ├── main.py                         ✅ App entry point, CORS, router registration
│   ├── requirements.txt                ✅ Python dependencies
│   ├── .env                            # Environment variables (tạo từ .env.example)
│   ├── .env.example
│   └── app/
│       ├── __init__.py
│       ├── config.py                   ✅ Settings (Hive host, HDFS, CORS)
│       ├── database.py                 ✅ HiveConnection, HDFSConnection, MockDataService
│       └── routers/
│           ├── __init__.py
│           ├── dashboard.py            ✅ GET /api/v1/dashboard/summary|platform-stats|crawl-timeline|label-distribution
│           ├── datasets.py             ✅ GET /api/v1/datasets/overview|detail|hdfs-files
│           └── models.py               ✅ GET /api/v1/models/|comparison|{model_id}
│
└── frontend/                           # React + Recharts Frontend
    ├── package.json
    ├── index.html
    ├── vite.config.js
    └── src/
        ├── main.jsx
        └── App.jsx                     ✅ Dashboard + Dataset + Model Evaluation pages
```

---

## 🗄 Kiến trúc hệ thống

```
┌─────────────────────────────────────────────────────────────┐
│                        FRONTEND                              │
│   React.js + Recharts + Tailwind                            │
│   Dashboard │ Dataset Manager │ Model Evaluation            │
└──────────────────────┬──────────────────────────────────────┘
                       │ REST API (JSON)
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                     BACKEND (FastAPI)                        │
│   /api/v1/dashboard  │  /api/v1/datasets  │ /api/v1/models  │
│                   HiveConnection                             │
│                   HDFSConnection                             │
└──────────┬─────────────────────────────────────┬────────────┘
           │ pyhive (Thrift)                      │ hdfs (WebHDFS)
           ▼                                      ▼
┌──────────────────────┐               ┌──────────────────────┐
│   Apache Hive        │               │   Apache HDFS        │
│   HiveServer2 :10000 │               │   NameNode :9870     │
│                      │               │                      │
│   hate_speech_db     │               │   /data/raw/         │
│   ├─ raw_crawled_data│               │   /data/processed/   │
│   ├─ processed_data  │               │   /models/           │
│   ├─ model_registry  │               │                      │
│   └─ model_eval_... │               │                      │
└──────────────────────┘               └──────────────────────┘
```

---

## 🗃 Hive Tables

| Bảng                       | Mô tả                                  | Format  |
|----------------------------|----------------------------------------|---------|
| `raw_crawled_data`         | Dữ liệu thô từ TikTok/Threads/Facebook | Parquet |
| `processed_data`           | Dữ liệu đã xử lý + gán nhãn           | Parquet |
| `model_registry`           | Registry mô hình đã huấn luyện        | ORC     |
| `model_evaluation_results` | Kết quả đánh giá chi tiết             | ORC     |
| `crawl_sessions`           | Lịch sử phiên crawl                   | ORC     |

### Views tiện ích
- `v_platform_stats` — thống kê theo nền tảng
- `v_dataset_split_stats` — thống kê Train/Test/Validation
- `v_model_comparison` — so sánh mô hình (join model_registry + eval)

---

## 🚀 API Endpoints

### Dashboard
| Method | Path                              | Mô tả                            |
|--------|-----------------------------------|----------------------------------|
| GET    | `/api/v1/dashboard/summary`       | KPI tổng quan + timeline         |
| GET    | `/api/v1/dashboard/platform-stats`| Thống kê từng nền tảng           |
| GET    | `/api/v1/dashboard/crawl-timeline`| Timeline crawl theo tháng        |
| GET    | `/api/v1/dashboard/label-distribution` | Phân phối nhãn              |

### Datasets
| Method | Path                         | Mô tả                            |
|--------|------------------------------|----------------------------------|
| GET    | `/api/v1/datasets/overview`  | Train/Test split overview        |
| GET    | `/api/v1/datasets/detail`    | Chi tiết có thể filter           |
| GET    | `/api/v1/datasets/hdfs-files`| Liệt kê file HDFS                |

### Models
| Method | Path                          | Mô tả                           |
|--------|-------------------------------|----------------------------------|
| GET    | `/api/v1/models/`             | Danh sách tất cả mô hình        |
| GET    | `/api/v1/models/comparison`   | So sánh đầy đủ + confusion matrix |
| GET    | `/api/v1/models/{model_id}`   | Chi tiết một mô hình            |

---

## ⚙️ Cài đặt & Chạy

### 1. Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Tạo file .env
cp .env.example .env
# Chỉnh sửa HIVE_HOST, HDFS_HOST, USE_MOCK_DATA=true (nếu chưa có Hadoop)

uvicorn main:app --reload --port 8000
# Swagger UI: http://localhost:8000/docs
```

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
# App: http://localhost:3000
```

### 3. Hive Setup (nếu có Hadoop)

```bash
# Đăng nhập Hive và chạy DDL
hive -f hive/schema.sql

# Hoặc dùng Beeline
beeline -u "jdbc:hive2://localhost:10000" -f hive/schema.sql
```

### 4. .env.example

```
# Môi trường chạy
DEBUG_MODE=True
USE_MOCK_DATA=False

# Cấu hình HDFS
HDFS_HOST=localhost
HDFS_PORT=9870
HDFS_RPC_PORT=9000
HDFS_USER=hadoop
HDFS_RAW_DATA_DIR=/data/raw
ALLOWED_ORIGINS=["http://localhost:3000"]
```

---

## 📊 Mô hình đã tích hợp

| Mô hình                       | Loại          | Accuracy | Macro F1 |
|-------------------------------|---------------|----------|----------|
| TF-IDF + SVM                  | Traditional   | 78.23%   | 76.15%   |
| TF-IDF + Logistic Regression  | Traditional   | 80.15%   | 78.32%   |
| PhoBERT + Classification Head | Deep Learning | **89.34%** | **88.23%** |

---

## 🎯 Frontend Screens

1. **Dashboard** — KPI cards, Pie chart phân phối nền tảng, Bar chart so sánh,
   Line chart timeline crawl, Platform detail cards.

2. **Dataset Manager** — Train/Test ratio donut, label distribution bar chart,
   per-platform breakdown.

3. **Model Evaluation** — Comparison table với best highlighting, Grouped bar chart,
   Radar chart đa chiều, Confusion Matrix tương tác (click từng model để xem).




python -m uvicorn main:app --reload --port 8000