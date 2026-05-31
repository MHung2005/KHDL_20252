"""
app/routers/datasets.py
API endpoints quản lý Dataset
"""
import json
from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List, Dict, Any
from pydantic import BaseModel

from app.database import hive_conn, mock_data
from app.config import settings

router = APIRouter()


class DatasetOverview(BaseModel):
    split_set: str
    total_records: int
    platforms: Dict[str, int]
    labels: Dict[str, int]
    ratio: float


@router.get("/overview", summary="Tổng quan Train/Test split")
async def get_dataset_overview():
    """
    Trả về thống kê phân chia Train/Test theo nền tảng và nhãn.
    """
    try:
        if settings.USE_MOCK_DATA:
            raw = mock_data.get_dataset_split_stats()
        else:
            raw = hive_conn.execute_query(
                "SELECT * FROM hate_speech_db.v_dataset_split_stats"
            )

        # Gộp dữ liệu theo split_set
        splits: Dict[str, Dict] = {}
        for row in raw:
            split = row["split_set"]
            if split not in splits:
                splits[split] = {"total": 0, "platforms": {}, "labels": {}}
            splits[split]["total"] += row["record_count"]
            splits[split]["platforms"][row["platform"]] = \
                splits[split]["platforms"].get(row["platform"], 0) + row["record_count"]
            splits[split]["labels"][row["label_name"]] = \
                splits[split]["labels"].get(row["label_name"], 0) + row["record_count"]

        total_all = sum(v["total"] for v in splits.values())
        result = []
        for split_name, data in splits.items():
            result.append({
                "split_set": split_name,
                "total_records": data["total"],
                "platforms": data["platforms"],
                "labels": data["labels"],
                "ratio": round(data["total"] / total_all, 4) if total_all > 0 else 0
            })

        return {"success": True, "data": result, "total_labeled": total_all}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/detail", summary="Chi tiết dataset theo split và nền tảng")
async def get_dataset_detail(
    split_set: Optional[str] = Query(None, description="train | test | validation"),
    platform: Optional[str] = Query(None, description="tiktok | threads | facebook")
):
    """Chi tiết tập dữ liệu, có thể lọc theo split hoặc nền tảng"""
    try:
        if settings.USE_MOCK_DATA:
            data = mock_data.get_dataset_split_stats()
            if split_set:
                data = [d for d in data if d["split_set"] == split_set]
            if platform:
                data = [d for d in data if d["platform"] == platform]
        else:
            conditions = []
            if split_set:
                conditions.append(f"split_set = '{split_set}'")
            if platform:
                conditions.append(f"platform = '{platform}'")
            where = "WHERE " + " AND ".join(conditions) if conditions else ""
            data = hive_conn.execute_query(
                f"SELECT * FROM hate_speech_db.v_dataset_split_stats {where}"
            )

        return {"success": True, "data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/hdfs-files", summary="Danh sách file trên HDFS")
async def get_hdfs_files(path: str = Query("/data", description="HDFS path cần liệt kê")):
    """Liệt kê file trong thư mục HDFS"""
    if settings.USE_MOCK_DATA:
        return {"success": True, "path": path, "files": [
            {"name": "train_tiktok.parquet",   "length": 15728640, "type": "FILE"},
            {"name": "train_threads.parquet",  "length": 10485760, "type": "FILE"},
            {"name": "train_facebook.parquet", "length": 25165824, "type": "FILE"},
            {"name": "test_tiktok.parquet",    "length": 3932160,  "type": "FILE"},
            {"name": "test_threads.parquet",   "length": 2621440,  "type": "FILE"},
            {"name": "test_facebook.parquet",  "length": 6291456,  "type": "FILE"},
        ]}
    from app.database import hdfs_conn
    files = hdfs_conn.list_files(path)
    return {"success": True, "path": path, "files": files}
