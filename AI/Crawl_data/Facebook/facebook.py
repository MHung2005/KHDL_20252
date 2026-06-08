"""
Facebook Comment Crawler - Logic mới 2026
==========================================
1. Tìm kiếm bài viết theo từ khóa
2. Vòng lặp: Nhấn button bình luận → crawl bình luận → scroll tiếp
3. Lặp cho đến khi đủ 20 bài viết mỗi từ khóa

Output: CSV với 3 cột: text, topic, keyword
"""

import time
import random
import urllib.parse
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import (
    TimeoutException, NoSuchElementException, StaleElementReferenceException
)
import io
import uuid
from datetime import datetime
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from hdfs import InsecureClient

# ============================================================
#  CẤU HÌNH HDFS
# ============================================================
HDFS_URL  = "http://localhost:9870"
HDFS_USER = "hadoop"
HDFS_BASE = "/data/raw/facebook"

def save_to_hdfs(df: pd.DataFrame):
    """Lưu DataFrame lên HDFS dưới dạng Parquet (SNAPPY)."""
    today     = datetime.now().strftime("%Y-%m-%d")
    file_id   = uuid.uuid4().hex[:8]
    hdfs_dir  = f"{HDFS_BASE}/crawl_date={today}"
    hdfs_path = f"{hdfs_dir}/part_{file_id}.parquet"

    out = pd.DataFrame({
        "id":      [str(uuid.uuid4()) for _ in range(len(df))],
        "text":    df["text"],
        "topic":   df["topic"],
        "keyword": df["keyword"],
        "url":     "",          # Facebook không lấy được URL comment
        "label":   -1,          # -1 = chưa gán nhãn
    })

    buf = io.BytesIO()
    pq.write_table(pa.Table.from_pandas(out, preserve_index=False), buf, compression="snappy")
    buf.seek(0)

    try:
        client = InsecureClient(HDFS_URL, user=HDFS_USER)
        client.makedirs(hdfs_dir)
        with client.write(hdfs_path, overwrite=True) as f:
            f.write(buf.read())
        print(f"☁️  HDFS: đã lưu {len(out)} dòng → {hdfs_path}")
    except Exception as e:
        print(f"⚠️  Lưu HDFS thất bại (dữ liệu vẫn có trong CSV): {e}")

# ============================================================
#  CẤU HÌNH TỪ KHÓA & CHỦ ĐỀ
# ============================================================
METADATA_KEYWORDS = {
    "the_thao": ["Bóng đá"],
}

# ============================================================
#  CẤU HÌNH CRAWL
# ============================================================
CONFIG = {
    "posts_per_keyword":      20,    # Số bài viết cần crawl mỗi từ khóa
    "max_comments_per_post":  50,    # Giới hạn bình luận mỗi bài
    "scroll_pause_time":       3.0,  # Giây chờ sau mỗi lần scroll
    "page_load_timeout":      30,    # Timeout load trang
    "output_file":            "facebook_comments.csv",
    "max_feed_scrolls":       60,    # Số lần scroll feed tối đa (để tránh vòng lặp vô tận)
}

# ============================================================
#  KHỞI TẠO TRÌNH DUYỆT
# ============================================================
def init_driver(headless: bool = False) -> webdriver.Chrome:
    options = Options()
    if headless:
        options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-notifications")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    options.add_argument("--lang=vi-VN")
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
    driver = webdriver.Chrome(options=options)
    driver.set_page_load_timeout(CONFIG["page_load_timeout"])
    driver.execute_script(
        "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
    )
    return driver

# ============================================================
#  ĐĂNG NHẬP THỦ CÔNG
# ============================================================
def manual_login(driver: webdriver.Chrome) -> bool:
    print("\n" + "=" * 60)
    print("  🔐  ĐĂNG NHẬP FACEBOOK")
    print("=" * 60)
    print("  Vui lòng hoàn thành đăng nhập trên trình duyệt.")
    print("  Sau khi vào được Trang chủ (Newsfeed), quay lại nhấn Enter.")
    print("=" * 60 + "\n")
    driver.get("https://www.facebook.com/")
    input("  👉 Nhấn Enter khi đã đăng nhập xong... ")
    return True

# ============================================================
#  BỘ LỌC CAPTION / HASHTAG
# ============================================================
def _is_caption_or_hashtag(text: str) -> bool:
    words = text.split()
    if not words:
        return True
    hashtag_count = sum(1 for w in words if w.startswith("#"))
    if hashtag_count >= 3:
        return True
    if hashtag_count / len(words) > 0.5:
        return True
    return False

