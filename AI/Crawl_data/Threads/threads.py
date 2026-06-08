import time
import random
import csv
import io
import uuid
import logging
import re
from datetime import datetime

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from hdfs import InsecureClient

logger = logging.getLogger(__name__)

# ============================================================
#  CẤU HÌNH HDFS
# ============================================================
HDFS_URL  = "http://localhost:9870"
HDFS_USER = "hadoop"
HDFS_BASE = "/data/raw/threads"

def save_to_hdfs(rows: list):
    """Lưu list[dict] bình luận lên HDFS dưới dạng Parquet (SNAPPY)."""
    if not rows:
        return
    today     = datetime.now().strftime("%Y-%m-%d")
    file_id   = uuid.uuid4().hex[:8]
    hdfs_dir  = f"{HDFS_BASE}/crawl_date={today}"
    hdfs_path = f"{hdfs_dir}/part_{file_id}.parquet"

    out = pd.DataFrame([{
        "id":      str(uuid.uuid4()),
        "text":    r["comment_text"],
        "topic":   r["topic"],
        "keyword": r["keyword"],
        "url":     r["post_url"],
        "label":   -1,          # -1 = chưa gán nhãn
    } for r in rows])

    buf = io.BytesIO()
    pq.write_table(pa.Table.from_pandas(out, preserve_index=False), buf, compression="snappy")
    buf.seek(0)

    try:
        client = InsecureClient(HDFS_URL, user=HDFS_USER)
        client.makedirs(hdfs_dir)
        with client.write(hdfs_path, overwrite=True) as f:
            f.write(buf.read())
        logger.info(f"☁️  HDFS: đã lưu {len(out)} dòng → {hdfs_path}")
    except Exception as e:
        logger.warning(f"⚠️  Lưu HDFS thất bại (dữ liệu vẫn có trong CSV): {e}")

METADATA_KEYWORDS = {
     "the_thao":   ["Bóng đá", "Thể thao", "Liên minh huyền thoại", "Liên quân mobile", "Thể hình", "Bóng chuyền", "Cầu lông", "Chạy bộ", "Bóng rổ", "Tin thể thao"],
    # "lam_dep":    ["Trang điểm", "Chăm sóc da", "Làm đẹp", "Đánh giá mỹ phẩm", "Làm tóc", "Chăm sóc da", "Mẹo làm đẹp", "Trị mụn", "Son môi", "Móng tay đẹp" ],
    # "am_thuc":    ["Ẩm thực", "Nấu ăn", "Đánh giá món ăn", "Quay cảnh ăn uống", "Món ngon mỗi ngày", "Công thức nấu ăn", "Ăn vặt", "Địa điểm ăn uống", "Học làm bánh", "Ẩm thực đường phố"],
    # "giai_tri":   ["Xu hướng", "Hài hước", "Thịnh hành", "Nhạc hay", "Đánh giá phim", "Phim hay", "Chương trình giải trí", "Ảnh chế", "Nhạc thư giãn", "Tin giải trí"],
    # "giao_duc":   ["Học tập", "Sách hay", "Tiếng Anh", "Khoa học", "Du học", "Phát triển bản thân", "Mẹo học tập", "Lịch sử", "Tin học văn phòng", "Kỹ năng sống"],
    # "chinh_tri":  ["Tin tức", "Xã hội", "Thời sự", "Tin nóng dư luận", "Bản tin 24 giờ", "Tin nóng", "Sự kiện", "Thế giới", "Phóng sự", "Điểm tin"],
    # "cong_nghe":  ["Công nghệ", "Đánh giá công nghệ", "Thủ thuật", "Trí tuệ nhân tạo", "Điện thoại mới", "Đập hộp", "Máy tính chơi game", "Ứng dụng hay", "Gạt công nghệ", "Nhà thông minh"],
    # "kinh_doanh": ["Kinh doanh", "Khởi nghiệp", "Tài chính", "Chứng khoán", "Kiếm tiền trực tuyến", "Đầu tư", "Quản lý tài chính", "Bất động sản", "Bài học kinh doanh", "Tiếp thị"],
    # "thoi_trang": ["Thời trang", "Trang phục", "Phối đồ", "Thời trang nam", "Thời trang nữ", "Xu hướng thời trang", "Phong cách", "Thương hiệu nội địa", "Phụ kiện thời trang", "Mua sắm quần áo"],
    #"du_lich": ["Du lịch", "Khám phá", "Check-in Việt Nam", "Phượt", "Đánh giá du lịch", "Kinh nghiệm du lịch", "Du lịch tự túc", "Khách sạn đẹp", "Ẩm thực vùng miền", "Cẩm nang chuyến đi"],
}

# Số bài viết tối đa lấy mỗi keyword
MAX_POSTS_PER_KEYWORD = 20

# Số bình luận tối đa lấy mỗi bài viết
MAX_COMMENTS_PER_POST = 10000

# Số lần scroll liên tiếp không ra nội dung mới thì dừng
MAX_NO_NEW = 5


