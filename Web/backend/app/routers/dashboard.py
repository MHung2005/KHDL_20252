"""
app/routers/dashboard.py
API endpoints cho Dashboard tổng quan
"""
import json
from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from pydantic import BaseModel
from typing import List, Dict, Any

from app.database import hive_conn, mock_data
from app.config import settings

router = APIRouter()


# ---------------------------------------------------------------
# Pydantic Response Models
# ---------------------------------------------------------------
class PlatformStat(BaseModel):
    platform: str
    total_records: int
    vietnamese_records: int
    first_crawled: Optional[str]
    last_crawled: Optional[str]
    avg_char_count: float


class DashboardSummary(BaseModel):
    total_records: int
    total_platforms: int
    total_labeled: int
    total_models: int
    platform_stats: List[PlatformStat]
    crawl_timeline: List[Dict[str, Any]]


class CrawlTimelinePoint(BaseModel):
    month: str
    tiktok: int
    threads: int
    facebook: int


# ---------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------

@router.get("/summary", response_model=DashboardSummary, summary="Thống kê tổng quan Dashboard")
async def get_dashboard_summary():
    """
    Trả về thống kê tổng quan:
    - Tổng số bản ghi theo từng nền tảng
    - Timeline crawl theo tháng
    - Tổng số mô hình
    """
    try:
        if settings.USE_MOCK_DATA:
            platform_stats = mock_data.get_platform_stats()
            crawl_timeline = mock_data.get_crawl_timeline()
        else:
            # Query Hive view
            platform_stats = hive_conn.execute_query(
                "SELECT * FROM hate_speech_db.v_platform_stats ORDER BY total_records DESC"
            )
            crawl_timeline = hive_conn.execute_query("""
                SELECT
                    DATE_FORMAT(crawled_at, 'yyyy-MM') AS month,
                    SUM(CASE WHEN platform='tiktok'   THEN 1 ELSE 0 END) AS tiktok,
                    SUM(CASE WHEN platform='threads'  THEN 1 ELSE 0 END) AS threads,
                    SUM(CASE WHEN platform='facebook' THEN 1 ELSE 0 END) AS facebook
                FROM hate_speech_db.raw_crawled_data
                GROUP BY DATE_FORMAT(crawled_at, 'yyyy-MM')
                ORDER BY month ASC
            """)

        total_records = sum(p["total_records"] for p in platform_stats)

        # Lấy tổng labeled từ processed_data
        if settings.USE_MOCK_DATA:
            split_stats = mock_data.get_dataset_split_stats()
            total_labeled = sum(s["record_count"] for s in split_stats)
        else:
            result = hive_conn.execute_query(
                "SELECT COUNT(*) AS cnt FROM hate_speech_db.processed_data"
            )
            total_labeled = result[0]["cnt"] if result else 0

        return DashboardSummary(
            total_records=total_records,
            total_platforms=len(platform_stats),
            total_labeled=total_labeled,
            total_models=3,
            platform_stats=platform_stats,
            crawl_timeline=crawl_timeline,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Dashboard query failed: {str(e)}")


@router.get("/platform-stats", summary="Thống kê theo nền tảng")
async def get_platform_stats():
    """Thống kê chi tiết dữ liệu theo từng nền tảng"""
    try:
        if settings.USE_MOCK_DATA:
            data = mock_data.get_platform_stats()
        else:
            data = hive_conn.execute_query(
                "SELECT * FROM hate_speech_db.v_platform_stats ORDER BY total_records DESC"
            )
        return {"success": True, "data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/crawl-timeline", response_model=List[CrawlTimelinePoint], summary="Timeline crawl theo tháng")
async def get_crawl_timeline():
    """Dữ liệu crawl theo tháng cho từng nền tảng (dùng cho biểu đồ đường)"""
    try:
        if settings.USE_MOCK_DATA:
            return mock_data.get_crawl_timeline()
        return hive_conn.execute_query("""
            SELECT
                DATE_FORMAT(crawled_at, 'yyyy-MM') AS month,
                SUM(CASE WHEN platform='tiktok'   THEN 1 ELSE 0 END) AS tiktok,
                SUM(CASE WHEN platform='threads'  THEN 1 ELSE 0 END) AS threads,
                SUM(CASE WHEN platform='facebook' THEN 1 ELSE 0 END) AS facebook
            FROM hate_speech_db.raw_crawled_data
            GROUP BY DATE_FORMAT(crawled_at, 'yyyy-MM')
            ORDER BY month ASC
        """)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/label-distribution", summary="Phân phối nhãn dữ liệu")
async def get_label_distribution(
    platform: Optional[str] = Query(None, description="Lọc theo nền tảng: tiktok|threads|facebook")
):
    """Phân phối nhãn (normal/hate_speech/offensive) toàn bộ hoặc theo nền tảng"""
    try:
        if settings.USE_MOCK_DATA:
            all_data = mock_data.get_dataset_split_stats()
            if platform:
                all_data = [d for d in all_data if d["platform"] == platform]
            # Gộp theo label
            label_agg: Dict[str, int] = {}
            for d in all_data:
                label_agg[d["label_name"]] = label_agg.get(d["label_name"], 0) + d["record_count"]
            return {"success": True, "data": [
                {"label": k, "count": v} for k, v in label_agg.items()
            ]}
        else:
            sql = """
                SELECT label_name, COUNT(*) as count
                FROM hate_speech_db.processed_data
                {where}
                GROUP BY label_name
            """
            where = f"WHERE platform = '{platform}'" if platform else ""
            data = hive_conn.execute_query(sql.format(where=where))
            return {"success": True, "data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
