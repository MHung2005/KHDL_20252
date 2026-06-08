"""
TikTok Comment Scraper — Playwright
====================================
Thu thập bình luận từ TikTok theo từ khóa tìm kiếm, phân nhóm theo chủ đề.

Luồng xử lý chính:
    1. Mở trang tìm kiếm theo từ khóa → lấy danh sách URL video
    2. Mở từng video   → cuộn phần bình luận → thu thập bình luận
    3. Lưu kết quả vào file CSV duy nhất (tránh trùng lặp)
"""

import asyncio
import csv
import io
import uuid
import random
import re
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from hdfs import InsecureClient
from playwright.async_api import async_playwright, Page, BrowserContext

# ============================================================
#  CẤU HÌNH HDFS
# ============================================================
HDFS_URL  = "http://localhost:9870"
HDFS_USER = "hadoop"
HDFS_BASE = "/data/raw/tiktok"

def save_to_hdfs(comments: list):
    """Lưu list[Comment] lên HDFS dưới dạng Parquet (SNAPPY)."""
    if not comments:
        return
    today     = datetime.now().strftime("%Y-%m-%d")
    file_id   = uuid.uuid4().hex[:8]
    hdfs_dir  = f"{HDFS_BASE}/crawl_date={today}"
    hdfs_path = f"{hdfs_dir}/part_{file_id}.parquet"

    out = pd.DataFrame([{
        "id":      str(uuid.uuid4()),
        "text":    c.text.strip(),
        "topic":   c.topic,
        "keyword": c.keyword,
        "url":     c.video_url,
        "label":   -1,          # -1 = chưa gán nhãn
    } for c in comments])

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


# ===========================================================================
# Hằng số cấu hình
# ===========================================================================

# Danh sách chủ đề và từ khóa tìm kiếm tương ứng
TOPICS: dict[str, list[str]] = {
    #"the_thao":   ["Bóng đá", "Thể thao", "Liên minh huyền thoại", "Liên quân mobile", "Thể hình", "Bóng chuyền", "Cầu lông", "Chạy bộ", "Bóng rổ", "Tin thể thao"],
    # "lam_dep":    ["Trang điểm", "Chăm sóc da", "Làm đẹp", "Đánh giá mỹ phẩm", "Làm tóc", "Chăm sóc da", "Mẹo làm đẹp", "Trị mụn", "Son môi", "Móng tay đẹp"],
    # "am_thuc":    ["Ẩm thực", "Nấu ăn", "Đánh giá món ăn", "Quay cảnh ăn uống", "Món ngon mỗi ngày", "Công thức nấu ăn", "Ăn vặt", "Địa điểm ăn uống", "Học làm bánh", "Ẩm thực đường phố"],
    # "giai_tri":   ["Xu hướng", "Hài hước", "Thịnh hành", "Nhạc hay", "Đánh giá phim", "Phim hay", "Chương trình giải trí", "Ảnh chế", "Nhạc thư giãn", "Tin giải trí"],
    # "giao_duc":   ["Học tập", "Sách hay", "Tiếng Anh", "Khoa học", "Du học", "Phát triển bản thân", "Mẹo học tập", "Lịch sử", "Tin học văn phòng", "Kỹ năng sống"],
    "chinh_tri":  ["Thế giới"],
    # "chinh_tri":  ["Tin tức", "Xã hội", "Thời sự", "Tin nóng dư luận", "Bản tin 24 giờ", "Tin nóng", "Sự kiện", "Thế giới", "Phóng sự", "Điểm tin"],
    # "cong_nghe":  ["Công nghệ", "Đánh giá công nghệ", "Thủ thuật", "Trí tuệ nhân tạo", "Điện thoại mới", "Đập hộp", "Máy tính chơi game", "Ứng dụng hay", "Gạt công nghệ", "Nhà thông minh"],
    # "kinh_doanh": ["Kinh doanh", "Khởi nghiệp", "Tài chính", "Chứng khoán", "Kiếm tiền trực tuyến", "Đầu tư", "Quản lý tài chính", "Bất động sản", "Bài học kinh doanh", "Tiếp thị"],
    # "thoi_trang": [ "Thời trang", "Trang phục", "Phối đồ", "Thời trang nam", "Thời trang nữ", "Xu hướng thời trang", "Phong cách", "Thương hiệu nội địa", "Phụ kiện thời trang", "Mua sắm quần áo" ],
    #"du_lich": [ "Du lịch", "Khám phá", "Check-in Việt Nam", "Phượt", "Đánh giá du lịch", "Kinh nghiệm du lịch", "Du lịch tự túc", "Khách sạn đẹp", "Ẩm thực vùng miền", "Cẩm nang chuyến đi" ],
}

