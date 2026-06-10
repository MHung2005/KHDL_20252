"""
app/routers/dashboard.py
API endpoints cho Dashboard EDA (Exploratory Data Analysis)
Cung cấp thống kê phân phối nhãn, nguồn, chủ đề, độ dài văn bản
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
    first_crawled: Optional[str]
    last_crawled: Optional[str]

class DashboardSummary(BaseModel):
    total_records: int
    total_platforms: int
    total_labeled: int
    total_unlabeled: int
    platform_stats: List[PlatformStat]
    crawl_timeline: List[Dict[str, Any]]


# ---------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------

@router.get("/summary", response_model=DashboardSummary, summary="Thống kê tổng quan")
async def get_dashboard_summary():
    try:
        if settings.USE_MOCK_DATA:
            platform_stats = mock_data.get_platform_stats()
            crawl_timeline = mock_data.get_crawl_timeline()
            total_records = sum(p["total_records"] for p in platform_stats)
            source_label = mock_data.get_source_label_distribution()
            total_labeled = sum(
                r["count"] for r in source_label if r["label"] != -1
            )
            total_unlabeled = sum(
                r["count"] for r in source_label if r["label"] == -1
            )
            return DashboardSummary(
                total_records=total_records,
                total_platforms=len(platform_stats),
                total_labeled=total_labeled,
                total_unlabeled=total_unlabeled,
                platform_stats=[
                    {"platform": p["platform"],
                     "total_records": p["total_records"],
                     "first_crawled": p.get("first_crawled"),
                     "last_crawled": p.get("last_crawled")}
                    for p in platform_stats
                ],
                crawl_timeline=crawl_timeline,
            )

        engine = spark_engine.get_engine()
        platform_df = engine.platform_comparison().collect()

        platform_stats = []
        total_records = 0
        total_labeled = 0
        total_unlabeled = 0

        for row in platform_df:
            r = row.asDict()
            total = r.get("total", 0)
            chua_gan = r.get("chưa_gán_nhãn", 0)
            total_records += total
            total_labeled += (total - chua_gan)
            total_unlabeled += chua_gan
            platform_stats.append({
                "platform": r["platform"],
                "total_records": total,
                "first_crawled": None,
                "last_crawled": None,
            })

        daily_df = engine.daily_count().collect()
        timeline_dict = {}
        for row in daily_df:
            r = row.asDict()
            date_str = r.get("crawl_date")
            if not date_str:
                continue
            month = date_str[:7]
            plat = r.get("platform")
            count = r.get("total", 0)
            if month not in timeline_dict:
                timeline_dict[month] = {"month": month, "tiktok": 0, "threads": 0}
            if plat in timeline_dict[month]:
                timeline_dict[month][plat] += count

        crawl_timeline = sorted(list(timeline_dict.values()), key=lambda x: x["month"])

        return DashboardSummary(
            total_records=total_records,
            total_platforms=len(platform_stats),
            total_labeled=total_labeled,
            total_unlabeled=total_unlabeled,
            platform_stats=platform_stats,
            crawl_timeline=crawl_timeline,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Dashboard query failed: {str(e)}")


@router.get("/label-distribution", summary="Phân phối nhãn tổng thể")
async def get_label_distribution(
    platform: Optional[str] = Query(None, description="Lọc theo nền tảng: tiktok|threads")
):
    """Trả về phân phối nhãn (bình thường / offensive / hate speech / chưa gán nhãn)"""
    try:
        if settings.USE_MOCK_DATA:
            all_data = mock_data.get_source_label_distribution()
            if platform:
                all_data = [d for d in all_data if d["platform"] == platform]
            label_agg: Dict[str, int] = {}
            for d in all_data:
                key = d["label_name"]
                label_agg[key] = label_agg.get(key, 0) + d["count"]
            return {"success": True, "data": [
                {"label_name": k, "total": v} for k, v in label_agg.items()
            ]}

        engine = spark_engine.get_engine()
        rows = engine.label_distribution(platform=platform).collect()
        data = [{"label_name": r.label_name, "total": r.total} for r in rows]
        return {"success": True, "data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/source-label", summary="Phân phối nhãn theo nguồn (grouped bar)")
async def get_source_label_distribution():
    """So sánh phân phối nhãn giữa các nền tảng"""
    try:
        if settings.USE_MOCK_DATA:
            return {"success": True, "data": mock_data.get_source_label_distribution()}

        engine = spark_engine.get_engine()
        rows = engine.source_label_distribution().collect()
        data = [row.asDict() for row in rows]
        return {"success": True, "data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/topic-distribution", summary="Phân phối bài viết theo chủ đề")
async def get_topic_distribution(
    platform: Optional[str] = Query(None, description="Lọc theo nền tảng")
):
    """Thống kê số lượng bài viết theo từng chủ đề (topic)"""
    try:
        if settings.USE_MOCK_DATA:
            return {"success": True, "data": mock_data.get_topic_distribution()}

        engine = spark_engine.get_engine()
        rows = engine.topic_stats(platform=platform).collect()
        # Gom nhóm topic nếu không lọc platform
        topic_agg: Dict[str, int] = {}
        for row in rows:
            r = row.asDict()
            t = r.get("topic", "unknown")
            topic_agg[t] = topic_agg.get(t, 0) + r.get("total", 0)
        data = [{"topic": t, "total": v} for t, v in
                sorted(topic_agg.items(), key=lambda x: -x[1])]
        return {"success": True, "data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/topic-label-heatmap", summary="Heatmap tỷ lệ nhãn theo chủ đề")
async def get_topic_label_heatmap():
    """Trả về tỷ lệ phần trăm nhãn trong từng chủ đề để vẽ heatmap"""
    try:
        if settings.USE_MOCK_DATA:
            return {"success": True, "data": mock_data.get_topic_label_heatmap()}

        engine = spark_engine.get_engine()
        rows = engine.topic_label_distribution().collect()

        # Gom nhóm theo topic
        topic_counts: Dict[str, Dict] = {}
        for row in rows:
            r = row.asDict()
            t = r.get("topic", "unknown")
            label = r.get("label", -1)
            count = r.get("count", 0)
            if t not in topic_counts:
                topic_counts[t] = {-1: 0, 0: 0, 1: 0, 2: 0}
            topic_counts[t][label] = topic_counts[t].get(label, 0) + count

        result = []
        for topic, counts in topic_counts.items():
            total = sum(counts.values())
            if total == 0:
                continue
            result.append({
                "topic": topic,
                "binh_thuong": round(counts.get(0, 0) / total * 100, 1),
                "offensive":   round(counts.get(1, 0) / total * 100, 1),
                "hate_speech": round(counts.get(2, 0) / total * 100, 1),
            })
        return {"success": True, "data": sorted(result, key=lambda x: x["topic"])}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/text-length-stats", summary="Phân phối độ dài văn bản theo nhãn")
async def get_text_length_stats(
    platform: Optional[str] = Query(None, description="Lọc theo nền tảng")
):
    """Thống kê phân phối độ dài văn bản (min/q1/median/q3/max) theo nhãn — dùng cho boxplot"""
    try:
        if settings.USE_MOCK_DATA:
            data = mock_data.get_text_length_stats()
            if platform:
                data = [d for d in data if d["platform"] == platform]
            return {"success": True, "data": data}

        engine = spark_engine.get_engine()
        rows = engine.text_length_stats(platform=platform).collect()
        data = [row.asDict() for row in rows]
        return {"success": True, "data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/crawl-timeline", summary="Timeline crawl theo tháng")
async def get_crawl_timeline():
    try:
        if settings.USE_MOCK_DATA:
            return mock_data.get_crawl_timeline()

        engine = spark_engine.get_engine()
        daily_df = engine.daily_count().collect()
        timeline_dict = {}
        for row in daily_df:
            r = row.asDict()
            date_str = r.get("crawl_date")
            if not date_str:
                continue
            month = date_str[:7]
            plat = r.get("platform")
            count = r.get("total", 0)
            if month not in timeline_dict:
                timeline_dict[month] = {"month": month, "tiktok": 0, "threads": 0}
            if plat in timeline_dict[month]:
                timeline_dict[month][plat] += count
        return sorted(list(timeline_dict.values()), key=lambda x: x["month"])
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))