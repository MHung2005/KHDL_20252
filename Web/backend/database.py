"""
app/database.py - Quản lý kết nối Hive và HDFS
Sử dụng pyhive để kết nối Hive, hdfs để kết nối HDFS
"""
import logging
from typing import Optional, List, Dict, Any
from contextlib import contextmanager

from app.config import settings

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------
# Hive Connection Manager
# ---------------------------------------------------------------
class HiveConnection:
    """Quản lý kết nối đến Apache Hive qua Thrift Server"""

    def __init__(self):
        self._connection = None

    def get_connection(self):
        """Lấy kết nối Hive, tạo mới nếu chưa có"""
        if self._connection is None:
            try:
                from pyhive import hive
                self._connection = hive.Connection(
                    host=settings.HIVE_HOST,
                    port=settings.HIVE_PORT,
                    database=settings.HIVE_DATABASE,
                    username=settings.HIVE_USERNAME,
                    auth=settings.HIVE_AUTH,
                )
                logger.info(f"✅ Hive connected: {settings.HIVE_HOST}:{settings.HIVE_PORT}")
            except ImportError:
                raise RuntimeError("pyhive not installed. Run: pip install pyhive[hive]")
            except Exception as e:
                raise RuntimeError(f"Hive connection failed: {e}")
        return self._connection

    @contextmanager
    def cursor(self):
        """Context manager cho Hive cursor"""
        conn = self.get_connection()
        cur = conn.cursor()
        try:
            yield cur
        finally:
            cur.close()

    def execute_query(self, sql: str, params: tuple = None) -> List[Dict[str, Any]]:
        """
        Thực thi câu query Hive và trả về list dict
        
        Args:
            sql: Câu HiveQL cần thực thi
            params: Tham số (nếu có)
        Returns:
            List[Dict] - Kết quả query
        """
        with self.cursor() as cur:
            if params:
                cur.execute(sql, params)
            else:
                cur.execute(sql)
            
            columns = [desc[0] for desc in cur.description] if cur.description else []
            rows = cur.fetchall()
            return [dict(zip(columns, row)) for row in rows]

    def close(self):
        if self._connection:
            self._connection.close()
            self._connection = None


# ---------------------------------------------------------------
# HDFS Connection Manager
# ---------------------------------------------------------------
class HDFSConnection:
    """Quản lý kết nối đến HDFS qua WebHDFS REST API"""

    def __init__(self):
        self._client = None

    def get_client(self):
        if self._client is None:
            try:
                from hdfs import InsecureClient
                self._client = InsecureClient(
                    url=f"http://{settings.HDFS_HOST}:{settings.HDFS_PORT}",
                    user=settings.HDFS_USER
                )
                logger.info(f"✅ HDFS connected: {settings.HDFS_HOST}:{settings.HDFS_PORT}")
            except ImportError:
                raise RuntimeError("hdfs not installed. Run: pip install hdfs")
            except Exception as e:
                raise RuntimeError(f"HDFS connection failed: {e}")
        return self._client

    def list_files(self, path: str) -> List[Dict]:
        """Liệt kê files trong một thư mục HDFS"""
        client = self.get_client()
        try:
            files = client.list(path, status=True)
            return [{"name": f[0], **f[1]} for f in files]
        except Exception as e:
            logger.error(f"HDFS list error at {path}: {e}")
            return []

    def get_file_info(self, path: str) -> Optional[Dict]:
        """Lấy thông tin file trên HDFS"""
        client = self.get_client()
        try:
            status = client.status(path)
            return status
        except Exception as e:
            logger.error(f"HDFS status error at {path}: {e}")
            return None

    def read_file(self, path: str, encoding: str = "utf-8") -> Optional[str]:
        """Đọc nội dung file từ HDFS"""
        client = self.get_client()
        try:
            with client.read(path, encoding=encoding) as reader:
                return reader.read()
        except Exception as e:
            logger.error(f"HDFS read error at {path}: {e}")
            return None


