"""
Hate Speech Detection System - FastAPI Backend
Kết nối Hive/HDFS và cung cấp REST API cho Frontend
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
from contextlib import asynccontextmanager

from app.routers import dashboard, datasets, models
from app.database import hive_conn, test_connections
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
        logger.info("✅ Hive & HDFS connections established")
    except Exception as e:
        logger.warning(f"⚠️  Connection test failed (running in demo mode): {e}")
    yield
    logger.info("🔌 Shutting down API server...")


app = FastAPI(
    title="Hate Speech Detection - Management API",
    description="""
    API quản lý dữ liệu và kết quả huấn luyện mô hình Hate Speech Detection.
    
    ## Tính năng:
    - **Dashboard**: Thống kê tổng quan dữ liệu crawl
    - **Datasets**: Quản lý và thống kê tập dữ liệu Train/Test
    - **Models**: So sánh hiệu năng các mô hình AI
    """,
    version="1.0.0",
    lifespan=lifespan
)

# CORS - cho phép React frontend kết nối
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Đăng ký routers
app.include_router(dashboard.router, prefix="/api/v1/dashboard", tags=["Dashboard"])
app.include_router(datasets.router, prefix="/api/v1/datasets", tags=["Datasets"])
app.include_router(models.router, prefix="/api/v1/models", tags=["Models"])


@app.get("/", tags=["Health"])
async def root():
    return {
        "service": "Hate Speech Detection API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs"
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """Kiểm tra trạng thái kết nối"""
    status = {
        "api": "healthy",
        "hive": "unknown",
        "hdfs": "unknown"
    }
    try:
        await test_connections()
        status["hive"] = "healthy"
        status["hdfs"] = "healthy"
    except Exception as e:
        status["hive"] = f"error: {str(e)}"

    return status
