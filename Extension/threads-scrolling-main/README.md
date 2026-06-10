## 1. Tạo môi trường ảo Python 3.10

### Dùng Conda

```bash
conda create -n myenv python=3.10
conda activate myenv
```

### Hoặc dùng venv

```bash
python3.10 -m venv venv
```

Kích hoạt môi trường:

* Windows:

```bash
venv\Scripts\activate
```

* Linux / macOS:

```bash
source venv/bin/activate
```

---

## 2. Cài đặt thư viện từ `requirements.txt`

```bash
pip install -r requirements.txt
```

---

## 3. Thêm extension vào Chrome

* Mở Chrome và truy cập:

```text
chrome://extensions/
```

* Bật **Developer mode**
* Chọn **Load unpacked**
* Thêm thư mục:

```text
extension/
```

---

## 4. Chạy backend

Di chuyển vào thư mục backend:

```bash
cd backend
```

Chạy server:

```bash
uvicorn main:app --reload
```
