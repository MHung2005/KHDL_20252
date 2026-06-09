"""
app/routers/datasets.py
API endpoints quản lý Dataset (Sử dụng PySpark và WebHDFS)
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List, Dict, Any
from pydantic import BaseModel
from pyspark.sql import functions as F

# Đổi hive_conn thành spark_engine, giữ nguyên hdfs_conn cho API quét file
from database import spark_engine, hdfs_conn, mock_data
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
            # Logic xử lý mock data giữ nguyên
            splits: Dict[str, Dict] = {}
            for row in raw:
                split = row["split_set"]
                if split not in splits:
                    splits[split] = {"total": 0, "platforms": {}, "labels": {}}
                splits[split]["total"] += row["record_count"]
                splits[split]["platforms"][row["platform"]] = splits[split]["platforms"].get(row["platform"], 0) + row["record_count"]
                splits[split]["labels"][row["label_name"]] = splits[split]["labels"].get(row["label_name"], 0) + row["record_count"]
        else:
            engine = spark_engine.get_engine()
            # Kéo dữ liệu đã gán nhãn và chia tập từ Spark (Hàm này sẽ thêm vào HdfsQuery sau)
            df_processed = engine.get_processed_data()
            
            if df_processed is None:
                return {"success": True, "data": [], "total_labeled": 0}

            # Dùng Spark gom nhóm và đếm siêu tốc
            agg_df = (
                df_processed.groupBy("split_set", "platform", "label")
                .agg(F.count("*").alias("record_count"))
                .collect()
            )

            # Dictionary chuyển đổi ID nhãn thành Tên nhãn cho Frontend dễ đọc
            label_map = {-1: "chưa gán nhãn", 0: "bình thường", 1: "offensive", 2: "hate speech"}
            
            splits: Dict[str, Dict] = {}
            for row in agg_df:
                r = row.asDict()
                split = r.get("split_set")
                if not split: continue
                
                plat = r["platform"]
                label_name = label_map.get(r["label"], "không xác định")
                count = r["record_count"]

                if split not in splits:
                    splits[split] = {"total": 0, "platforms": {}, "labels": {}}
                
                splits[split]["total"] += count
                splits[split]["platforms"][plat] = splits[split]["platforms"].get(plat, 0) + count
                splits[split]["labels"][label_name] = splits[split]["labels"].get(label_name, 0) + count

        # Tính toán tỷ lệ (Ratio) trả về cho UI
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
            return {"success": True, "data": data}

        engine = spark_engine.get_engine()
        df = engine.get_processed_data()
        
        if df is None:
            return {"success": True, "data": []}

        # Áp dụng bộ lọc bằng PySpark thay cho câu lệnh WHERE của SQL
        if split_set:
            df = df.filter(F.col("split_set") == split_set)
        if platform:
            df = df.filter(F.col("platform") == platform)
            
        # Gom nhóm lấy tổng số bản ghi
        agg_df = (
            df.groupBy("split_set", "platform", "label")
            .agg(F.count("*").alias("record_count"))
            .collect()
        )
        
        label_map = {-1: "chưa gán", 0: "bình thường", 1: "offensive", 2: "hate speech"}
        data = []
        for row in agg_df:
            r = row.asDict()
            data.append({
                "split_set": r["split_set"],
                "platform": r["platform"],
                "label_name": label_map.get(r["label"], "unknown"),
                "record_count": r["record_count"]
            })

        return {"success": True, "data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/hdfs-files", summary="Danh sách file trên HDFS")
async def get_hdfs_files(path: str = Query("/data", description="HDFS path cần liệt kê")):
    """Liệt kê file trong thư mục HDFS"""
    if settings.USE_MOCK_DATA:
        return {"success": True, "path": path, "files": [
            {"name": "train_tiktok.parquet",   "length": 15728640, "type": "FILE"},
            {"name": "test_tiktok.parquet",    "length": 3932160,  "type": "FILE"},
        ]}
        
    # Không dùng Spark ở đây vì WebHDFS (port 9870) liệt kê file nhanh và nhẹ hơn Spark nhiều
    files = hdfs_conn.list_files(path)
    return {"success": True, "path": path, "files": files}