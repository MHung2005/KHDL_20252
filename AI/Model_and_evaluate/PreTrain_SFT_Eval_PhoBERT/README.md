# SFT and Evaluation with PhoBERT

## 1. Continued Pretraining PhoBERT

Notebook: `phobert-pretrain.ipynb`

Notebook này thực hiện continued pretraining cho PhoBERT trên tập dữ liệu thu thập từ mạng xã hội trước khi tiến hành huấn luyện tác vụ Hate Speech Detection.

### Môi trường yêu cầu

* Nền tảng: **Kaggle Notebook**
* GPU khuyến nghị:

  * RTX 6000 Pro
  * Hoặc GPU có hiệu năng và VRAM tương đương

### Bước 1: Thêm dataset

Trong mục **Add Input**, thêm dataset:

* https://www.kaggle.com/datasets/phanhuycng/phobert-pretrain-dataset

### Bước 2: Thêm model PhoBERT

Trong mục **Add Input**, thêm model:

* https://www.kaggle.com/models/phanhuycng/phobert-base-v2/PyTorch/default/1

### Bước 3: Chạy notebook

Mở:

```text
phobert-pretrain.ipynb
```

và chạy toàn bộ notebook:

```text
Run All
```

### Bước 4: Tải model đầu ra

Sau khi hoàn tất quá trình pretraining, notebook sẽ sinh ra model checkpoint mới.

Tải toàn bộ thư mục model đầu ra từ Kaggle về máy để sử dụng cho bước SFT ở phần tiếp theo.

---

## 2. Supervised Fine-tuning and Evaluation

Notebook: `SFT_and_Evaluate_PhoBert.ipynb`

Notebook này thực hiện huấn luyện và đánh giá mô hình PhoBERT trên bộ dữ liệu đã được gán nhãn.

### Chuẩn bị dữ liệu

Sử dụng file dữ liệu đã được tạo ở giai đoạn Labeling (sau bước Hard Voting).

Upload file dữ liệu này lên Google Drive hoặc vị trí lưu trữ được notebook sử dụng.

### Cấu hình Secrets

Trước khi chạy notebook, cần cập nhật các biến bí mật (Secrets) cho phù hợp với tài khoản của người dùng.

Ví dụ:

```python
HF_TOKEN = "your_huggingface_token"
```

Các token, API key hoặc thông tin xác thực khác cần được thay thế bằng giá trị tương ứng của người sử dụng.

### Chạy notebook

Mở:

```text
SFT_and_Evaluate_PhoBert.ipynb
```

Sau khi dữ liệu và secrets đã được cấu hình đúng, chạy toàn bộ notebook:

```text
Run All
```

### Kết quả

Notebook sẽ:

1. Nạp mô hình PhoBERT đã được continued pretraining.
2. Huấn luyện trên bộ dữ liệu đã gán nhãn.
3. Đánh giá mô hình trên tập kiểm thử.
4. Xuất các chỉ số đánh giá phục vụ cho quá trình phân tích kết quả.

