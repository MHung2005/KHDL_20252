# Labeling

## 1. Chạy `labeling_with_Qwen.ipynb`

Notebook này được sử dụng để gán nhãn dữ liệu bằng mô hình **Qwen 2.5 7B Instruct** thông qua kỹ thuật quantization với BitsAndBytes.

### Môi trường yêu cầu

* Nền tảng: **Kaggle Notebook**
* Accelerator: **GPU RTX 6000 Pro** (khuyến nghị để đảm bảo đủ VRAM)
* Internet: Tắt (sau khi đã thêm đầy đủ datasets và model)

### Bước 1: Thêm datasets

Trong mục **Add Input** của Kaggle Notebook, thêm các tài nguyên sau:

#### Dataset dữ liệu

* TikTok Mini Dataset:
  https://www.kaggle.com/datasets/phanhuycng/tiktok-mini

#### Thư viện Quantization

* BitsAndBytes:
  https://www.kaggle.com/datasets/phanhuycng/bitsandbtyes

### Bước 2: Thêm model

Trong mục **Add Input**, thêm model:

* Qwen 2.5 7B Instruct:
  https://www.kaggle.com/models/phanhuycng/qwen-2-5-7b-instruct/PyTorch/default/1

### Bước 3: Chọn sheet cần gán nhãn

Trong notebook, tìm biến cấu hình sheet và sửa thành một trong hai giá trị:

```python
SHEET_NAME = "tiktok"
```

hoặc

```python
SHEET_NAME = "threads"
```

* `tiktok`: gán nhãn dữ liệu TikTok.
* `threads`: gán nhãn dữ liệu Threads.

### Bước 4: Chạy notebook

Chạy toàn bộ notebook từ đầu đến cuối:

```text
Runtime → Run All
```

Sau khi hoàn thành, notebook sẽ sinh ra file `.xlsx` chứa kết quả gán nhãn.

### Kết quả đầu ra

File Excel đầu ra sẽ được sử dụng làm đầu vào cho bước Hard Voting ở phần tiếp theo.

---

## 2. Chạy `HardVoting.ipynb`

Notebook này thực hiện tổng hợp kết quả từ các lần gán nhãn bằng phương pháp **Hard Voting** để tạo nhãn cuối cùng.

### Môi trường yêu cầu

* Nền tảng: **Google Colab**
* GPU: **T4**

### Bước 1: Tải notebook lên Colab

Mở file:

```text
HardVoting.ipynb
```

trên Google Colab.

### Bước 2: Tải file kết quả từ Kaggle

Upload file `.xlsx` được sinh ra từ notebook `labeling_with_Qwen.ipynb`.

Ví dụ:

```text
output_tiktok.xlsx
```

hoặc

```text
output_threads.xlsx
```

### Bước 3: Cập nhật đường dẫn file

Trong notebook, sửa biến đường dẫn để trỏ tới file Excel vừa upload.

Ví dụ:

```python
INPUT_FILE = "/content/output_tiktok.xlsx"
```

### Bước 4: Chạy notebook

Chạy toàn bộ notebook:

```text
Runtime → Run All
```

### Kết quả đầu ra

Notebook sẽ tạo ra file dữ liệu cuối cùng sau khi tổng hợp nhãn bằng Hard Voting, được sử dụng cho các bước phân tích và huấn luyện mô hình tiếp theo.

