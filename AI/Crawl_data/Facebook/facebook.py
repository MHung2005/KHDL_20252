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
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
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
    "posts_per_keyword":      2,    # Số bài viết cần crawl mỗi từ khóa
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
                                        main_blacklist: set,
                                        context_element=None) -> list[str]:
    """Thu thập text bình luận trong một phạm vi cụ thể (Inline hoặc Modal)."""
    ignore_ui = {
        "Thích", "Phản hồi", "Chia sẻ", "Đã chỉnh sửa", "Xem thêm",
        "Bình luận", "Viết bình luận...", "Like", "Reply", "Comment", "Share",
        "Yêu thích", "Haha", "Wow", "Buồn", "Phẫn nộ",
    }

    # Nếu có context_element (vùng chứa) thì tìm trong đó, không thì tìm toàn màn hình
    context = context_element if context_element else driver

    # Mở rộng bình luận (LƯU Ý CÓ DẤU CHẤM TRƯỚC //)
    for _ in range(3):
        try:
            more_btns = context.find_elements(
                By.XPATH,
                ".//div[@role='button'][contains(.,'Xem thêm bình luận') "
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
        # LƯU Ý CÓ DẤU CHẤM TRƯỚC // ĐỂ KHÔNG BỊ QUÉT TEXT CỦA BÀI KHÁC TRÊN FEED
        elements = context.find_elements(
            By.XPATH,
            ".//div[@dir='auto' and not(ancestor::h1) and not(ancestor::h2)]"
        )
        for el in elements:
            try:
                text = el.text.strip()
            except StaleElementReferenceException:
                continue

            if not text or text in ignore_ui or text in main_blacklist:
                continue
            if len(text) <= 2 or text.replace(",", "").replace(".", "").replace("K", "").isdigit():
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
#  LOGIC CHÍNH: CRAWL THEO TỪ KHÓA (UPDATE LÀM VIỆC TRÊN FEED)
# ============================================================
def crawl_keyword(driver: webdriver.Chrome, keyword: str) -> list[str]:
    """
    Logic mới 2026:
    1. Mở trang tìm kiếm Facebook theo từ khóa.
    2. Quét các nút bình luận chưa tương tác (dùng thuộc tính tự chế data-crawled).
    3. Click mở bình luận ngay trên Feed (Inline hoặc Modal).
    4. Cào dữ liệu text, sau đó nhấn ESC để đóng Modal (nếu là Reels).
    5. Cuộn xuống để tải thêm bài.
    """
    POSTS_TARGET = CONFIG["posts_per_keyword"]
    all_comments: list[str] = []
    feed_scroll_count = 0
    processed_count = 0

    encoded_kw = urllib.parse.quote(keyword)
    search_url = f"https://www.facebook.com/search/posts?q={encoded_kw}"

    print(f"\n     [*] Mở trang tìm kiếm: {search_url}")
    driver.get(search_url)
    time.sleep(5)  # Chờ feed load lần đầu

    print(f"     [*] Bắt đầu vòng lặp — mục tiêu: {POSTS_TARGET} bài viết\n")

    while processed_count < POSTS_TARGET:
        # TÌm các nút bình luận dựa vào class/role bạn cung cấp, 
        # CỰC KỲ QUAN TRỌNG: Loại trừ những nút đã được đánh dấu 'data-crawled'
        buttons = driver.find_elements(
            By.XPATH,
            "//div[@data-ad-rendering-role='comment_button' and not(@data-crawled='true')]"
        )

        if buttons:
            btn = buttons[0] # Luôn lấy nút đầu tiên tìm thấy trong danh sách chưa xử lý
            try:
                # 1. Đánh dấu nút này đã xử lý bằng JavaScript để các vòng lặp sau bỏ qua
                driver.execute_script("arguments[0].setAttribute('data-crawled', 'true');", btn)

                # 2. Cuộn nút vào giữa màn hình
                driver.execute_script("arguments[0].scrollIntoView({block:'center'});", btn)
                time.sleep(1)

                # 3. Trích xuất blacklist (nội dung post) để lọc rác. 
                # (Tìm thẻ article cha gần nhất của nút bình luận này)
                main_blacklist = set()
                try:
                    parent_article = btn.find_element(By.XPATH, "./ancestor::div[@role='article'][1]")
                    for el in parent_article.find_elements(By.XPATH, ".//div[@dir='auto']"):
                        t = el.text.strip()
                        if t:
                            main_blacklist.add(t)
                except Exception:
                    pass # Nếu không tìm thấy, bỏ qua blacklist cho bài này

                # 4. Click mở bình luận
                driver.execute_script("arguments[0].click();", btn)
                time.sleep(3)  # Chờ comment popup/inline hiển thị

                processed_count += 1
                print(f"\n     🗨️  Bài viết {processed_count}/{POSTS_TARGET}")

                # 5. Thu thập bình luận (Sử dụng nguyên bản hàm cũ của bạn)
                comments = _collect_comments_from_current_page(driver, main_blacklist)
                all_comments.extend(comments)
                print(f"         → {len(comments)} bình luận")

                # 6. THOÁT MODAL: Nếu post là dạng Reel/Video, click sẽ mở một màn hình đen (Modal).
                # Nhấn ESCAPE để tắt nó đi, trả màn hình về lại trang tìm kiếm ban đầu.
                ActionChains(driver).send_keys(Keys.ESCAPE).perform()
                time.sleep(1)

            except Exception as e:
                print(f"         ⚠️ Lỗi khi xử lý bài viết (có thể bị che mất hoặc stale): {e}")
                processed_count += 1 # Bỏ qua bài lỗi, đi tiếp tới bài sau
        else:
            # Nếu không tìm thấy nút nào mới trên màn hình -> cuộn feed xuống
            if feed_scroll_count >= CONFIG["max_feed_scrolls"]:
                print(f"\n     ⚠️ Đã đạt giới hạn scroll ({CONFIG['max_feed_scrolls']} lần). Dừng sớm.")
                break

            print(f"     ↓  Scroll feed lần {feed_scroll_count + 1} để tải thêm bài...")
            driver.execute_script("window.scrollBy(0, 1000);")
            time.sleep(CONFIG["scroll_pause_time"])
            feed_scroll_count += 1

    print(f"\n     ✅ Hoàn tất từ khóa '{keyword}': "
          f"{processed_count} bài viết | {len(all_comments)} bình luận")
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