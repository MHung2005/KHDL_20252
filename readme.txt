# Hướng dẫn tổng cho dự án

## 1. Các gói phần mềm sử dụng kèm theo

### 1.1. `AI/Crawl_data`

File: `AI/Crawl_data/requirements.txt`

- `pandas`
- `numpy`
- `pyarrow`
- `selenium`
- `webdriver-manager`
- `playwright`
# Cài Chromium riêng cho Playwright:
# python -m playwright install chromium

### 1.2. `Extension/threads-scrolling-main`

File: `Extension/threads-scrolling-main/requirements.txt`

- `fastapi`
- `uvicorn`
- `torch`
- `transformers`

### 1.3. `Web_demo`

File: `Web_demo/requirements.txt`

- `fastapi==0.111.0`
- `uvicorn==0.30.1`
- `pydantic==2.7.4`
- `pydantic-settings==2.3.4`
- `pyspark==3.5.1`
- `hdfs==2.7.3`
- `pandas==2.2.2`
- `pyarrow==16.1.0`

### 1.4. Nhóm thư viện cho folder AI

- `transformers`
- `torch`
- `bitsandbytes`
- `pandas`
- `numpy`
- `scikit-learn`
- `datasets`
- `accelerate`
- `openpyxl`
- `jupyter`
- `ipykernel`

## 2. Hướng dẫn chạy dự án

### 2.1. Chạy extension 

1. Thêm extension vào Chrome

* Mở Chrome và truy cập:

```text
chrome://extensions/
```

* Bật **Developer mode**
* Chọn **Load unpacked**
* Thêm thư mục:

```text
extension/
```

---

2. Chạy backend

Di chuyển vào thư mục backend:

```bash
cd backend
```

Chạy server:

```bash
uvicorn main:app --reload
```

### 2.2. Chạy web demo với HDFS

1. Khởi động cụm Hadoop:

```bash
cd Web_demo
docker-compose up -d
```

2. Tạo các thư mục cần thiết trên HDFS:

```bash
docker exec -it namenode hdfs dfs -mkdir -p /data/raw/threads
docker exec -it namenode hdfs dfs -mkdir -p /data/raw/tiktok
docker exec -it namenode hdfs dfs -mkdir -p /data/processed
```

3. Cấp quyền đọc ghi cho toàn bộ thư mục dữ liệu:

```bash
docker exec -it namenode hdfs dfs -chmod -R 777 /data
```

4. Nạp dữ liệu lên HDFS:

```bash
cd Web_demo
python DataIO/import_data.py
```

5. Chạy backend của web demo:

```bash
cd Web_demo/Web/backend
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

6. Chạy frontend của web demo:

```bash
cd Web_demo/Web/frontend
npm install
npm run dev
```

### 2.3. Chạy các bước trong thư mục `AI`

#### Crawl dữ liệu

```bash
cd AI/Crawl_data
pip install -r requirements.txt
python Threads/threads.py
python Tiktok/tiktok.py
```

#### Tiền xử lý và EDA

Mở và chạy toàn bộ các notebook sau bằng Jupyter, JupyterLab hoặc VS Code:

- `AI/Preprocessing/preprocessing.ipynb`
- `AI/EDA/EDA.ipynb`

#### Gán nhãn và tổng hợp nhãn

- `AI/Model_and_Evaluate/Labeling/labeling_with_Qwen.ipynb`: chạy trên Kaggle Notebook, chọn `SHEET_NAME = "tiktok"` hoặc `SHEET_NAME = "threads"`.
- `AI/Model_and_Evaluate/Labeling/HardVoting.ipynb`: chạy trên Google Colab, cập nhật đường dẫn file Excel đầu vào rồi chạy toàn bộ notebook.

#### Continued pretraining, fine-tuning và đánh giá PhoBERT

- `AI/Model_and_Evaluate/PreTrain_SFT_Eval_PhoBERT/phobert-pretrain.ipynb`
- `AI/Model_and_Evaluate/PreTrain_SFT_Eval_PhoBERT/SFT_and_Evaluate_PhoBert.ipynb`