# Danh sách User-Agent để luân phiên, tránh bị chặn
USER_AGENTS: list[str] = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
]

# CSS selector để tìm phần tử bình luận (TikTok hay thay đổi class, nên dùng nhiều fallback)
COMMENT_SELECTORS: list[str] = [
    '[data-e2e="comment-level-1"]',       # selector cũ (giữ lại phòng trường hợp rollback)
    'div[class*="CommentItemWrapper"]',
    'p[data-e2e="comment-level-1-text"]',
]

# Selector container bình luận (dùng để scroll)
COMMENT_CONTAINER_SELECTORS: list[str] = [
    '[class*="DivCommentMain"]',               # video page — đã xác nhận (2025)
    '[data-e2e="search-comment-container"]',   # search page
    '[data-e2e="comment-list"]',               # fallback cũ
]

# Pattern URL của video TikTok
VIDEO_URL_PATTERN = re.compile(r"/video/(\d+)")

# Pattern nút/tab Bình luận
COMMENT_TAB_PATTERN = re.compile(r"Bình luận|Comments", re.IGNORECASE)


# ===========================================================================
# Model dữ liệu
# ===========================================================================

@dataclass
class Comment:
    """
    Đại diện cho một bình luận thô thu thập được từ TikTok.

    Các trường nhãn (label, confidence, label_method) được điền
    sau khi phân loại — mặc định chưa gán nhãn.
    """
    comment_id:   str
    text:         str
    author:       str
    likes:        int
    topic:        str
    keyword:      str
    video_url:    str
    video_id:     str
    scraped_at:   str
    label:        int   = -1      # -1 = chưa gán nhãn
    confidence:   float = 0.0
    label_method: str   = "none"


# ===========================================================================
# Scraper chính
# ===========================================================================

