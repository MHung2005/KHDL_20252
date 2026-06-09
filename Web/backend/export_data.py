"""
export_data.py — Module truy vấn dữ liệu crawl trên HDFS bằng PySpark
======================================================================
Hỗ trợ các truy vấn:
    - Theo label      : query_by_label()
    - Theo ngày       : query_by_date()
    - Theo nền tảng   : query_by_platform()
    - Theo topic      : query_by_topic()
    - Theo keyword    : query_by_keyword()
    - Tổng hợp thống kê: summary()

Cách dùng:
    from export_data import HdfsQuery

    q = HdfsQuery()

    # Lấy toàn bộ bình luận chưa gán nhãn
    df = q.query_by_label(-1)

    # Lấy dữ liệu Facebook từ ngày 2026-06-01 đến 2026-06-09
    df = q.query_by_date("2026-06-01", "2026-06-09", platform="facebook")

    q.stop()   # Tắt SparkSession khi xong

Cài đặt:
    pip install pyspark
"""

from __future__ import annotations

from typing import Optional
from datetime import datetime, timedelta

from pyspark.sql import SparkSession, DataFrame
from pyspark.sql import functions as F


# ============================================================
#  CẤU HÌNH
# ============================================================
HDFS_HOST  = "localhost"
HDFS_PORT  = 9000
HDFS_BASE  = f"hdfs://{HDFS_HOST}:{HDFS_PORT}/data/raw"
HDFS_PROCESSED_BASE = f"hdfs://{HDFS_HOST}:{HDFS_PORT}/data/processed"
PLATFORMS  = ("threads", "tiktok")

# Nhãn label
LABEL_NAMES = {
    -1: "chưa gán nhãn",
     0: "bình thường",
     1: "offensive",
     2: "hate speech",
}


# ============================================================
#  LỚP TRUY VẤN CHÍNH
# ============================================================

