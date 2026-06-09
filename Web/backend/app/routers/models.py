"""
app/routers/models.py
API endpoints đánh giá và so sánh mô hình (Đang dùng Mock Data để test UI)
"""
import json
from fastapi import APIRouter, HTTPException
from typing import Optional, List, Dict, Any
from pydantic import BaseModel

# Loại bỏ hive_conn, chỉ giữ lại mock_data
from database import mock_data
from app.config import settings

router = APIRouter()

class ModelMetrics(BaseModel):
    model_id: str
    model_display_name: str
    model_type: str
    version: str
    accuracy: float
    macro_f1: float
    weighted_f1: float
    macro_precision: float
    macro_recall: float
    target_hate_f1: float
    target_offensive_f1: float
    target_normal_f1: float
    confusion_matrix: str
    train_ratio: float
    test_ratio: float
    total_samples: int
    evaluated_at: str


@router.get("/comparison", summary="So sánh hiệu năng tất cả mô hình")
async def get_model_comparison():
    """
    Trả về kết quả đánh giá và so sánh tất cả mô hình.
    Hiện tại ĐANG ÉP DÙNG MOCK DATA để Frontend test giao diện biểu đồ.
    """
    try:
        # TODO: Sau này khi có dữ liệu thật trên HDFS/MLflow, thay thế đoạn này bằng Spark
        models = mock_data.get_model_comparison()

        # Parse confusion matrix JSON string
        for m in models:
            if isinstance(m.get("confusion_matrix"), str):
                try:
                    m["confusion_matrix"] = json.loads(m["confusion_matrix"])
                except Exception:
                    m["confusion_matrix"] = []

        return {"success": True, "data": models}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{model_id}", summary="Chi tiết một mô hình")
async def get_model_detail(model_id: str):
    """Lấy thông tin chi tiết một mô hình theo ID"""
    try:
        all_models = mock_data.get_model_comparison()
        model = next((m for m in all_models if m["model_id"] == model_id), None)

        if not model:
            raise HTTPException(status_code=404, detail=f"Model '{model_id}' not found")

        if isinstance(model.get("confusion_matrix"), str):
            try:
                model["confusion_matrix"] = json.loads(model["confusion_matrix"])
            except Exception:
                model["confusion_matrix"] = []

        return {"success": True, "data": model}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", summary="Danh sách tất cả mô hình")
async def list_models():
    """Liệt kê tất cả mô hình đã đăng ký (Dùng cho bảng hoặc Dropdown)"""
    try:
        models = mock_data.get_model_comparison()
        # Chỉ lấy metadata cơ bản đẩy ra cho nhẹ API
        data = [
            {
                "model_id": m["model_id"],
                "model_display_name": m["model_display_name"],
                "model_type": m["model_type"],
                "version": m["version"],
                "accuracy": m["accuracy"],
                "macro_f1": m["macro_f1"],
                "is_active": True,
                "created_at": m["evaluated_at"]
            }
            for m in models
        ]
        return {"success": True, "data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))