class TikTokScraper:
    """
    Crawl bình luận TikTok sử dụng Playwright (headless Chromium).

    Tham số khởi tạo:
        output_dir   : Thư mục lưu file CSV đầu ra
        max_videos   : Số video tối đa mỗi từ khóa
        max_comments : Số bình luận tối đa mỗi video
        headless     : Chạy trình duyệt ẩn (True) hay hiện (False)
        page_wait    : Thời gian chờ sau khi tải trang (giây)
        delay_min    : Thời gian chờ ngẫu nhiên tối thiểu giữa các bước (giây)
        delay_max    : Thời gian chờ ngẫu nhiên tối đa giữa các bước (giây)
    """

    def __init__(
        self,
        output_dir:   str   = "data/raw",
        max_videos:   int   = 20,
        max_comments: int   = 10000,
        headless:     bool  = True,
        page_wait:    float = 5.0,
        delay_min:    float = 1.0,
        delay_max:    float = 2.0,
    ):
        self.output_dir   = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.max_videos   = max_videos
        self.max_comments = max_comments
        self.headless     = headless
        self.page_wait    = page_wait
        self.delay_min    = delay_min
        self.delay_max    = delay_max

    # -----------------------------------------------------------------------
    # Tiện ích nội bộ
    # -----------------------------------------------------------------------

    async def _wait_random(self):
        """Chờ một khoảng thời gian ngẫu nhiên để giả lập hành vi người dùng."""
        await asyncio.sleep(random.uniform(self.delay_min, self.delay_max))

    async def _wait_for_page(self, page: Page):
        """Chờ trang tải xong theo thời gian cấu hình."""
        await page.wait_for_timeout(int(self.page_wait * 1_000))

    async def _scroll_down(self, page: Page, times: int = 3, distance: int = 3000):
        """
        Cuộn trang tìm kiếm xuống để load thêm video.

        TikTok dùng body overflow:hidden nên window.scrollBy không hoạt động.
        Thay vào đó scroll container kết quả tìm kiếm, hoặc dùng mouse wheel.
        """
        for _ in range(times):
            scrolled = await page.evaluate(f"""
                (() => {{
                    // Thử các container kết quả tìm kiếm phổ biến
                    const candidates = [
                        document.querySelector('[data-e2e="search-video-container"]'),
                        document.querySelector('[data-e2e="search_top-item-list"]'),
                        document.querySelector('[data-e2e="search-card-container"]'),
                        document.querySelector('main'),
                        document.querySelector('[class*="DivContentContainer"]'),
                        document.querySelector('[class*="search"]'),
                    ];
                    for (const el of candidates) {{
                        if (el) {{
                            el.scrollBy(0, {distance});
                            el.scrollTop += {distance};
                            return el.getAttribute('data-e2e') || el.tagName;
                        }}
                    }}
                    // Last resort
                    window.scrollBy(0, {distance});
                    return 'window';
                }})()
            """)
            print(f"    [scroll-search] container={scrolled}")
            if scrolled == 'window':
                # TikTok search page: thử mouse wheel ở giữa trang
                try:
                    vp = page.viewport_size
                    if vp:
                        cx, cy = vp["width"] // 2, vp["height"] // 2
                        await page.mouse.move(cx, cy)
                        for _ in range(6):
                            await page.mouse.wheel(0, 500)
                            await asyncio.sleep(0.15)
                except Exception:
                    pass
            await self._wait_random()

    async def _scroll_comment_container(self, page: Page, times: int = 1, distance: int = 2000):
        """
        Cuộn bên trong container bình luận của TikTok.

        Chiến lược theo thứ tự ưu tiên:
        1. Thử từng selector trong COMMENT_CONTAINER_SELECTORS (scrollBy + scrollTop)
        2. Fallback: hover vào bình luận cuối cùng rồi dùng mouse wheel
        3. Fallback cuối: dùng keyboard End/PageDown trên element đó
        """
        for _ in range(times):
            scrolled = await page.evaluate(f"""
                (() => {{
                    const selectors = {COMMENT_CONTAINER_SELECTORS!r};
                    for (const sel of selectors) {{
                        const el = document.querySelector(sel);
                        if (el) {{
                            el.scrollBy(0, {distance});
                            el.scrollTop += {distance};
                            return sel;
                        }}
                    }}

                    // Ưu tiên 2: tìm div có chứa comment, kể cả không có overflow CSS
                    const container = document.querySelector('[data-e2e*="comment-container"], [data-e2e*="comment-list"]');
                    if (container) {{
                        container.scrollBy(0, {distance});
                        container.scrollTop += {distance};
                        return 'generic-container';
                    }}

                    return null;
                }})()
            """)

            if not scrolled:
                # Fallback: hover vào bình luận cuối cùng và dùng mouse wheel
                try:
                    comment_elements = await page.query_selector_all(
                        '[data-e2e="comment-level-1"]'
                    )
                    target = comment_elements[-1] if comment_elements else None
                    if not target:
                        target = await page.query_selector('[data-e2e="search-comment-container"]')
                    if target:
                        box = await target.bounding_box()
                        if box:
                            cx = box["x"] + box["width"] / 2
                            cy = box["y"] + box["height"] / 2
                            await page.mouse.move(cx, cy)
                            # Wheel nhiều lần nhỏ hiệu quả hơn một lần lớn
                            for _ in range(5):
                                await page.mouse.wheel(0, distance // 5)
                                await asyncio.sleep(0.1)
                except Exception:
                    pass

            await self._wait_random()

    # -----------------------------------------------------------------------
    # Khởi tạo trình duyệt
    # -----------------------------------------------------------------------

    async def _create_browser_context(self, playwright) -> BrowserContext:
        """
        Khởi động Chromium và tạo context giả lập người dùng thật:
        - Ẩn cờ `navigator.webdriver`
        - Dùng User-Agent ngẫu nhiên
        - Locale và múi giờ Việt Nam
        """
        browser = await playwright.chromium.launch(
            headless=self.headless,
            args=["--disable-blink-features=AutomationControlled"],
        )
        context = await browser.new_context(
            user_agent=random.choice(USER_AGENTS),
            viewport={"width": 1280, "height": 800},
            locale="vi-VN",
            timezone_id="Asia/Ho_Chi_Minh",
        )
        await context.add_init_script(
            "Object.defineProperty(navigator, 'webdriver', { get: () => undefined })"
        )
        return context

    # -----------------------------------------------------------------------
    # Lấy danh sách URL video từ trang tìm kiếm từ khóa
    # -----------------------------------------------------------------------

    async def _fetch_video_urls(self, page: Page, keyword: str) -> list[str]:
        """
        Mở trang tìm kiếm TikTok theo từ khóa và thu thập đúng `max_videos` URL video.

        Tự động scroll thêm cho đến khi đủ số lượng yêu cầu hoặc không còn video mới.
        Trả về danh sách URL đầy đủ (bắt đầu bằng https://...).
        """
        from urllib.parse import quote
        encoded = quote(keyword)
        url = f"https://www.tiktok.com/search/video?q={encoded}"
        print(f"  [keyword] Mở {url}")

        await page.goto(url, wait_until="domcontentloaded", timeout=60_000)
        await self._wait_for_page(page)
        await self._wait_random()

        urls: list[str] = []
        seen: set[str] = set()
        max_scroll_attempts = 20   # Giới hạn số lần scroll để tránh vòng lặp vô tận
        no_new_count = 0           # Số lần scroll liên tiếp không tìm được video mới
        MAX_NO_NEW = 4             # Dừng nếu scroll 4 lần liên tiếp không ra video mới

        for attempt in range(max_scroll_attempts):
            # Thu thập tất cả anchor hiện có trên trang
            anchors = await page.query_selector_all('a[href*="/video/"]')
            prev_count = len(urls)

            for anchor in anchors:
                if len(urls) >= self.max_videos:
                    break
                href = await anchor.get_attribute("href")
                if not href or "/video/" not in href or href in seen:
                    continue
                seen.add(href)
                full_url = href if href.startswith("http") else f"https://www.tiktok.com{href}"
                urls.append(full_url)

            print(f"  [keyword] Lần scroll {attempt + 1}: {len(urls)}/{self.max_videos} video")

            # Đủ số lượng → dừng
            if len(urls) >= self.max_videos:
                break

            # Không có video mới sau lần scroll này
            if len(urls) == prev_count:
                no_new_count += 1
                if no_new_count >= MAX_NO_NEW:
                    print(f"  [keyword] Không tìm thêm được video mới sau {MAX_NO_NEW} lần scroll → dừng")
                    break
            else:
                no_new_count = 0  # Reset khi tìm được video mới

            # Scroll xuống để load thêm video
            await self._scroll_down(page, times=2, distance=3000)
            await self._wait_for_page(page)
        print(f"  [keyword] Tổng cộng tìm được {len(urls)} video")
        return urls

    async def _extract_unique_urls(self, anchors) -> list[str]:
        """Lọc và chuẩn hóa các href thành URL video không trùng lặp."""
        urls: list[str] = []
        seen: set[str] = set()

        for anchor in anchors:
            href = await anchor.get_attribute("href")
            if not href or "/video/" not in href or href in seen:
                continue
            seen.add(href)
            full_url = href if href.startswith("http") else f"https://www.tiktok.com{href}"
            urls.append(full_url)
            if len(urls) >= self.max_videos:
                break

        print(f"  [keyword] Tìm được {len(urls)} video")
        return urls

    # -----------------------------------------------------------------------
    # Thu thập bình luận từ một video
    # -----------------------------------------------------------------------

    async def _scrape_video_comments(
        self, page: Page, video_url: str, topic: str, keyword: str
    ) -> list[Comment]:
        """
        Mở một video TikTok, mở tab Bình luận, cuộn và thu thập bình luận.

        Trả về danh sách `Comment` (có thể rỗng nếu lỗi hoặc không có bình luận).
        """
        print(f"    [video] {video_url}")

        if not await self._navigate_to_video(page, video_url):
            return []

        video_id = self._extract_video_id(video_url)
        await self._open_comment_tab(page)

        comments: list[Comment] = []
        seen_comments: set[str] = set()
        max_scroll_attempts = 20
        no_new_streak = 0       # Số lần scroll liên tiếp không ra comment mới
        MAX_NO_NEW = 3
        prev_element_count = 0  # Theo dõi số element DOM để phát hiện scroll có hiệu quả không

        for _ in range(max_scroll_attempts):
            comment_elements = await self._find_comment_elements(page)
            current_element_count = len(comment_elements)

            current_comments = await self._parse_comments(
                comment_elements, video_id, video_url, topic, keyword
            )

            new_comments = []
            for comment in current_comments:
                comment_key = comment.text.strip()
                if comment_key in seen_comments:
                    continue
                seen_comments.add(comment_key)
                new_comments.append(comment)

            comments.extend(new_comments)

            if len(comments) >= self.max_comments:
                comments = comments[: self.max_comments]
                break

            # Dừng khi DOM không tăng thêm element sau nhiều lần scroll
            if current_element_count <= prev_element_count:
                no_new_streak += 1
                if no_new_streak >= MAX_NO_NEW:
                    break
            else:
                no_new_streak = 0

            prev_element_count = current_element_count

            await self._scroll_comment_container(page, times=1, distance=2000)
            await self._wait_for_page(page)
            await self._wait_random()

        print(f"    [video] Thu được {len(comments)} bình luận")
        return comments

    async def _navigate_to_video(self, page: Page, video_url: str) -> bool:
        """Điều hướng đến video. Trả về False nếu tải trang thất bại."""
        try:
            await page.goto(video_url, wait_until="domcontentloaded", timeout=60_000)
            await self._wait_for_page(page)
            await self._wait_random()
            return True
        except Exception as e:
            print(f"    [video] Lỗi tải trang: {e}")
            return False

    def _extract_video_id(self, video_url: str) -> str:
        """Trích video ID từ URL. Trả về 'unknown' nếu không tìm thấy."""
        match = VIDEO_URL_PATTERN.search(video_url)
        return match.group(1) if match else "unknown"

    async def _open_comment_tab(self, page: Page) -> bool:
        """
        Tìm và bấm vào tab/nút Bình luận.

        TikTok đôi khi hiển thị tab gợi ý mặc định; cần chuyển sang Bình luận.
        Trả về True nếu bấm thành công.
        """
        candidates = [
            page.get_by_role("tab", name=COMMENT_TAB_PATTERN),
            page.get_by_text(COMMENT_TAB_PATTERN),
        ]
        for candidate in candidates:
            try:
                if await candidate.count() > 0:
                    await candidate.first.click(timeout=5_000)
                    await page.wait_for_timeout(2_000)
                    return True
            except Exception:
                continue

        print("    [video] Không tìm thấy tab Bình luận")
        return False

    async def _find_comment_elements(self, page: Page) -> list:
        """
        Thử lần lượt các CSS selector để tìm phần tử bình luận.

        TikTok thường xuyên thay đổi class name nên cần nhiều fallback.
        """
        for selector in COMMENT_SELECTORS:
            elements = await page.query_selector_all(selector)
            if elements:
                return elements
        return []

    async def _parse_comments(
        self,
        elements: list,
        video_id: str,
        video_url: str,
        topic: str,
        keyword: str,
    ) -> list[Comment]:
        """Chuyển đổi danh sách phần tử DOM thành danh sách `Comment`."""
        comments: list[Comment] = []
        scraped_at = datetime.now().isoformat()

        for element in elements[: self.max_comments]:
            comment = await self._parse_single_comment(
                element, video_id, video_url, topic, keyword, scraped_at, len(comments)
            )
            if comment:
                comments.append(comment)

        return comments

    async def _parse_single_comment(
        self,
        element,
        video_id: str,
        video_url: str,
        topic: str,
        keyword: str,
        scraped_at: str,
        index: int,
    ) -> Optional[Comment]:
        """
        Đọc text, tác giả và lượt thích từ một phần tử bình luận.

        Trả về None nếu text quá ngắn hoặc xảy ra lỗi.
        """
        try:
            text = (await element.inner_text()).strip()
            if not text or len(text) < 3:
                return None

            author, likes = await self._extract_author_and_likes(element)

            return Comment(
                comment_id=f"{video_id}_{index}",
                text=text,
                author=author,
                likes=likes,
                topic=topic,
                keyword=keyword,
                video_url=video_url,
                video_id=video_id,
                scraped_at=scraped_at,
            )
        except Exception:
            return None

    async def _extract_author_and_likes(self, element) -> tuple[str, int]:
        """
        Lấy tên tác giả và số lượt thích từ container bình luận.

        Trả về ('unknown', 0) nếu không tìm thấy.
        """
        author = "unknown"
        likes  = 0

        try:
            container = await element.evaluate_handle(
                "el => el.closest('[data-e2e=\"comment-item\"]') || el.parentElement"
            )
            author_el = await container.query_selector('[data-e2e="comment-username-1"]')
            if author_el:
                author = (await author_el.inner_text()).strip()

            like_el = await container.query_selector('[data-e2e="comment-like-count"]')
            if like_el:
                raw_like = (await like_el.inner_text()).strip()
                likes = _parse_like_count(raw_like)
        except Exception:
            pass

        return author, likes

    # -----------------------------------------------------------------------
    # Lưu kết quả vào file CSV
    # -----------------------------------------------------------------------

    def _save_comments(self, comments: list[Comment], topic: str):
        output_file = self.output_dir / "comments.csv"
        existing_pairs = self._load_existing_keys(output_file)

        new_comments = [
            c for c in comments
            if (c.text.strip(), c.topic, c.keyword, c.video_url) not in existing_pairs
        ]

        if not new_comments:
            print(f"  [save] Không có bình luận mới → {output_file}")
            return

        file_exists = output_file.exists()
        with output_file.open("a", encoding="utf-8-sig", newline="") as f:
            writer = csv.writer(f, quoting=csv.QUOTE_ALL)
            if not file_exists:
                writer.writerow(["text", "topic", "keyword", "post_url"])
            for c in new_comments:
                writer.writerow([c.text.strip(), c.topic, c.keyword, c.video_url])

        print(f"  [save] Đã ghi {len(new_comments)} bình luận → {output_file}")
        save_to_hdfs(new_comments)


    def _load_existing_keys(self, file_path: Path) -> set[tuple[str, str, str, str]]:
        existing: set[tuple[str, str, str, str]] = set()
        if not file_path.exists():
            return existing
        try:
            with file_path.open("r", encoding="utf-8-sig", newline="") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    existing.add((
                        row.get("text", "").strip(),
                        row.get("topic", ""),
                        row.get("keyword", ""),
                        row.get("post_url", ""),
                    ))
        except Exception:
            pass
        return existing
    # -----------------------------------------------------------------------
    # Điểm vào (entry points)
    # -----------------------------------------------------------------------

    async def scrape_topic(self, topic: str, keywords: list[str]) -> list[Comment]:
        """
        Crawl toàn bộ từ khóa trong một chủ đề và lưu kết quả.

        Trả về danh sách tất cả bình luận thu thập được.
        """
        all_comments: list[Comment] = []

        async with async_playwright() as playwright:
            context = await self._create_browser_context(playwright)
            page = await context.new_page()

            for keyword in keywords:
                print(f"\n[topic={topic}] keyword={keyword}")
                comments = await self._scrape_keyword(page, keyword, topic)
                all_comments.extend(comments)

            await context.close()

        self._save_comments(all_comments, topic)
        return all_comments

    async def _scrape_keyword(
        self, page: Page, keyword: str, topic: str
    ) -> list[Comment]:
        """
        Crawl đủ max_videos video thuộc một từ khóa tìm kiếm.

        _fetch_video_urls đã tự scroll cho đến khi đủ số lượng;
        hàm này chỉ cần duyệt qua danh sách trả về và crawl bình luận.
        Bỏ qua keyword nếu có lỗi nghiêm trọng.
        """
        try:
            video_urls = await self._fetch_video_urls(page, keyword)

            if len(video_urls) < self.max_videos:
                print(
                    f"  [warn] Chỉ tìm được {len(video_urls)}/{self.max_videos} video "
                    f"cho keyword '{keyword}' — tiếp tục với số hiện có"
                )

            comments: list[Comment] = []
            for idx, url in enumerate(video_urls, start=1):
                print(f"  [scrape] Video {idx}/{len(video_urls)}: {url}")
                video_comments = await self._scrape_video_comments(page, url, topic, keyword)
                comments.extend(video_comments)
                await self._wait_random()

            print(
                f"  [keyword] '{keyword}' hoàn tất — "
                f"{len(video_urls)} video, {len(comments)} bình luận"
            )
            return comments
        except Exception as e:
            print(f"  [error] Lỗi khi crawl '{keyword}': {e}")
            return []

    async def scrape_all_topics(self, topics: dict[str, list[str]] = None):
        """
        Crawl tất cả chủ đề và in tổng số bình luận thu thập được.

        Nếu không truyền `topics`, dùng danh sách mặc định `TOPICS`.
        """
        # Đợi 30 giây trước khi bắt đầu (yêu cầu: "trước khi bắt đầu thì chờ 30 s")
        # print("\n[init] Chờ 30 giây trước khi bắt đầu crawl...")
        # await asyncio.sleep(30)

        if topics is None:
            topics = TOPICS

        total = 0
        for topic, keywords in topics.items():
            comments = await self.scrape_topic(topic, keywords)
            total += len(comments)

        print(f"\n[DONE] Tổng số bình luận: {total}")


# ===========================================================================
# Hàm tiện ích độc lập
# ===========================================================================

def _parse_like_count(raw: str) -> int:
    """
    Chuyển chuỗi lượt thích (ví dụ: '1.2K', '3M', '500') thành số nguyên.

    Ví dụ:
        '1.2K' → 1200
        '3M'   → 3000000
        '500'  → 500
    """
    normalized = raw.strip().upper()
    try:
        if "K" in normalized:
            return int(float(normalized.replace("K", "")) * 1_000)
        if "M" in normalized:
            return int(float(normalized.replace("M", "")) * 1_000_000)
        return int(normalized.replace(",", ""))
    except ValueError:
        return 0


if __name__ == "__main__":
    scraper = TikTokScraper(
        output_dir="data/raw",
        max_videos=20,      
        max_comments=10000,
        headless=False,      
    )
    asyncio.run(scraper.scrape_all_topics())