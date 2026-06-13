================================================================================
         HỆ THỐNG PHÁT HIỆN NGÔN NGỮ THÙ ĐỊCH (HATE SPEECH DETECTION)
                          HƯỚNG DẪN CÀI ĐẶT & CHẠY DỰ ÁN
================================================================================

MỤC LỤC
--------
  1.  Tổng quan hệ thống
  2.  Cấu trúc thư mục
  3.  Yêu cầu môi trường
  4.  Các gói phần mềm sử dụng
  5.  Hướng dẫn chạy từng thành phần
      5.1  Crawl dữ liệu (AI/Crawl_data)
      5.2  Tiền xử lý & EDA (AI/Preprocessing & AI/EDA)
      5.3  Gán nhãn (AI/Model_and_evaluate/Labeling)
      5.4  Tổng hợp nhãn Hard Voting
      5.5  Continued Pretraining PhoBERT
      5.6  Fine-tuning & Đánh giá PhoBERT
      5.7  Extension Chrome (Extension/threads-scrolling-main)
      5.8  Web Demo với HDFS (Web_demo)
  6.  Biến môi trường (.env)

================================================================================
1. TỔNG QUAN HỆ THỐNG
================================================================================

Dự án xây dựng pipeline đầu cuối phát hiện ngôn ngữ thù địch trên mạng xã hội
tiếng Việt, gồm 4 thành phần chính:

  [A] AI 	        — Crawl → Tiền xử lý → EDA → Gán nhãn → Huấn luyện
  [B] Chrome Extension  — Phát hiện hate speech trực tiếp trên trang Threads
  [C] Web Dashboard     — Hiển thị biểu đồ EDA (FastAPI + Next.js)
  [D] Big Data Layer    — HDFS + PySpark lưu trữ & truy vấn dữ liệu lớn

================================================================================
2. CẤU TRÚC THƯ MỤC
================================================================================

├── AI/
│   ├── Crawl_data/
│   │   ├── Threads/threads.py          # Crawl bình luận từ Threads (Selenium)
│   │   ├── Tiktok/tiktok.py            # Crawl bình luận từ TikTok (Playwright)
│   │   └── requirements.txt
│   │
│   ├── Preprocessing/
│   │   └── preprocessing.ipynb         # Chuẩn hóa văn bản tiếng Việt
│   │
│   ├── EDA/
│   │   └── EDA.ipynb                   # Phân tích khám phá dữ liệu
│   │
│   └── Model_and_evaluate/
│       ├── Labeling/
│       │   ├── labeling_with_Qwen.ipynb  # Gán nhãn tự động với Qwen 2.5 7B
│       │   └── HardVoting.ipynb          # Tổng hợp nhãn bằng Hard Voting
│       └── PreTrain_SFT_Eval_PhoBERT/
│           ├── phobert-pretrain.ipynb    # Continued Pretraining PhoBERT
│           └── SFT_and_Evaluate_PhoBert.ipynb  # Fine-tuning & Đánh giá
│
├── Extension/
│   └── threads-scrolling-main/
│       ├── backend/
│       │   ├── main.py                 # FastAPI backend cho extension
│       │   └── evaluator.py            # Logic phân loại dùng PhoBERT
│       ├── extension/
│       │   ├── manifest.json           # Manifest Chrome Extension
│       │   ├── content.js              # Script quét DOM Threads
│       │   └── background.js           # Service worker gọi API Python
│       └── requirements.txt
│
└── Web_demo/
    ├── docker-compose.yml              # Khởi động Hadoop (NameNode + DataNode)
    ├── requirements.txt                # Python deps cho toàn bộ web demo
    ├── DataIO/
    │   └── import_data.py             # Nạp dữ liệu CSV lên HDFS
    └── Web/
        ├── backend/
        │   ├── main.py                # FastAPI app chính
        │   ├── database.py            # SparkDataEngine + HDFSConnection
        │   ├── export_data.py         # Module truy vấn PySpark
        │   └── app/
        │       ├── config.py          # Biến môi trường (pydantic-settings)
        │       └── routers/
        │           └── dashboard.py   # Các API endpoint EDA
        └── frontend/
            ├── package.json
            ├── next.config.js
            ├── tailwind.config.js
            └── src/
                ├── app/               # Next.js App Router
                ├── components/        # UI components 
                └── lib/api.js         # API client
