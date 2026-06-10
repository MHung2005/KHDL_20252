"""
app/config.py - Quản lý biến môi trường và cấu hình hệ thống
Yêu cầu cài đặt: pip install pydantic-settings pydantic
"""
import os
from typing import List
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parent.parent

class Settings(BaseSettings):
    # ==========================================
    # Cấu hình Ứng dụng Backend
    # ==========================================
    PROJECT_NAME: str = "Hate Speech Detection API"
    VERSION: str = "1.0.0"
    API_PREFIX: str = "/api/v1"
    DEBUG_MODE: bool = True
    
    # CORS (Cho phép Frontend gọi API)
    BACKEND_CORS_ORIGINS: List[str] = ["*"] # Trên production nên đổi thành ["http://localhost:3000"]

    # ==========================================
    # Cấu hình Hadoop / HDFS
    # ==========================================
    HDFS_HOST: str = "localhost"
    
    # Port 9870: Dùng cho WebHDFS REST API (Thư viện hdfs)
    HDFS_PORT: int = 9870 
    
    # Port 9000: Dùng cho giao thức RPC nội bộ của PySpark
    HDFS_RPC_PORT: int = 9000 
    
    # User có quyền đọc/ghi trên HDFS (chú ý phân quyền như đã setup)
    HDFS_USER: str = "hadoop" 
    
    # Thư mục gốc chứa dữ liệu crawl trên HDFS
    HDFS_RAW_DATA_DIR: str = "/data/raw"

    HDFS_PROCESSED_DATA_DIR: str = "/data/processed"

    # ==========================================
    # Cấu hình Môi trường Phát triển
    # ==========================================
    # Bật True nếu Docker đang tắt hoặc muốn test UI Frontend nhanh
    USE_MOCK_DATA: bool = False

    # Đọc cấu hình từ file .env (nếu có)
    model_config = SettingsConfigDict(
        env_file=os.path.join(BACKEND_DIR, ".env"),
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

# Khởi tạo instance duy nhất để import ở các file khác
settings = Settings()