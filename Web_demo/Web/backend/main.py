"""
Hate Speech Detection System - FastAPI Backend
Kết nối Spark/HDFS và cung cấp REST API cho Frontend
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
from contextlib import asynccontextmanager

# Cập nhật lại import: Bỏ hive_conn, thêm spark_engine
from app.routers import dashboard
from database import spark_engine, test_connections
from app.config import settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Khởi tạo kết nối khi startup, đóng khi shutdown"""
    logger.info("🚀 Starting Hate Speech Detection API Server...")
    try:
        await test_connections()
        logger.info("✅ Spark & HDFS connections established")
    except Exception as e:
        logger.warning(f"⚠️  Connection test failed (running in mock data mode): {e}")
        
    yield  # Ứng dụng chạy tại đây
    
    logger.info("🔌 Shutting down API server...")
    # BẮT BUỘC: Giải phóng RAM và tắt máy ảo Java của Spark khi tắt Backend
    spark_engine.close()


app = FastAPI(
    title="Hate Speech Detection - Management API",
    description="""
    API quản lý dữ liệu và kết quả huấn luyện mô hình Hate Speech Detection.
    
    ## Tính năng:
    - **Dashboard**: Thống kê tổng quan dữ liệu crawl bằng PySpark
    - **Datasets**: Quản lý và thống kê tập dữ liệu Train/Test
    - **Models**: So sánh hiệu năng các mô hình AI
    """,
    version="1.0.0",
    lifespan=lifespan
)

# CORS - cho phép React frontend kết nối
app.add_middleware(
    CORSMiddleware,
    # Sửa lại tên biến cho khớp với config.py mới
    allow_origins=settings.BACKEND_CORS_ORIGINS, 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Đăng ký routers
app.include_router(dashboard.router, prefix="/api/v1/dashboard", tags=["Dashboard"])

@app.get("/", tags=["Health"])
async def root():
    return {
        "service": "Hate Speech Detection API",
        "version": "1.0.0",
        "status": "running",
        "engine": "PySpark + WebHDFS",
        "docs": "/docs"
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """Kiểm tra trạng thái kết nối các dịch vụ Big Data"""
    status = {
        "api": "healthy",
        "spark": "unknown", # Đổi từ hive sang spark
        "hdfs": "unknown"
    }
    try:
        await test_connections()
        status["spark"] = "healthy"
        status["hdfs"] = "healthy"
    except Exception as e:
        # Nếu đang bật USE_MOCK_DATA = True trong .env thì API vẫn báo lỗi ở đây nhưng app vẫn chạy tốt
        status["spark"] = f"error/mock_mode: {str(e)}"

    return status