# ============================================================
#  TRÍCH XUẤT LINK BÀI VIẾT TỪ FEED HIỆN TẠI
# ============================================================
def _extract_post_links_from_current_view(driver: webdriver.Chrome) -> list[str]:
    """Trích xuất tất cả link bài viết đang hiển thị trên màn hình."""
    links = []
    seen = set()
    try:
        anchors = driver.find_elements(
            By.XPATH,
            "//a[contains(@href, '/posts/') "
            "or contains(@href, '/permalink.php') "
            "or contains(@href, '/story.php') "
            "or contains(@href, '/videos/') "
            "or contains(@href, '/reel/')]"
        )
        for a in anchors:
            try:
                href = a.get_attribute("href") or ""
                if "facebook.com" not in href or "/search/" in href:
                    continue
                clean = href.split("?")[0].split("#")[0]
                if clean and clean not in seen:
                    seen.add(clean)
                    links.append(clean)
            except StaleElementReferenceException:
                continue
    except Exception:
        pass
    return links

# ============================================================
#  NHẤN BUTTON BÌNH LUẬN ĐỂ MỞ RỘNG COMMENT
# ============================================================
def _click_comment_button(driver: webdriver.Chrome) -> bool:
    """
    Tìm và click nút 'Bình luận' hoặc icon comment trên bài viết đang hiển thị.
    Trả về True nếu click thành công.
    """
    xpaths = [
        # Nút dạng text 'Bình luận' / 'Comment'
        "//div[@role='article'][1]//div[@role='button' and (contains(.,'Bình luận') or contains(.,'Comment'))]",
        # Nút dạng aria-label
        "//div[@role='article'][1]//div[@aria-label='Bình luận']",
        "//div[@role='article'][1]//div[@aria-label='Comment']",
    ]
    for xp in xpaths:
        try:
            btn = driver.find_element(By.XPATH, xp)
            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", btn)
            time.sleep(0.5)
            driver.execute_script("arguments[0].click();", btn)
            time.sleep(2)
            return True
        except NoSuchElementException:
            continue
        except Exception:
            continue
    return False

# ============================================================
#  CRAWL BÌNH LUẬN TỪ SECTION COMMENT (INLINE HOẶC POST PAGE)
# ============================================================
def _collect_comments_from_current_page(driver: webdriver.Chrome,
                                        main_blacklist: set) -> list[str]:
    """Thu thập text bình luận từ trang hiện tại (sau khi đã mở section comment)."""
    ignore_ui = {
        "Thích", "Phản hồi", "Chia sẻ", "Đã chỉnh sửa", "Xem thêm",
        "Bình luận", "Viết bình luận...", "Like", "Reply", "Comment", "Share",
        "Yêu thích", "Haha", "Wow", "Buồn", "Phẫn nộ",
    }

    # Mở rộng các bình luận ẩn
    for _ in range(3):
        try:
            more_btns = driver.find_elements(
                By.XPATH,
                "//div[@role='button'][contains(.,'Xem thêm bình luận') "
                "or contains(.,'Xem các bình luận trước')]"
            )
            for btn in more_btns:
                if btn.is_displayed():
                    driver.execute_script("arguments[0].click();", btn)
                    time.sleep(1.5)
        except Exception:
            pass
        driver.execute_script("window.scrollBy(0, 600);")
        time.sleep(1.5)

    comments = []
    seen = set()
    try:
        elements = driver.find_elements(
            By.XPATH,
            "//div[@dir='auto' and not(ancestor::h1) and not(ancestor::h2)]"
        )
        for el in elements:
            try:
                text = el.text.strip()
            except StaleElementReferenceException:
                continue

            if not text:
                continue
            if text in ignore_ui or text in main_blacklist:
                continue
            if len(text) <= 2:
                continue
            if text.replace(",", "").replace(".", "").replace("K", "").isdigit():
                continue
            if _is_caption_or_hashtag(text):
                continue
            if text not in seen:
                seen.add(text)
                comments.append(text)
            if len(comments) >= CONFIG["max_comments_per_post"]:
                break
    except Exception as e:
        print(f"         ⚠️ Lỗi khi trích xuất comment: {e}")

    return comments

# ============================================================
#  CRAWL 1 BÀI VIẾT (MỞ TRANG CHI TIẾT)
# ============================================================
def crawl_single_post(driver: webdriver.Chrome, post_url: str) -> list[str]:
    """Mở trang bài viết, nhấn nút bình luận, rồi thu thập comment."""
    print(f"         [*] Đang mở: {post_url[:80]}...")
    try:
        driver.get(post_url)
        time.sleep(CONFIG["scroll_pause_time"])
    except Exception as e:
        print(f"         ⚠️ Không mở được bài viết: {e}")
        return []

    # Lấy nội dung bài viết gốc làm blacklist
    main_blacklist: set = set()
    try:
        first_article = driver.find_element(By.XPATH, "//div[@role='article']")
        for el in first_article.find_elements(By.XPATH, ".//div[@dir='auto']"):
            t = el.text.strip()
            if t:
                main_blacklist.add(t)
    except Exception:
        pass

    # Nhấn nút bình luận
    clicked = _click_comment_button(driver)
    if clicked:
        print(f"         [✓] Đã click nút bình luận")
    else:
        print(f"         [~] Không tìm thấy nút bình luận riêng, tiếp tục thu thập...")

    # Thu thập bình luận
    comments = _collect_comments_from_current_page(driver, main_blacklist)
    print(f"         → {len(comments)} bình luận")
    return comments