================================================================================
3. YÊU CẦU MÔI TRƯỜNG
================================================================================

  CHUNG
  -----
  - Python       : >= 3.10
  - Node.js      : >= 18.x
  - npm          : >= 9.x
  - Git          : >= 2.x
  - Docker       : >= 24.x (chỉ cần cho Web Demo với Hadoop)
  - Docker Compose: >= 2.x

  NỀN TẢNG CLOUD (cho các bước AI nặng)
  ----------------------------------------
  - Kaggle Notebook  : Gán nhãn Qwen, Pretraining PhoBERT
                       (GPU RTX 6000 Pro khuyến nghị)
  - Google Colab     : Hard Voting, Fine-tuning PhoBERT (GPU T4)

================================================================================
4. CÁC GÓI PHẦN MỀM SỬ DỤNG
================================================================================

4.1  AI/Crawl_data  (requirements.txt)
---------------------------------------
  pandas             — Xử lý và lưu dữ liệu CSV
  numpy              — Tính toán mảng số
  pyarrow            — Đọc/ghi Parquet
  selenium           — Điều khiển Chrome để crawl Threads
  webdriver-manager  — Tự động tải ChromeDriver phù hợp
  playwright         — Crawl TikTok (async, headless Chromium)

  Cài thêm sau khi cài playwright:
    python -m playwright install chromium

4.2  Extension/threads-scrolling-main  (requirements.txt)
-----------------------------------------------------------
  fastapi            — Web framework cho backend extension
  uvicorn            — ASGI server
  torch              — PyTorch (inference PhoBERT)
  transformers       — Hugging Face Transformers (PhoBERT tokenizer & model)

  Model sử dụng:
    KalvinPhan/phobert-vihsd-finetuned  (tải tự động từ Hugging Face)

4.3  Web_demo  (requirements.txt)
-----------------------------------
  fastapi==0.111.0         — Web framework API
  uvicorn==0.30.1          — ASGI server
  pydantic==2.7.4          — Data validation
  pydantic-settings==2.3.4 — Quản lý biến môi trường từ .env
  pyspark==3.5.1           — Truy vấn dữ liệu trên HDFS
  hdfs==2.7.3              — WebHDFS client (liệt kê/xoá file HDFS)
  pandas==2.2.2            — Xử lý dữ liệu
  pyarrow==16.1.0          — Đọc/ghi Parquet

4.4  Web_demo/Web/frontend  (package.json)
-------------------------------------------
  next@14.2.3              — React framework (App Router)
  react@^18.3.1            — UI library
  react-dom@^18.3.1        — DOM rendering
  recharts@^2.12.7         — Biểu đồ (Bar, Line, Pie, Radar, Scatter)
  clsx@^2.1.1              — Ghép className có điều kiện
  axios@^1.7.2             — HTTP client

  devDependencies:
  tailwindcss@^3.4.4       — Utility-first CSS framework
  autoprefixer@^10.4.19    — PostCSS plugin
  postcss@^8.4.38          — CSS transform
  eslint@^8                — Linting

4.5  AI/Model_and_evaluate  (cài thủ công)
--------------------------------------------
  transformers       — Hugging Face (PhoBERT, Qwen)
  torch              — PyTorch
  bitsandbytes       — Quantization (4-bit/8-bit cho Qwen)
  pandas             — Xử lý Excel/CSV
  numpy              — Tính toán
  scikit-learn       — TF-IDF, SVM, Logistic Regression, metrics
  datasets           — Hugging Face Datasets
  accelerate         — Tăng tốc training
  openpyxl           — Đọc/ghi file .xlsx
  jupyter            — Chạy notebook
  ipykernel          — Kernel cho Jupyter

================================================================================
5. HƯỚNG DẪN CHẠY TỪNG THÀNH PHẦN
================================================================================

────────────────────────────────────────────────────────────────────────────────
5.1  CRAWL DỮ LIỆU
────────────────────────────────────────────────────────────────────────────────

BƯỚC 1: Cài thư viện

  cd AI/Crawl_data
  pip install -r requirements.txt
  python -m playwright install chromium

