import pandas as pd
from datetime import datetime
import uuid
import io
import pyarrow as pa
import pyarrow.parquet as pq
from hdfs import InsecureClient

HDFS_URL  = "http://localhost:9870"
HDFS_USER = "hadoop"
HDFS_BASE = "/data/raw/tiktok"

def save_to_hdfs(df: pd.DataFrame):
    """Lưu DataFrame lên HDFS dưới dạng Parquet (SNAPPY)."""
    today     = datetime.now().strftime("%Y-%m-%d")
    file_id   = uuid.uuid4().hex[:8]
    hdfs_dir  = f"{HDFS_BASE}/crawl_date={today}"
    hdfs_path = f"{hdfs_dir}/part_{file_id}.parquet"

    out = pd.DataFrame({
        "id":      [str(uuid.uuid4()) for _ in range(len(df))],
        "text":    df["text"],
        "topic":   df["topic"],
        "keyword": df["keyword"],
        "url":     df["post_url"],          # Facebook không lấy được URL comment
        "label":   df["label"],          # -1 = chưa gán nhãn
    })

    buf = io.BytesIO()
    pq.write_table(pa.Table.from_pandas(out, preserve_index=False), buf, compression="snappy")
    buf.seek(0)

    try:
        client = InsecureClient(HDFS_URL, user=HDFS_USER)
        client.makedirs(hdfs_dir)
        with client.write(hdfs_path, overwrite=True) as f:
            f.write(buf.read())
        print(f"☁️  HDFS: đã lưu {len(out)} dòng → {hdfs_path}")
    except Exception as e:
        print(f"⚠️  Lưu HDFS thất bại (dữ liệu vẫn có trong CSV): {e}")


path = "./AI/DataIO/Data_final - tiktok.csv"
df = pd.read_csv(path)
print(f"✅ Đã đọc {len(df)} dòng từ {path}")
save_to_hdfs(df)

