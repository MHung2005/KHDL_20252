"""
app/routers/models.py
API endpoints đánh giá và so sánh mô hình
"""
import json
from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List, Dict, Any
from pydantic import BaseModel

from app.database import hive_conn, mock_data
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
    Trả về kết quả đánh giá và so sánh tất cả mô hình:
    TF-IDF + SVM, TF-IDF + LR, PhoBERT
    """
    try:
        if settings.USE_MOCK_DATA:
            models = mock_data.get_model_comparison()
        else:
            models = hive_conn.execute_query(
                "SELECT * FROM hate_speech_db.v_model_comparison ORDER BY macro_f1 DESC"
            )

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
        if settings.USE_MOCK_DATA:
            all_models = mock_data.get_model_comparison()
            model = next((m for m in all_models if m["model_id"] == model_id), None)
        else:
            results = hive_conn.execute_query(
                "SELECT * FROM hate_speech_db.v_model_comparison WHERE model_id = %(id)s",
                (model_id,)
            )
            model = results[0] if results else None

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
    """Liệt kê tất cả mô hình đã đăng ký"""
    try:
        if settings.USE_MOCK_DATA:
            models = mock_data.get_model_comparison()
            # Chỉ trả về metadata cơ bản
            return {"success": True, "data": [
                {
                    "model_id": m["model_id"],
                    "model_display_name": m["model_display_name"],
                    "model_type": m["model_type"],
                    "version": m["version"],
                    "accuracy": m["accuracy"],
                    "macro_f1": m["macro_f1"],
                }
                for m in models
            ]}
        else:
            data = hive_conn.execute_query("""
                SELECT model_id, model_display_name, model_type, version,
                       is_active, created_at
                FROM hate_speech_db.model_registry
                WHERE is_active = TRUE
                ORDER BY created_at DESC
            """)
            return {"success": True, "data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