BƯỚC 2: Crawl Threads (Selenium + Chrome)

  python Threads/threads.py

  Lưu ý:
  - Script sẽ mở Chrome và yêu cầu đăng nhập Threads thủ công.
  - Sau khi đăng nhập xong, nhấn Enter trong terminal để tiếp tục.
  - Kết quả lưu vào: threads_selenium1.csv

BƯỚC 3: Crawl TikTok (Playwright)

  python Tiktok/tiktok.py

  Lưu ý:
  - Mặc định chạy headless=False để có thể quan sát.
  - Kết quả lưu vào: data/raw/comments.csv
  - Tùy chỉnh số video/bình luận trong __main__:
      max_videos=10, max_comments=500

  Cấu hình chủ đề crawl: Chỉnh dict TOPICS trong mỗi file
  (mặc định gồm 10 chủ đề: thể thao, ẩm thực, giải trí, ...)

────────────────────────────────────────────────────────────────────────────────
5.2  TIỀN XỬ LÝ & EDA
────────────────────────────────────────────────────────────────────────────────

Mở bằng Jupyter, JupyterLab hoặc VS Code rồi chạy toàn bộ:

  jupyter notebook AI/Preprocessing/preprocessing.ipynb
  jupyter notebook AI/EDA/EDA.ipynb

────────────────────────────────────────────────────────────────────────────────
5.3  GÁN NHÃN VỚI QWEN (Kaggle Notebook)
────────────────────────────────────────────────────────────────────────────────

Chạy trên Kaggle Notebook với GPU RTX 6000 Pro.

BƯỚC 1: Thêm Input vào Kaggle Notebook
  - Dataset dữ liệu : https://www.kaggle.com/datasets/phanhuycng/tiktok-mini
  - Thư viện quant   : https://www.kaggle.com/datasets/phanhuycng/bitsandbtyes
  - Model Qwen       : https://www.kaggle.com/models/phanhuycng/qwen-2-5-7b-instruct

BƯỚC 2: Chọn sheet cần gán nhãn (trong notebook)
  SHEET_NAME = "tiktok"   # hoặc "threads"

BƯỚC 3: Chạy toàn bộ notebook
  Runtime → Run All

Output: file .xlsx chứa nhãn được gán bởi Qwen 2.5 7B Instruct
        (quantization 4-bit với BitsAndBytes)

────────────────────────────────────────────────────────────────────────────────
5.4  TỔNG HỢP NHÃN HARD VOTING (Google Colab)
────────────────────────────────────────────────────────────────────────────────

Chạy trên Google Colab với GPU T4.

BƯỚC 1: Upload file .xlsx từ bước gán nhãn lên Colab
  Ví dụ: output_tiktok.xlsx

BƯỚC 2: Cập nhật đường dẫn trong notebook
  INPUT_FILE = "/content/output_tiktok.xlsx"

BƯỚC 3: Chạy toàn bộ notebook
  Runtime → Run All

Output: file dữ liệu cuối cùng với nhãn tổng hợp, sẵn sàng cho training.

────────────────────────────────────────────────────────────────────────────────
5.5  CONTINUED PRETRAINING PHOBERT (Kaggle Notebook)
────────────────────────────────────────────────────────────────────────────────

BƯỚC 1: Thêm Input vào Kaggle Notebook
  - Dataset pretrain : https://www.kaggle.com/datasets/phanhuycng/phobert-pretrain-dataset
  - Model PhoBERT    : https://www.kaggle.com/models/phanhuycng/phobert-base-v2

BƯỚC 2: Mở và chạy notebook
  phobert-pretrain.ipynb → Run All

BƯỚC 3: Tải model đầu ra về máy
  Tải toàn bộ thư mục checkpoint để dùng cho bước Fine-tuning.

────────────────────────────────────────────────────────────────────────────────
5.6  FINE-TUNING & ĐÁNH GIÁ PHOBERT (Google Colab)
────────────────────────────────────────────────────────────────────────────────

BƯỚC 1: Upload dữ liệu đã gán nhãn lên Google Drive

BƯỚC 2: Cấu hình Secrets trong Colab
  HF_TOKEN = "your_huggingface_token"  # token từ huggingface.co

BƯỚC 3: Mở và chạy notebook
  SFT_and_Evaluate_PhoBert.ipynb → Run All

Kết quả: Accuracy, Macro F1, Weighted F1, Confusion Matrix theo từng nhãn.

