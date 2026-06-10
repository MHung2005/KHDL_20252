"""
process_data.py — Gộp raw data từ HDFS, chia train/test, ghi vào /data/processed/
====================================================================================
Quy trình:
    1. Đọc toàn bộ /data/raw/tiktok + /data/raw/threads
    2. Lọc bỏ dòng null / duplicate
    3. Chỉ giữ dữ liệu đã gán nhãn (label != -1)
    4. Chia train 80% / test 20% (stratified theo label)
    5. Ghi vào /data/processed/ dạng Parquet (SNAPPY)

Cách chạy:
    python AI/DataIO/process_data.py

Sau khi chạy xong, /data/processed/ sẽ có dữ liệu và API /datasets/overview
sẽ trả về thống kê train/test đầy đủ.
"""

from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import StringType

# ============================================================
#  CẤU HÌNH
# ============================================================
HDFS_HOST        = "localhost"
HDFS_PORT        = 9000
HDFS_RAW         = f"hdfs://{HDFS_HOST}:{HDFS_PORT}/data/raw"
HDFS_PROCESSED   = f"hdfs://{HDFS_HOST}:{HDFS_PORT}/data/processed"
PLATFORMS        = ("tiktok", "threads")
TRAIN_RATIO      = 0.8
TEST_RATIO       = 0.2
RANDOM_SEED      = 42


# ============================================================
#  MAIN
# ============================================================
def main():
    spark = (
        SparkSession.builder
        .appName("ProcessRawData")
        .master("local[*]")
        .config("spark.sql.session.timeZone", "Asia/Ho_Chi_Minh")
        .config("spark.hadoop.dfs.client.use.datanode.hostname", "true")
        .config("spark.driver.extraJavaOptions", "-Dlog4j.logLevel=ERROR")
        .getOrCreate()
    )
    spark.sparkContext.setLogLevel("ERROR")

    # ── 1. Đọc raw data từ tất cả platform ──────────────────
    print("\n📥 Đọc raw data từ HDFS...")
    frames = []
    for platform in PLATFORMS:
        path = f"{HDFS_RAW}/{platform}"
        try:
            df = (
                spark.read
                .option("mergeSchema", "true")
                .parquet(path)
                .withColumn("platform", F.lit(platform))
                .withColumn("crawl_date", F.regexp_extract(
                    F.input_file_name(), r"crawl_date=(\d{4}-\d{2}-\d{2})", 1
                ))
            )
            count = df.count()
            print(f"   ✅ {platform}: {count:,} dòng")
            frames.append(df)
        except Exception as e:
            print(f"   ⚠️  Bỏ qua {platform}: {e}")

    if not frames:
        print("❌ Không đọc được dữ liệu nào từ /data/raw. Dừng.")
        spark.stop()
        return

    df_all = frames[0]
    for df in frames[1:]:
        df_all = df_all.unionByName(df)

    total_raw = df_all.count()
    print(f"\n   Tổng raw: {total_raw:,} dòng")

    # ── 2. Làm sạch ─────────────────────────────────────────
    print("\n🧹 Làm sạch dữ liệu...")

    # Bỏ dòng thiếu text hoặc label
    df_clean = df_all.dropna(subset=["text", "label"])

    # Bỏ duplicate theo text + platform
    df_clean = df_clean.dropDuplicates(["text", "platform"])

    # Chỉ giữ dữ liệu đã gán nhãn
    df_labeled = df_clean.filter(F.col("label") != -1)

    total_labeled = df_labeled.count()
    total_dropped = total_raw - total_labeled
    print(f"   Sau làm sạch : {total_labeled:,} dòng")
    print(f"   Đã loại bỏ   : {total_dropped:,} dòng (null / duplicate / chưa nhãn)")

    # Thống kê phân phối nhãn
    print("\n   📊 Phân phối nhãn:")
    df_labeled.groupBy("label").count().orderBy("label").show()

    # ── 3. Chia train / test (stratified theo label) ─────────
    print(f"\n✂️  Chia train/test ({int(TRAIN_RATIO*100)}/{int(TEST_RATIO*100)})...")

    # Stratified split: chia từng nhãn riêng rồi gộp lại
    # → đảm bảo tỷ lệ nhãn trong train và test giống nhau
    labels = [row["label"] for row in df_labeled.select("label").distinct().collect()]

    train_frames = []
    test_frames  = []

    for lbl in sorted(labels):
        df_lbl = df_labeled.filter(F.col("label") == lbl)
        tr, te = df_lbl.randomSplit([TRAIN_RATIO, TEST_RATIO], seed=RANDOM_SEED)
        train_frames.append(tr)
        test_frames.append(te)
        print(f"   label={lbl}: train={tr.count():,}  test={te.count():,}")

    df_train = train_frames[0]
    for df in train_frames[1:]:
        df_train = df_train.unionByName(df)

    df_test = test_frames[0]
    for df in test_frames[1:]:
        df_test = df_test.unionByName(df)

    df_train = df_train.withColumn("split_set", F.lit("train"))
    df_test  = df_test.withColumn("split_set",  F.lit("test"))

    df_processed = df_train.unionByName(df_test)

    total_train = df_train.count()
    total_test  = df_test.count()
    print(f"\n   Train tổng: {total_train:,} dòng")
    print(f"   Test  tổng: {total_test:,}  dòng")

    # ── 4. Ghi vào /data/processed/ ─────────────────────────
    print(f"\n☁️  Ghi vào HDFS: {HDFS_PROCESSED} ...")
    (
        df_processed
        .write
        .mode("overwrite")
        .option("compression", "snappy")
        .partitionBy("split_set", "platform")   # partition để đọc nhanh hơn
        .parquet(HDFS_PROCESSED)
    )

    print(f"\n✅ Hoàn tất! Đã ghi {total_train + total_test:,} dòng vào {HDFS_PROCESSED}")
    print(f"   Cấu trúc thư mục:")
    print(f"   /data/processed/split_set=train/platform=tiktok/")
    print(f"   /data/processed/split_set=train/platform=threads/")
    print(f"   /data/processed/split_set=test/platform=tiktok/")
    print(f"   /data/processed/split_set=test/platform=threads/")

    spark.stop()
    print("\n🔌 SparkSession đã dừng.")


if __name__ == "__main__":
    main()