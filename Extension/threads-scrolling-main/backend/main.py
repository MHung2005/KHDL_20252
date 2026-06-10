from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from evaluator import SimpleTextEvaluator

app = FastAPI()

# Cấp quyền CORS để Extension có thể gọi API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Khởi tạo class logic
evaluator = SimpleTextEvaluator()

# Định nghĩa cấu trúc dữ liệu nhận từ Extension
class TextPayload(BaseModel):
    text: str
    x: float
    y: float
    width: float
    height: float

@app.post("/analyze")
def analyze_element(payload: TextPayload):
    # Đẩy text vào class logic để kiểm tra
    is_target_word = evaluator.predict(payload.text)
    
    # Nếu đúng là chữ cần tìm, in log tọa độ bằng Python
    if is_target_word:
        print("-" * 40)
        print(f"🎯 PHÁT HIỆN: '{payload.text}'")
        print(f"📍 Tọa độ màn hình: X={payload.x:.1f}, Y={payload.y:.1f}")
        print(f"📏 Kích thước: Rộng={payload.width:.1f}, Cao={payload.height:.1f}")
    
    return {"success": True, "is_target": is_target_word}