"""
app/routers/dashboard.py
API endpoints cho Dashboard tổng quan (Sử dụng PySpark Engine)
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List, Dict, Any
from pydantic import BaseModel

from database import spark_engine, mock_data
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
    try:
        if settings.USE_MOCK_DATA:
            platform_stats = mock_data.get_platform_stats()
            crawl_timeline = mock_data.get_crawl_timeline()
            total_records = sum(p["total_records"] for p in platform_stats)
            split_stats = mock_data.get_dataset_split_stats()
            total_labeled = sum(s["record_count"] for s in split_stats)
            
            return DashboardSummary(
                total_records=total_records,
                total_platforms=len(platform_stats),
                total_labeled=total_labeled,
                total_models=3,
                platform_stats=platform_stats,
                crawl_timeline=crawl_timeline,
            )

        # 1. Gọi PySpark Engine
        engine = spark_engine.get_engine()
        
        # 2. Lấy thống kê nền tảng từ Spark
        # platform_comparison() trả về DataFrame: platform, total, chưa_gán_nhãn, bình_thường,...
        platform_df = engine.platform_comparison().collect()
        
        platform_stats = []
        total_records = 0
        total_labeled = 0
        
        for row in platform_df:
            r = row.asDict()
            total = r.get("total", 0)
            chua_gan = r.get("chưa_gán_nhãn", 0)
            da_gan = total - chua_gan
            
            total_records += total
            total_labeled += da_gan
            
            # Map dữ liệu Spark vào Pydantic model (Giả lập các trường Spark chưa tính)
            platform_stats.append({
                "platform": r["platform"],
                "total_records": total,
                "vietnamese_records": total, # Tạm gán bằng total (vì chưa có cột language)
                "first_crawled": None,
                "last_crawled": None,
                "avg_char_count": 0.0
            })

        # 3. Xử lý Timeline (Gom nhóm từ ngày thành tháng)
        # daily_count() trả về: crawl_date, platform, total
        daily_df = engine.daily_count().collect()
        
        timeline_dict = {}
        for row in daily_df:
            r = row.asDict()
            date_str = r.get("crawl_date")
            if not date_str: continue
            
            month = date_str[:7]  # Cắt chuỗi "yyyy-MM-dd" thành "yyyy-MM"
            plat = r.get("platform")
            count = r.get("total", 0)
            
            if month not in timeline_dict:
                timeline_dict[month] = {"month": month, "tiktok": 0, "threads": 0, "facebook": 0}
            
            if plat in timeline_dict[month]:
                timeline_dict[month][plat] += count
                
        # Sắp xếp lại danh sách theo tháng tăng dần
        crawl_timeline = sorted(list(timeline_dict.values()), key=lambda x: x["month"])

        return DashboardSummary(
            total_records=total_records,
            total_platforms=len(platform_stats),
            total_labeled=total_labeled,
            total_models=3,  # Số lượng model có thể fix cứng hoặc query từ DB khác
            platform_stats=platform_stats,
            crawl_timeline=crawl_timeline,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Dashboard query failed: {str(e)}")


@router.get("/platform-stats", summary="Thống kê theo nền tảng")
async def get_platform_stats():
    try:
        if settings.USE_MOCK_DATA:
            return {"success": True, "data": mock_data.get_platform_stats()}
            
        engine = spark_engine.get_engine()
        rows = engine.platform_comparison().collect()
        
        # Format lại dữ liệu cho mượt mà trước khi ném ra API
        data = [row.asDict() for row in rows]
        return {"success": True, "data": data}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/crawl-timeline", response_model=List[CrawlTimelinePoint], summary="Timeline crawl theo tháng")
async def get_crawl_timeline():
    try:
        if settings.USE_MOCK_DATA:
            return mock_data.get_crawl_timeline()
            
        engine = spark_engine.get_engine()
        daily_df = engine.daily_count().collect()
        
        # Tái sử dụng logic gộp ngày thành tháng ở trên
        timeline_dict = {}
        for row in daily_df:
            r = row.asDict()
            date_str = r.get("crawl_date")
            if not date_str: continue
            
            month = date_str[:7]
            plat = r.get("platform")
            count = r.get("total", 0)
            
            if month not in timeline_dict:
                timeline_dict[month] = {"month": month, "tiktok": 0, "threads": 0, "facebook": 0}
            
            if plat in timeline_dict[month]:
                timeline_dict[month][plat] += count
                
        return sorted(list(timeline_dict.values()), key=lambda x: x["month"])
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/label-distribution", summary="Phân phối nhãn dữ liệu")
async def get_label_distribution(
    platform: Optional[str] = Query(None, description="Lọc theo nền tảng: tiktok|threads|facebook")
):
    try:
        if settings.USE_MOCK_DATA:
            all_data = mock_data.get_dataset_split_stats()
            if platform:
                all_data = [d for d in all_data if d["platform"] == platform]
            label_agg: Dict[str, int] = {}
            for d in all_data:
                label_agg[d["label_name"]] = label_agg.get(d["label_name"], 0) + d["record_count"]
            return {"success": True, "data": [{"label": k, "count": v} for k, v in label_agg.items()]}
            
        engine = spark_engine.get_engine()
        
        # Gọi thẳng hàm label_distribution có sẵn trong HdfsQuery
        rows = engine.label_distribution(platform=platform).collect()
        
        data = [{"label": r.label_name, "count": r.total} for r in rows]
        return {"success": True, "data": data}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))