class HdfsQuery:
    """
    Giao diện truy vấn dữ liệu crawl trên HDFS.

    Parameters
    ----------
    app_name  : Tên SparkSession
    master    : Spark master URL (mặc định local, đổi thành spark://... nếu có cluster)
    """

    def __init__(
        self,
        app_name: str = "HateSpeechQuery",
        master: str = "local[*]",
    ):
        self.spark = (
            SparkSession.builder
            .appName(app_name)
            .master(master)
            .config("spark.sql.session.timeZone", "Asia/Ho_Chi_Minh")
            # Tắt log rác của Spark
            .config("spark.hadoop.dfs.client.use.datanode.hostname", "true")
            .config("spark.driver.extraJavaOptions", "-Dlog4j.logLevel=ERROR")
            .getOrCreate()
        )
        self.spark.sparkContext.setLogLevel("ERROR")
        self._all: Optional[DataFrame] = None   # cache toàn bộ dữ liệu

    # ── Nội bộ ───────────────────────────────────────────────

    def _load_platform(self, platform: str) -> DataFrame:
        """Đọc toàn bộ Parquet của một nền tảng, thêm cột platform + crawl_date."""
        path = f"{HDFS_BASE}/{platform}"
        df = (
            self.spark.read
            .option("mergeSchema", "true")
            .parquet(path)
            .withColumn("platform", F.lit(platform))
            # Trích crawl_date từ tên thư mục partition (crawl_date=yyyy-MM-dd)
            .withColumn("crawl_date", F.regexp_extract(
                F.input_file_name(), r"crawl_date=(\d{4}-\d{2}-\d{2})", 1
            ))
        )
        return df

    def _load_all(self) -> DataFrame:
        """
        Khởi tạo Logical Plan kết nối 3 nền tảng.
        KHÔNG dùng .cache() để tận dụng tính năng Predicate Pushdown của Parquet.
        """
        # Nếu đã tạo Logical Plan rồi thì trả về luôn, không tốn tài nguyên
        if getattr(self, "_all_plan", None) is not None:
            return self._all_plan
            
        frames = []
        for p in PLATFORMS:
            try:
                df_platform = self._load_platform(p)
                frames.append(df_platform)
            except Exception:
                continue

        if not frames:
            raise ValueError("❌ Lỗi: Tất cả các thư mục trên HDFS đều trống!")

        # Chỉ tạo ra bản đồ thực thi (Logical Plan), dữ liệu chưa hề được load vào RAM
        result_df = frames[0]
        for df in frames[1:]:
            result_df = result_df.unionByName(df)
            
        # Lưu lại Plan, KHÔNG GỌI .cache()
        self._all_plan = result_df
        return self._all_plan
    
    def _filter_platform(self, df: DataFrame, platform: Optional[str]) -> DataFrame:
        if platform:
            if platform not in PLATFORMS:
                raise ValueError(f"platform không hợp lệ: {platform}. Chọn: {PLATFORMS}")
            df = df.filter(F.col("platform") == platform)
        return df
    
    # ─────────────────────────────────────────────────────────
    #  MODULE 1 — Truy vấn theo label
    # ─────────────────────────────────────────────────────────

    def query_by_label(
        self,
        label: int,
        platform: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> DataFrame:
        """
        Lấy các bản ghi theo nhãn label.

        Parameters
        ----------
        label    : -1 (chưa gán nhãn) | 0 (bình thường) | 1 (offensive) | 2 (hate speech)
        platform : Lọc thêm theo nền tảng (tuỳ chọn)
        limit    : Giới hạn số dòng trả về (tuỳ chọn)

        Ví dụ
        -----
        # Toàn bộ bình luận chưa gán nhãn
        df = q.query_by_label(-1)

        # Hate speech trên TikTok
        df = q.query_by_label(2, platform="tiktok")
        """
        label_name = LABEL_NAMES.get(label, str(label))
        print(f"🔍 Truy vấn label={label} ({label_name})"
              + (f", platform={platform}" if platform else ""))

        df = self._load_all()
        df = df.filter(F.col("label") == label)
        df = self._filter_platform(df, platform)

        if limit:
            df = df.limit(limit)

        print(f"   → {df.count()} bản ghi")
        return df

    def label_distribution(self, platform: Optional[str] = None) -> DataFrame:
        """
        Thống kê phân phối nhãn.

        Ví dụ
        -----
        q.label_distribution().show()
        q.label_distribution(platform="facebook").show()
        """
        df = self._load_all()
        df = self._filter_platform(df, platform)
        result = (
            df.groupBy("label")
            .agg(F.count("*").alias("total"))
            .withColumn("label_name", F.when(F.col("label") == -1, "chưa gán nhãn")
                                       .when(F.col("label") ==  0, "bình thường")
                                       .when(F.col("label") ==  1, "offensive")
                                       .when(F.col("label") ==  2, "hate speech")
                                       .otherwise("không xác định"))
            .orderBy("label")
        )
        return result

    # ─────────────────────────────────────────────────────────
    #  MODULE 2 — Truy vấn theo ngày
    # ─────────────────────────────────────────────────────────

    def query_by_date(
        self,
        start_date: str,
        end_date: Optional[str] = None,
        platform: Optional[str] = None,
        label: Optional[int] = None,
    ) -> DataFrame:
        """
        Lấy bản ghi trong khoảng ngày crawl.

        Parameters
        ----------
        start_date : Ngày bắt đầu, định dạng "yyyy-MM-dd"
        end_date   : Ngày kết thúc (mặc định = start_date, tức lọc đúng 1 ngày)
        platform   : Lọc thêm theo nền tảng (tuỳ chọn)
        label      : Lọc thêm theo nhãn (tuỳ chọn)

        Ví dụ
        -----
        # Dữ liệu ngày hôm nay
        df = q.query_by_date("2026-06-09")

        # Dữ liệu Facebook trong tuần
        df = q.query_by_date("2026-06-01", "2026-06-09", platform="facebook")

        # Hate speech trong tháng 6
        df = q.query_by_date("2026-06-01", "2026-06-30", label=2)
        """
        if end_date is None:
            end_date = start_date

        print(f"🔍 Truy vấn ngày {start_date} → {end_date}"
              + (f", platform={platform}" if platform else "")
              + (f", label={label}" if label is not None else ""))

        df = self._load_all()
        df = df.filter(
            (F.col("crawl_date") >= start_date) &
            (F.col("crawl_date") <= end_date)
        )
        df = self._filter_platform(df, platform)
        if label is not None:
            df = df.filter(F.col("label") == label)

        print(f"   → {df.count()} bản ghi")
        return df

    def daily_count(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        platform: Optional[str] = None,
    ) -> DataFrame:
        """
        Thống kê số bản ghi crawl theo từng ngày.

        Ví dụ
        -----
        q.daily_count().show(30)
        q.daily_count("2026-06-01", "2026-06-09", platform="tiktok").show()
        """
        df = self._load_all()
        if start_date:
            df = df.filter(F.col("crawl_date") >= start_date)
        if end_date:
            df = df.filter(F.col("crawl_date") <= end_date)
        df = self._filter_platform(df, platform)

        return (
            df.groupBy("crawl_date", "platform")
            .agg(F.count("*").alias("total"))
            .orderBy("crawl_date", "platform")
        )

    # ─────────────────────────────────────────────────────────
    #  MODULE 3 — Truy vấn theo nền tảng
    # ─────────────────────────────────────────────────────────

    def query_by_platform(
        self,
        platform: str,
        label: Optional[int] = None,
        limit: Optional[int] = None,
    ) -> DataFrame:
        """
        Lấy toàn bộ bản ghi của một nền tảng.

        Parameters
        ----------
        platform : "facebook" | "threads" | "tiktok"
        label    : Lọc thêm theo nhãn (tuỳ chọn)
        limit    : Giới hạn số dòng (tuỳ chọn)

        Ví dụ
        -----
        df = q.query_by_platform("tiktok")
        df = q.query_by_platform("facebook", label=2)
        """
        print(f"🔍 Truy vấn platform={platform}"
              + (f", label={label}" if label is not None else ""))

        df = self._load_all()
        df = self._filter_platform(df, platform)
        if label is not None:
            df = df.filter(F.col("label") == label)
        if limit:
            df = df.limit(limit)

        print(f"   → {df.count()} bản ghi")
        return df

    def platform_comparison(self) -> DataFrame:
        """
        So sánh số lượng bản ghi và phân phối nhãn giữa 3 nền tảng.

        Ví dụ
        -----
        q.platform_comparison().show()
        """
        df = self._load_all()
        return (
            df.groupBy("platform")
            .agg(
                F.count("*").alias("total"),
                F.sum(F.when(F.col("label") == -1, 1).otherwise(0)).alias("chưa_gán_nhãn"),
                F.sum(F.when(F.col("label") ==  0, 1).otherwise(0)).alias("bình_thường"),
                F.sum(F.when(F.col("label") ==  1, 1).otherwise(0)).alias("offensive"),
                F.sum(F.when(F.col("label") ==  2, 1).otherwise(0)).alias("hate_speech"),
            )
            .orderBy("platform")
        )

    # ─────────────────────────────────────────────────────────
    #  MODULE 4 — Truy vấn theo topic
    # ─────────────────────────────────────────────────────────

    def query_by_topic(
        self,
        topic: str,
        platform: Optional[str] = None,
        label: Optional[int] = None,
        limit: Optional[int] = None,
    ) -> DataFrame:
        """
        Lấy bản ghi theo chủ đề.

        Parameters
        ----------
        topic    : Tên chủ đề, ví dụ "the_thao", "chinh_tri"
        platform : Lọc thêm theo nền tảng (tuỳ chọn)
        label    : Lọc thêm theo nhãn (tuỳ chọn)
        limit    : Giới hạn số dòng (tuỳ chọn)

        Ví dụ
        -----
        df = q.query_by_topic("the_thao")
        df = q.query_by_topic("chinh_tri", platform="facebook", label=2)
        """
        print(f"🔍 Truy vấn topic='{topic}'"
              + (f", platform={platform}" if platform else "")
              + (f", label={label}" if label is not None else ""))

        df = self._load_all()
        df = df.filter(F.lower(F.col("topic")) == topic.lower())
        df = self._filter_platform(df, platform)
        if label is not None:
            df = df.filter(F.col("label") == label)
        if limit:
            df = df.limit(limit)

        print(f"   → {df.count()} bản ghi")
        return df

    def topic_stats(self, platform: Optional[str] = None) -> DataFrame:
        """
        Thống kê số lượng bản ghi theo từng topic.

        Ví dụ
        -----
        q.topic_stats().show(20)
        q.topic_stats(platform="tiktok").show()
        """
        df = self._load_all()
        df = self._filter_platform(df, platform)
        return (
            df.groupBy("topic", "platform")
            .agg(F.count("*").alias("total"))
            .orderBy(F.desc("total"))
        )

    # ─────────────────────────────────────────────────────────
    #  MODULE 5 — Truy vấn theo keyword
    # ─────────────────────────────────────────────────────────

    def query_by_keyword(
        self,
        keyword: str,
        platform: Optional[str] = None,
        label: Optional[int] = None,
        exact: bool = True,
        limit: Optional[int] = None,
    ) -> DataFrame:
        """
        Lấy bản ghi theo từ khoá crawl.

        Parameters
        ----------
        keyword  : Từ khoá cần lọc
        platform : Lọc thêm theo nền tảng (tuỳ chọn)
        label    : Lọc thêm theo nhãn (tuỳ chọn)
        exact    : True = khớp chính xác, False = tìm kiếm gần đúng (LIKE)
        limit    : Giới hạn số dòng (tuỳ chọn)

        Ví dụ
        -----
        # Khớp chính xác
        df = q.query_by_keyword("bóng đá")

        # Tìm kiếm gần đúng (chứa từ khoá)
        df = q.query_by_keyword("bóng", exact=False, platform="tiktok")

        # Hate speech theo keyword
        df = q.query_by_keyword("chính trị", label=2)
        """
        print(f"🔍 Truy vấn keyword='{keyword}' ({'exact' if exact else 'like'})"
              + (f", platform={platform}" if platform else "")
              + (f", label={label}" if label is not None else ""))

        df = self._load_all()
        if exact:
            df = df.filter(F.lower(F.col("keyword")) == keyword.lower())
        else:
            df = df.filter(F.lower(F.col("keyword")).contains(keyword.lower()))
        df = self._filter_platform(df, platform)
        if label is not None:
            df = df.filter(F.col("label") == label)
        if limit:
            df = df.limit(limit)

        print(f"   → {df.count()} bản ghi")
        return df

    def keyword_stats(self, platform: Optional[str] = None, top_n: int = 20) -> DataFrame:
        """
        Thống kê top keyword nhiều bản ghi nhất.

        Ví dụ
        -----
        q.keyword_stats(top_n=10).show()
        q.keyword_stats(platform="threads").show()
        """
        df = self._load_all()
        df = self._filter_platform(df, platform)
        return (
            df.groupBy("keyword", "platform")
            .agg(F.count("*").alias("total"))
            .orderBy(F.desc("total"))
            .limit(top_n)
        )

    # ─────────────────────────────────────────────────────────
    #  MODULE 6 — Tổng hợp thống kê
    # ─────────────────────────────────────────────────────────

    def summary(self) -> None:
        """
        In tổng hợp thống kê toàn bộ dữ liệu trên HDFS.

        Ví dụ
        -----
        q.summary()
        """
        df = self._load_all()
        total = df.count()
        print("\n" + "=" * 55)
        print("  TỔNG HỢP DỮ LIỆU HDFS")
        print("=" * 55)
        print(f"  Tổng bản ghi : {total:,}")

        print("\n  📊 Theo nền tảng:")
        self.platform_comparison().show(truncate=False)

        print("  📅 Theo ngày (7 ngày gần nhất):")
        self.daily_count().orderBy(F.desc("crawl_date")).limit(7).show(truncate=False)

        print("  🏷️  Phân phối nhãn:")
        self.label_distribution().show(truncate=False)

        print("  🔑 Top 10 keyword:")
        self.keyword_stats(top_n=10).show(truncate=False)

        print("  📁 Top 10 topic:")
        self.topic_stats().limit(10).show(truncate=False)
        print("=" * 55 + "\n")

    # ─────────────────────────────────────────────────────────
    #  MODULE 7 — Truy cập dữ liệu đã qua xử lý
    # ─────────────────────────────────────────────────────────
    def get_processed_data(self) -> Optional[DataFrame]:
        """
        Đọc tập dữ liệu đã qua xử lý (có cột split_set: train/test).
        """
        try:
            # Đọc toàn bộ thư mục /data/processed
            df = (
                self.spark.read
                .option("mergeSchema", "true")
                .parquet(HDFS_PROCESSED_BASE)
            )
            return df
        except Exception as e:
            print(f"⚠️ Thư mục Processed chưa có dữ liệu: {e}")
            return None

    # ─────────────────────────────────────────────────────────
    #  Tiện ích
    # ─────────────────────────────────────────────────────────

    def stop(self) -> None:
        """Dừng SparkSession, giải phóng tài nguyên."""
        self.spark.stop()
        print("✅ SparkSession đã dừng.")


# ============================================================
#  CHẠY THỬ TRỰC TIẾP
# ============================================================
if __name__ == "__main__":
    q = HdfsQuery()

    # ── Tổng hợp toàn bộ
    q.summary()

    # ── Theo label
    unlabeled = q.query_by_label(-1)
    unlabeled.show(5)

    hate = q.query_by_label(2, platform="tiktok")
    hate.show(5)

    # ── Theo ngày
    today = datetime.now().strftime("%Y-%m-%d")
    df_today = q.query_by_date(today)
    df_today.show(5)

    # week_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
    # df_week = q.query_by_date(week_ago, today, platform="facebook")
    # df_week.show(5)

    # ── Theo nền tảng
    # df_fb = q.query_by_platform("facebook")
    # df_fb.show(5)

    # ── Theo topic
    df_topic = q.query_by_topic("the_thao")
    df_topic.show(5)

    q.topic_stats().show(10)

    # ── Theo keyword
    df_kw = q.query_by_keyword("bóng đá")
    df_kw.show(5)

    df_kw_like = q.query_by_keyword("bóng", exact=False, platform="tiktok")
    df_kw_like.show(5)

    q.keyword_stats(top_n=10).show()

    q.stop()