────────────────────────────────────────────────────────────────────────────────
5.7  EXTENSION CHROME
────────────────────────────────────────────────────────────────────────────────

BƯỚC 1: Cài thư viện

  cd Extension/threads-scrolling-main
  pip install -r requirements.txt

BƯỚC 2: Chạy backend Python

  cd backend
  uvicorn main:app --reload

  Backend khởi động tại: http://127.0.0.1:8000
  Lần đầu chạy sẽ tự tải model KalvinPhan/phobert-vihsd-finetuned (~500MB).

BƯỚC 3: Cài extension vào Chrome

  1. Mở Chrome → địa chỉ: chrome://extensions/
  2. Bật "Developer mode" (góc trên phải)
  3. Chọn "Load unpacked"
  4. Trỏ vào thư mục: Extension/threads-scrolling-main/extension/

BƯỚC 4: Sử dụng

  - Truy cập threads.com và mở bất kỳ bài viết nào.
  - Extension tự động quét bình luận mỗi 2 giây.
  - Bình luận bị phát hiện là hate speech/offensive sẽ bị tô đen.
  - Terminal Python in log tọa độ và nội dung bình luận bị phát hiện.

────────────────────────────────────────────────────────────────────────────────
5.8  WEB DEMO VỚI HDFS
────────────────────────────────────────────────────────────────────────────────
BƯỚC 1: Khởi động cụm Hadoop bằng Docker

  cd Web_demo
  docker-compose up -d

  Kiểm tra các container đã chạy:
    docker ps
  Phải thấy 2 container: namenode, datanode

  Truy cập HDFS Web UI: http://localhost:9870

BƯỚC 2: Tạo thư mục trên HDFS

  docker exec -it namenode hdfs dfs -mkdir -p /data/raw/threads
  docker exec -it namenode hdfs dfs -mkdir -p /data/raw/tiktok
  docker exec -it namenode hdfs dfs -mkdir -p /data/processed
  docker exec -it namenode hdfs dfs -chmod -R 777 /data

BƯỚC 3: Cài thư viện Python cho Web Demo

  cd Web_demo
  pip install -r requirements.txt

BƯỚC 4: Nạp dữ liệu lên HDFS

  Đặt file dữ liệu đã tiền xử lý vào: Web_demo/DataIO/data_preprocessed.csv
  (file CSV phân cách bằng dấu chấm phẩy với các cột: text, topic, keyword,
   post_url, source, label)

  Sau đó chạy:
    cd Web_demo
    python DataIO/import_data.py

BƯỚC 5: Chạy Backend FastAPI

  cd Web_demo/Web/backend
  pip install -r ../../requirements.txt   # nếu chưa cài
  python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000

BƯỚC 6: Chạy Frontend Next.js

  cd Web_demo/Web/frontend
  npm install
  npm run dev

  Mở trình duyệt: http://localhost:3000

  Trang Dashboard hiển thị:
  - KPI tổng quan (tổng bài viết, đã gán nhãn, nền tảng, lớp nhãn)
  - Biểu đồ phân phối nhãn (Pie Chart)
  - So sánh nhãn theo nguồn (Grouped Bar Chart)
  - Top chủ đề (Bar Chart có màu)
  - Phân phối độ dài văn bản theo nhãn (Boxplot proxy)
  - Timeline crawl theo tháng (Bar Chart)
  - Heatmap tỷ lệ nhãn theo chủ đề

================================================================================
6. BIẾN MÔI TRƯỜNG (.env)
================================================================================

Tạo file .env trong thư mục Web_demo/Web/backend/ với nội dung:

  # ── Cấu hình ứng dụng ──
  DEBUG_MODE=True

  # ── Cấu hình HDFS ──
  HDFS_HOST=localhost
  HDFS_PORT=9870               # Port WebHDFS REST API
  HDFS_RPC_PORT=9000           # Port RPC nội bộ cho PySpark
  HDFS_USER=hadoop
  HDFS_RAW_DATA_DIR=/data/raw
  HDFS_PROCESSED_DATA_DIR=/data/processed

  # ── CORS ──
  BACKEND_CORS_ORIGINS=["http://localhost:3000"]

Tạo file .env.local trong thư mục Web_demo/Web/frontend/ với nội dung:

  NEXT_PUBLIC_API_BASE=http://localhost:8000/api/v1