# ---------------------------------------------------------------
# Mock Data Service (dùng khi không có Hadoop)
# ---------------------------------------------------------------
class MockDataService:
    """Cung cấp dữ liệu mẫu để phát triển frontend không cần Hadoop"""

    @staticmethod
    def get_platform_stats() -> List[Dict]:
        return [
            {"platform": "tiktok",   "total_records": 12450, "vietnamese_records": 11200,
             "first_crawled": "2024-01-15", "last_crawled": "2024-06-01", "avg_char_count": 128.5},
            {"platform": "threads",  "total_records": 8320,  "vietnamese_records": 7890,
             "first_crawled": "2024-02-01", "last_crawled": "2024-06-01", "avg_char_count": 215.3},
            {"platform": "facebook", "total_records": 15680, "vietnamese_records": 14900,
             "first_crawled": "2024-01-10", "last_crawled": "2024-06-01", "avg_char_count": 342.7},
        ]

    @staticmethod
    def get_dataset_split_stats() -> List[Dict]:
        return [
            {"split_set": "train", "platform": "tiktok",   "label_name": "normal",       "record_count": 3200, "avg_token_count": 28.4},
            {"split_set": "train", "platform": "tiktok",   "label_name": "hate_speech",  "record_count": 980,  "avg_token_count": 32.1},
            {"split_set": "train", "platform": "tiktok",   "label_name": "offensive",    "record_count": 820,  "avg_token_count": 30.5},
            {"split_set": "train", "platform": "threads",  "label_name": "normal",       "record_count": 2100, "avg_token_count": 45.2},
            {"split_set": "train", "platform": "threads",  "label_name": "hate_speech",  "record_count": 640,  "avg_token_count": 48.7},
            {"split_set": "train", "platform": "threads",  "label_name": "offensive",    "record_count": 540,  "avg_token_count": 44.3},
            {"split_set": "train", "platform": "facebook", "label_name": "normal",       "record_count": 4100, "avg_token_count": 62.8},
            {"split_set": "train", "platform": "facebook", "label_name": "hate_speech",  "record_count": 1200, "avg_token_count": 70.2},
            {"split_set": "train", "platform": "facebook", "label_name": "offensive",    "record_count": 980,  "avg_token_count": 65.4},
            {"split_set": "test",  "platform": "tiktok",   "label_name": "normal",       "record_count": 800,  "avg_token_count": 27.9},
            {"split_set": "test",  "platform": "tiktok",   "label_name": "hate_speech",  "record_count": 245,  "avg_token_count": 31.8},
            {"split_set": "test",  "platform": "tiktok",   "label_name": "offensive",    "record_count": 205,  "avg_token_count": 30.1},
            {"split_set": "test",  "platform": "threads",  "label_name": "normal",       "record_count": 520,  "avg_token_count": 44.8},
            {"split_set": "test",  "platform": "threads",  "label_name": "hate_speech",  "record_count": 158,  "avg_token_count": 47.9},
            {"split_set": "test",  "platform": "threads",  "label_name": "offensive",    "record_count": 132,  "avg_token_count": 43.7},
            {"split_set": "test",  "platform": "facebook", "label_name": "normal",       "record_count": 1020, "avg_token_count": 62.1},
            {"split_set": "test",  "platform": "facebook", "label_name": "hate_speech",  "record_count": 298,  "avg_token_count": 69.4},
            {"split_set": "test",  "platform": "facebook", "label_name": "offensive",    "record_count": 242,  "avg_token_count": 64.8},
        ]

    @staticmethod
    def get_model_comparison() -> List[Dict]:
        return [
            {
                "model_id": "model-001",
                "model_display_name": "TF-IDF + SVM",
                "model_type": "traditional",
                "version": "v1.0",
                "accuracy": 0.7823,
                "macro_f1": 0.7615,
                "weighted_f1": 0.7702,
                "macro_precision": 0.7798,
                "macro_recall": 0.7750,
                "target_hate_f1": 0.7221,
                "target_offensive_f1": 0.6805,
                "target_normal_f1": 0.8122,
                "confusion_matrix": "[[1254,178,88],[52,228,32],[28,24,116]]",
                "train_ratio": 0.80,
                "test_ratio": 0.20,
                "total_samples": 10000,
                "evaluated_at": "2024-06-01T10:00:00",
            },
            {
                "model_id": "model-002",
                "model_display_name": "TF-IDF + Logistic Regression",
                "model_type": "traditional",
                "version": "v1.0",
                "accuracy": 0.8015,
                "macro_f1": 0.7832,
                "weighted_f1": 0.7910,
                "macro_precision": 0.8034,
                "macro_recall": 0.7978,
                "target_hate_f1": 0.7370,
                "target_offensive_f1": 0.6973,
                "target_normal_f1": 0.8344,
                "confusion_matrix": "[[1252,180,88],[45,234,33],[22,30,116]]",
                "train_ratio": 0.80,
                "test_ratio": 0.20,
                "total_samples": 10000,
                "evaluated_at": "2024-06-01T10:30:00",
            },
            {
                "model_id": "model-003",
                "model_display_name": "PhoBERT + Classification Head",
                "model_type": "deep_learning",
                "version": "v1.0",
                "accuracy": 0.8934,
                "macro_f1": 0.8823,
                "weighted_f1": 0.8876,
                "macro_precision": 0.8945,
                "macro_recall": 0.8890,
                "target_hate_f1": 0.8732,
                "target_offensive_f1": 0.8612,
                "target_normal_f1": 0.9122,
                "confusion_matrix": "[[1370,98,52],[22,276,14],[12,14,142]]",
                "train_ratio": 0.80,
                "test_ratio": 0.20,
                "total_samples": 10000,
                "evaluated_at": "2024-06-01T11:00:00",
            },
        ]

    @staticmethod
    def get_crawl_timeline() -> List[Dict]:
        return [
            {"month": "2024-01", "tiktok": 1200, "threads": 0,    "facebook": 1800},
            {"month": "2024-02", "tiktok": 2100, "threads": 1200,  "facebook": 2400},
            {"month": "2024-03", "tiktok": 2800, "threads": 1800,  "facebook": 3100},
            {"month": "2024-04", "tiktok": 2500, "threads": 2100,  "facebook": 3500},
            {"month": "2024-05", "tiktok": 2400, "threads": 1980,  "facebook": 3200},
            {"month": "2024-06", "tiktok": 1450, "threads": 1240,  "facebook": 1680},
        ]


# ---------------------------------------------------------------
# Singleton instances
# ---------------------------------------------------------------
hive_conn = HiveConnection()
hdfs_conn = HDFSConnection()
mock_data = MockDataService()


async def test_connections():
    """Test kết nối Hive và HDFS"""
    if settings.USE_MOCK_DATA:
        logger.info("📦 Running in MOCK DATA mode - Hadoop not required")
        return
    hive_conn.get_connection()
    hdfs_conn.get_client()