# ============================================================
#  LOGIC CHÍNH: CRAWL THEO TỪ KHÓA
# ============================================================
def crawl_keyword(driver: webdriver.Chrome, keyword: str) -> list[str]:
    """
    Logic:
    1. Mở trang tìm kiếm Facebook theo từ khóa
    2. Vòng lặp:
       a. Lấy link bài viết đang hiển thị trên feed
       b. Với mỗi link chưa xử lý: mở bài viết, nhấn nút bình luận, crawl
       c. Scroll feed để tải thêm bài viết mới
    3. Dừng khi đủ 20 bài viết
    """
    POSTS_TARGET = CONFIG["posts_per_keyword"]
    all_comments: list[str] = []
    visited_links: set[str] = set()
    feed_scroll_count = 0

    encoded_kw = urllib.parse.quote(keyword)
    search_url = f"https://www.facebook.com/search/posts?q={encoded_kw}"

    print(f"\n     [*] Mở trang tìm kiếm: {search_url}")
    driver.get(search_url)
    time.sleep(5)  # Chờ feed load lần đầu

    print(f"     [*] Bắt đầu vòng lặp — mục tiêu: {POSTS_TARGET} bài viết\n")

    while len(visited_links) < POSTS_TARGET:
        # --- Bước 1: Thu thập link đang hiển thị ---
        current_links = _extract_post_links_from_current_view(driver)
        new_links = [lk for lk in current_links if lk not in visited_links]

        if new_links:
            for url in new_links:
                if len(visited_links) >= POSTS_TARGET:
                    break

                print(f"\n     🗨️  Bài viết {len(visited_links) + 1}/{POSTS_TARGET}")
                comments = crawl_single_post(driver, url)
                all_comments.extend(comments)
                visited_links.add(url)

                # Quay lại trang tìm kiếm để tiếp tục scroll
                print(f"         [*] Quay lại feed tìm kiếm...")
                driver.get(search_url)
                time.sleep(CONFIG["scroll_pause_time"])

                # Scroll xuống để bù lại vị trí đã mất khi reload
                scroll_pixels = feed_scroll_count * 800
                if scroll_pixels > 0:
                    driver.execute_script(f"window.scrollBy(0, {scroll_pixels});")
                    time.sleep(2)

                time.sleep(random.uniform(2, 4))  # Nghỉ tránh bị checkpoint

        # --- Bước 2: Scroll feed để tải thêm bài mới ---
        if len(visited_links) < POSTS_TARGET:
            if feed_scroll_count >= CONFIG["max_feed_scrolls"]:
                print(f"\n     ⚠️ Đã đạt giới hạn scroll ({CONFIG['max_feed_scrolls']} lần). Dừng sớm.")
                break

            print(f"     ↓  Scroll feed lần {feed_scroll_count + 1} để tải thêm bài...")
            driver.execute_script("window.scrollBy(0, 800);")
            time.sleep(CONFIG["scroll_pause_time"])
            feed_scroll_count += 1

    print(f"\n     ✅ Hoàn tất từ khóa '{keyword}': "
          f"{len(visited_links)} bài viết | {len(all_comments)} bình luận")
    return all_comments


# ============================================================
#  HÀM CHẠY TOÀN BỘ & LƯU FILE
# ============================================================
def crawl_all(driver: webdriver.Chrome) -> pd.DataFrame:
    records = []
    total_keywords = sum(len(v) for v in METADATA_KEYWORDS.values())
    processed = 0

    for topic, keywords in METADATA_KEYWORDS.items():
        print(f"\n{'='*60}\n 📂 CHỦ ĐỀ: {topic.upper()}\n{'='*60}")
        for keyword in keywords:
            processed += 1
            print(f"\n🔍 [{processed}/{total_keywords}] Từ khóa: \"{keyword}\"")
            comments = crawl_keyword(driver, keyword)
            for comment in comments:
                records.append({"text": comment, "topic": topic, "keyword": keyword})

    return pd.DataFrame(records, columns=["text", "topic", "keyword"])


def main():
    print(f"🚀 Bắt đầu Crawler lúc: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    driver = init_driver(headless=False)  # False để đăng nhập thủ công

    try:
        if manual_login(driver):
            df = crawl_all(driver)
            df.to_csv(CONFIG["output_file"], index=False, encoding="utf-8-sig")
            print(f"\n💾 THÀNH CÔNG: Đã lưu {len(df)} dòng → '{CONFIG['output_file']}'")
            save_to_hdfs(df)
    finally:
        driver.quit()
        print("🛑 Đã đóng trình duyệt.")


if __name__ == "__main__":
    main()