def collect_post_urls(driver, keyword: str, max_posts: int = MAX_POSTS_PER_KEYWORD) -> list[str]:
    """
    Tìm kiếm theo keyword trên Threads và thu thập URL các bài viết.
    Scroll liên tục cho đến khi đủ max_posts URL hoặc không còn bài mới.
    Trả về danh sách URL (đã dedup).
    """
    from selenium.webdriver.common.by import By

    url = f"https://www.threads.com/search?q={keyword.replace(' ', '+')}&serp_type=default"
    driver.get(url)
    time.sleep(random.uniform(3, 5))

    post_urls = []
    seen = set()
    no_new_count = 0

    def extract_urls():
        """Quét toàn bộ anchor hiện tại, trả về số link mới thêm được."""
        new = 0
        for a in driver.find_elements(By.TAG_NAME, "a"):
            if len(post_urls) >= max_posts:
                break
            href = a.get_attribute("href") or ""
            if re.search(r"threads\.com/@[^/]+/post/", href) and href not in seen:
                seen.add(href)
                post_urls.append(href)
                new += 1
        return new

    while len(post_urls) < max_posts:
        new_found = extract_urls()

        if len(post_urls) >= max_posts:
            logger.info(f"  → Đã đủ {max_posts} bài viết, dừng scroll cho keyword '{keyword}'")
            break

        if new_found == 0:
            no_new_count += 1
            logger.debug(f"  Scroll không ra link mới (lần {no_new_count}/{MAX_NO_NEW})")
            if no_new_count >= MAX_NO_NEW:
                logger.info(
                    f"  → Không còn bài mới sau {MAX_NO_NEW} lần scroll, "
                    f"dừng tại {len(post_urls)} bài cho keyword '{keyword}'"
                )
                break
        else:
            no_new_count = 0  # Reset nếu vừa lấy được link mới

        # Scroll xuống cuối trang rồi chờ lazy-load
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(random.uniform(3, 5))

    logger.info(f"  → Tìm được {len(post_urls)} bài viết cho keyword '{keyword}'")
    return post_urls


def collect_comments_from_post(driver, post_url: str, max_comments: int = MAX_COMMENTS_PER_POST) -> list[str]:
    """
    Truy cập trang bài viết và trích xuất bình luận dựa trên cấu trúc DOM thực tế của Threads.

    Chiến lược:
    - Mỗi bình luận/reply trên Threads là một khối `div[data-pressable-container='true']`
    - Bên trong mỗi khối đó, nội dung văn bản nằm trong:
        div.xat24cr > span[dir='auto'] > span   (thẻ span nội dung, KHÔNG có translate="no")
    - Các span[dir='auto'] có attribute translate="no" là tên username → bỏ qua
    - Các thẻ <time> chứa timestamp → bỏ qua
    - Dòng "Đang trả lời @..." nằm trong span.xr9ek0c → bỏ qua

    Scroll động: tiếp tục scroll cho đến khi không còn bình luận mới
    (giống logic collect_post_urls), không scroll cố định số lần.
    """
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC

    driver.get(post_url)

    # Nhãn UI hệ thống cần loại bỏ (so sánh exact)
    SYSTEM_BLACKLIST = {
        "Trả lời", "Xem thêm", "Thích", "Phản hồi", "Chia sẻ",
        "Xem bản dịch", "Xem tất cả", "Đăng lại", "Hàng đầu",
        "Xem hoạt động", "Theo dõi",
    }

    comments = []
    seen_comments = set()

    try:
        # Chờ các khối bình luận xuất hiện lần đầu
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, "div[data-pressable-container='true']")
            )
        )

        no_new_count = 0

        while True:
            # Lấy tất cả block hiện có trên trang
            post_blocks = driver.find_elements(
                By.CSS_SELECTOR, "div[data-pressable-container='true']"
            )

            new_found = 0

            for idx, block in enumerate(post_blocks):
                if len(comments) >= max_comments:
                    break

                # Bỏ qua khối đầu tiên = bài viết gốc (không phải bình luận)
                if idx == 0:
                    continue

                try:
                    # Selector nhắm đúng vào đoạn text nội dung bình luận:
                    # div.xat24cr chứa nội dung → span[dir='auto'] bên trong
                    # KHÔNG lấy span có translate="no" vì đó là username
                    content_spans = block.find_elements(
                        By.CSS_SELECTOR,
                        "div.xat24cr span[dir='auto']:not([translate='no'])"
                    )

                    for span in content_spans:
                        text = span.text.strip()
                        if not text:
                            continue

                        # Bỏ nhãn hệ thống
                        if text in SYSTEM_BLACKLIST:
                            continue

                        # Bỏ dòng "Đang trả lời @..."
                        if text.startswith("Đang trả lời"):
                            continue

                        # Bỏ timestamp dạng "8 giờ", "2 ngày", "vừa xong"...
                        if re.match(r'^\d+\s*(giờ|phút|ngày|tuần|tháng|giây)', text):
                            continue

                        # Bỏ số tương tác đơn thuần: "12", "4,2k", "1/2"
                        if re.match(r'^[\d,./km\s]+$', text.lower()):
                            continue

                        # Bỏ text quá ngắn (dưới 5 ký tự)
                        if len(text) < 5:
                            continue

                        if text not in seen_comments:
                            seen_comments.add(text)
                            comments.append(text)
                            new_found += 1
                            break  # Mỗi block chỉ lấy 1 nội dung chính (tránh lấy sub-span trùng)

                except Exception as e_block:
                    logger.debug(f"    ⚠ Lỗi xử lý block #{idx}: {e_block}")
                    continue

            # Đã đủ số lượng yêu cầu
            if len(comments) >= max_comments:
                logger.info(f"    → Đã đủ {max_comments} bình luận, dừng scroll.")
                break

            # Kiểm tra có ra bình luận mới không
            if new_found == 0:
                no_new_count += 1
                logger.debug(f"    Scroll không ra bình luận mới (lần {no_new_count}/{MAX_NO_NEW})")
                if no_new_count >= MAX_NO_NEW:
                    logger.info(
                        f"    → Không còn bình luận mới sau {MAX_NO_NEW} lần scroll, "
                        f"dừng tại {len(comments)} bình luận."
                    )
                    break
            else:
                no_new_count = 0  # Reset nếu vừa lấy được comment mới

            # Scroll xuống cuối trang rồi chờ lazy-load
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(random.uniform(2, 3))

    except Exception as e:
        logger.error(f"    ❌ Lỗi khi tải hoặc trích xuất bình luận tại {post_url}: {str(e)}")
        return []

    if not comments:
        logger.info(f"    → Không có bình luận nào được trích xuất tại {post_url}")
    else:
        logger.info(f"    → Đã lấy {len(comments)} bình luận thực tế từ {post_url}")

    return comments


