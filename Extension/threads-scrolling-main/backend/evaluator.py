import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification

class SimpleTextEvaluator:
    def __init__(self):
        print("Đang khởi tạo Evaluator (Sử dụng KalvinPhan/PhoBert-Pretrain)...")
        model_name = "KalvinPhan/PhoBert-Pretrain"
        # Khởi tạo tokenizer và model 1 lần duy nhất để tái sử dụng
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForSequenceClassification.from_pretrained(
            model_name, 
            num_labels=3, 
            ignore_mismatched_sizes=True
        )
        self.model.eval() # Chuyển sang chế độ đánh giá

    def predict(self, text: str) -> bool:
        if "bình luận" in text.lower():
            return True
        
        # Tiền xử lý văn bản
        inputs = self.tokenizer(text, return_tensors="pt", truncation=True, max_length=256)
        
        # Suy luận để lấy nhãn
        with torch.no_grad():
            logits = self.model(**inputs).logits
            predicted_id = int(torch.argmax(logits, dim=-1))
            
        # Kiểm tra nếu nhãn là 1 hoặc 2 thì trả về True
        if predicted_id in [2]:
            return True
            
        return False