def crawl_with_selenium(output_csv: str = "threads_selenium1.csv", headless: bool = False):
    """
    Crawl Threads theo luồng:
      1. Đăng nhập thủ công
      2. Với mỗi keyword → tìm danh sách bài viết
      3. Vào từng bài viết → thu thập bình luận (scroll động đến hết)
      4. Lưu ra CSV với các cột: comment_text, topic, keyword, post_url
    """
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.service import Service
        from selenium.webdriver.chrome.options import Options
        from webdriver_manager.chrome import ChromeDriverManager
    except ImportError:
        logger.error("Thiếu thư viện. Chạy: pip install selenium webdriver-manager")
        return []

    options = Options()
    if headless:
        options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    )

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options,
    )

    # ── Đăng nhập thủ công ───────────────────────────────────────────────────
    logger.info("Đang mở trang đăng nhập Threads...")
    driver.get("https://www.threads.com/login")

    print("\n" + "=" * 60)
    print("🔐  Vui lòng đăng nhập tài khoản Threads trên cửa sổ trình duyệt.")
    print("    Sau khi đăng nhập xong, quay lại đây và nhấn Enter để tiếp tục.")
    print("=" * 60)
    input("👉  Nhấn Enter khi đã đăng nhập xong... ")

    logger.info("Đã xác nhận đăng nhập. Bắt đầu crawl dữ liệu...")
    time.sleep(3)
    # ─────────────────────────────────────────────────────────────────────────

    all_rows = []

    try:
        for topic, keywords in METADATA_KEYWORDS.items():
            for keyword in keywords:
                logger.info(f"[{topic}] Keyword: '{keyword}'")

                # Bước 1: Thu thập URL bài viết từ trang tìm kiếm
                post_urls = collect_post_urls(driver, keyword)

                if not post_urls:
                    logger.warning(f"  Không tìm thấy bài viết nào cho '{keyword}', bỏ qua.")
                    continue

                # Bước 2: Vào từng bài viết, lấy bình luận (scroll động đến hết)
                for post_url in post_urls:
                    comments = collect_comments_from_post(driver, post_url)

                    for comment_text in comments:
                        all_rows.append({
                            "comment_text": comment_text,
                            "topic": topic,
                            "keyword": keyword,
                            "post_url": post_url,
                        })

                    # Nghỉ ngẫu nhiên giữa các bài để tránh bị block
                    time.sleep(random.uniform(3, 5))

    finally:
        driver.quit()

    # ── Dedup theo nội dung bình luận ────────────────────────────────────────
    seen, unique = set(), []
    for r in all_rows:
        key = r["comment_text"][:80].lower()
        if key not in seen:
            seen.add(key)
            unique.append(r)

    # ── Lưu CSV ──────────────────────────────────────────────────────────────
    fieldnames = ["comment_text", "topic", "keyword", "post_url"]
    with open(output_csv, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(unique)

    logger.info(f"Đã lưu {len(unique)} bình luận → {output_csv}")
    save_to_hdfs(unique)
    return unique


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    rows = crawl_with_selenium(headless=False)
    print(f"\n✅ Hoàn thành. Thu thập được {len(rows)} bình luận.")