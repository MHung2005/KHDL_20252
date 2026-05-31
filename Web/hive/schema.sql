-- =============================================================
-- HIVE DDL: Hate Speech Detection System
-- Database: hate_speech_db
-- =============================================================

CREATE DATABASE IF NOT EXISTS hate_speech_db
COMMENT 'Hate Speech Detection - Data & Model Management'
LOCATION '/user/hive/warehouse/hate_speech_db.db';

USE hate_speech_db;

-- =============================================================
-- TABLE 1: raw_crawled_data
-- Lưu trữ dữ liệu thô được crawl từ các nền tảng
-- HDFS path: /data/raw/{platform}/
-- =============================================================
CREATE EXTERNAL TABLE IF NOT EXISTS raw_crawled_data (
    id              STRING      COMMENT 'UUID duy nhất cho mỗi bản ghi',
    platform        STRING      COMMENT 'Nền tảng: tiktok | threads | facebook',
    post_id         STRING      COMMENT 'ID bài viết gốc trên nền tảng',
    content         STRING      COMMENT 'Nội dung văn bản gốc',
    author_id       STRING      COMMENT 'ID tác giả (đã ẩn danh)',
    likes_count     BIGINT      COMMENT 'Số lượt thích',
    comments_count  BIGINT      COMMENT 'Số bình luận',
    shares_count    BIGINT      COMMENT 'Số chia sẻ',
    crawled_at      TIMESTAMP   COMMENT 'Thời điểm crawl',
    language        STRING      COMMENT 'Ngôn ngữ phát hiện: vi | en | other',
    char_count      INT         COMMENT 'Độ dài văn bản (ký tự)',
    hdfs_path       STRING      COMMENT 'Đường dẫn file gốc trên HDFS'
)
COMMENT 'Dữ liệu thô được crawl từ TikTok, Threads, Facebook'
PARTITIONED BY (
    crawl_date      STRING      COMMENT 'Ngày crawl định dạng yyyy-MM-dd',
    source_platform STRING      COMMENT 'Partition theo nền tảng'
)
STORED AS PARQUET
LOCATION '/user/hive/warehouse/hate_speech_db.db/raw_crawled_data'
TBLPROPERTIES (
    'parquet.compression'='SNAPPY',
    'creator'='hate_speech_pipeline'
);

-- =============================================================
-- TABLE 2: processed_data
-- Dữ liệu sau khi tiền xử lý (làm sạch, tokenize, v.v.)
-- =============================================================
CREATE EXTERNAL TABLE IF NOT EXISTS processed_data (
    id                  STRING      COMMENT 'UUID - khớp với raw_crawled_data.id',
    raw_id              STRING      COMMENT 'FK -> raw_crawled_data.id',
    platform            STRING      COMMENT 'Nền tảng nguồn',
    original_content    STRING      COMMENT 'Nội dung gốc',
    cleaned_content     STRING      COMMENT 'Nội dung sau làm sạch',
    normalized_content  STRING      COMMENT 'Nội dung chuẩn hoá (lowercase, remove punct)',
    tokens              ARRAY<STRING> COMMENT 'Danh sách token sau phân tách',
    token_count         INT         COMMENT 'Số lượng token',
    label               INT         COMMENT 'Nhãn: 0=normal, 1=hate_speech, 2=offensive',
    label_name          STRING      COMMENT 'Tên nhãn: normal | hate_speech | offensive',
    labeled_by          STRING      COMMENT 'Nguồn gán nhãn: human | model | rule',
    split_set           STRING      COMMENT 'Tập dữ liệu: train | test | validation',
    labeled_at          TIMESTAMP   COMMENT 'Thời điểm gán nhãn',
    processed_at        TIMESTAMP   COMMENT 'Thời điểm xử lý',
    hdfs_path           STRING      COMMENT 'Đường dẫn file đã xử lý trên HDFS'
)
COMMENT 'Dữ liệu đã tiền xử lý và gán nhãn'
PARTITIONED BY (
    split_set_part  STRING  COMMENT 'train | test | validation',
    platform_part   STRING  COMMENT 'tiktok | threads | facebook'
)
STORED AS PARQUET
LOCATION '/user/hive/warehouse/hate_speech_db.db/processed_data'
TBLPROPERTIES ('parquet.compression'='SNAPPY');

-- =============================================================
-- TABLE 3: model_registry
-- Thông tin các mô hình đã huấn luyện
-- =============================================================
CREATE TABLE IF NOT EXISTS model_registry (
    model_id            STRING      COMMENT 'UUID mô hình',
    model_name          STRING      COMMENT 'Tên mô hình: tfidf_svm | tfidf_lr | phobert',
    model_display_name  STRING      COMMENT 'Tên hiển thị: TF-IDF + SVM, v.v.',
    model_type          STRING      COMMENT 'Loại: traditional | deep_learning',
    version             STRING      COMMENT 'Phiên bản: v1.0, v1.1, v.v.',
    description         STRING      COMMENT 'Mô tả ngắn về mô hình',
    hyperparameters     STRING      COMMENT 'JSON string chứa siêu tham số',
    train_dataset_id    STRING      COMMENT 'ID tập train đã dùng',
    test_dataset_id     STRING      COMMENT 'ID tập test đã dùng',
    train_samples       BIGINT      COMMENT 'Số lượng mẫu train',
    test_samples        BIGINT      COMMENT 'Số lượng mẫu test',
    train_duration_sec  DOUBLE      COMMENT 'Thời gian huấn luyện (giây)',
    model_hdfs_path     STRING      COMMENT 'Đường dẫn lưu mô hình trên HDFS',
    created_at          TIMESTAMP   COMMENT 'Thời điểm tạo',
    is_active           BOOLEAN     COMMENT 'Mô hình đang được sử dụng'
)
COMMENT 'Registry các mô hình đã huấn luyện'
STORED AS ORC
LOCATION '/user/hive/warehouse/hate_speech_db.db/model_registry'
TBLPROPERTIES ('orc.compress'='ZLIB');

-- =============================================================
-- TABLE 4: model_evaluation_results
-- Kết quả đánh giá chi tiết từng mô hình
-- =============================================================
CREATE TABLE IF NOT EXISTS model_evaluation_results (
    eval_id             STRING      COMMENT 'UUID kết quả đánh giá',
    model_id            STRING      COMMENT 'FK -> model_registry.model_id',
    model_name          STRING      COMMENT 'Tên mô hình (denormalized để query nhanh)',
    evaluated_at        TIMESTAMP   COMMENT 'Thời điểm đánh giá',
    -- Overall Metrics
    accuracy            DOUBLE      COMMENT 'Độ chính xác tổng thể',
    macro_precision     DOUBLE      COMMENT 'Macro-avg Precision',
    macro_recall        DOUBLE      COMMENT 'Macro-avg Recall',
    macro_f1            DOUBLE      COMMENT 'Macro-avg F1-Score',
    weighted_precision  DOUBLE      COMMENT 'Weighted-avg Precision',
    weighted_recall     DOUBLE      COMMENT 'Weighted-avg Recall',
    weighted_f1         DOUBLE      COMMENT 'Weighted-avg F1-Score',
    -- Per-class Metrics: Normal (0)
    normal_precision    DOUBLE      COMMENT 'Precision lớp Normal',
    normal_recall       DOUBLE      COMMENT 'Recall lớp Normal',
    normal_f1           DOUBLE      COMMENT 'F1 lớp Normal',
    normal_support      BIGINT      COMMENT 'Số mẫu lớp Normal trong test',
    -- Per-class Metrics: Hate Speech (1)
    hate_precision      DOUBLE      COMMENT 'Precision lớp Hate Speech',
    hate_recall         DOUBLE      COMMENT 'Recall lớp Hate Speech',
    hate_f1             DOUBLE      COMMENT 'F1 lớp Hate Speech',
    hate_support        BIGINT      COMMENT 'Số mẫu lớp Hate Speech trong test',
    -- Per-class Metrics: Offensive (2)
    offensive_precision DOUBLE      COMMENT 'Precision lớp Offensive',
    offensive_recall    DOUBLE      COMMENT 'Recall lớp Offensive',
    offensive_f1        DOUBLE      COMMENT 'F1 lớp Offensive',
    offensive_support   BIGINT      COMMENT 'Số mẫu lớp Offensive trong test',
    -- Confusion Matrix (JSON string)
    confusion_matrix    STRING      COMMENT 'JSON: [[TP,FP],[FN,TN]] dạng ma trận NxN',
    -- Dataset Split Info
    train_ratio         DOUBLE      COMMENT 'Tỉ lệ train (ví dụ: 0.8)',
    test_ratio          DOUBLE      COMMENT 'Tỉ lệ test (ví dụ: 0.2)',
    total_samples       BIGINT      COMMENT 'Tổng số mẫu',
    notes               STRING      COMMENT 'Ghi chú thêm'
)
COMMENT 'Kết quả đánh giá các mô hình Hate Speech Detection'
STORED AS ORC
LOCATION '/user/hive/warehouse/hate_speech_db.db/model_evaluation_results'
TBLPROPERTIES ('orc.compress'='ZLIB');

-- =============================================================
-- TABLE 5: crawl_sessions
-- Quản lý các phiên crawl dữ liệu
-- =============================================================
CREATE TABLE IF NOT EXISTS crawl_sessions (
    session_id          STRING      COMMENT 'UUID phiên crawl',
    platform            STRING      COMMENT 'Nền tảng: tiktok | threads | facebook',
    status              STRING      COMMENT 'Trạng thái: running | completed | failed',
    started_at          TIMESTAMP   COMMENT 'Thời điểm bắt đầu',
    completed_at        TIMESTAMP   COMMENT 'Thời điểm hoàn thành',
    records_crawled     BIGINT      COMMENT 'Số bản ghi đã crawl',
    records_failed      BIGINT      COMMENT 'Số bản ghi lỗi',
    keywords            STRING      COMMENT 'Từ khoá crawl (JSON array)',
    hdfs_output_path    STRING      COMMENT 'Thư mục output trên HDFS',
    error_log           STRING      COMMENT 'Log lỗi nếu có'
)
COMMENT 'Lịch sử các phiên crawl dữ liệu'
STORED AS ORC
LOCATION '/user/hive/warehouse/hate_speech_db.db/crawl_sessions'
TBLPROPERTIES ('orc.compress'='ZLIB');

-- =============================================================
-- VIEWS: Tiện lợi cho API queries
-- =============================================================

-- View: Thống kê tổng quan dữ liệu theo nền tảng
CREATE OR REPLACE VIEW v_platform_stats AS
SELECT
    platform,
    COUNT(*)                                    AS total_records,
    COUNT(CASE WHEN language = 'vi' THEN 1 END) AS vietnamese_records,
    MIN(crawled_at)                             AS first_crawled,
    MAX(crawled_at)                             AS last_crawled,
    AVG(char_count)                             AS avg_char_count
FROM raw_crawled_data
GROUP BY platform;

-- View: Thống kê tập train/test theo nhãn
CREATE OR REPLACE VIEW v_dataset_split_stats AS
SELECT
    split_set,
    platform,
    label_name,
    COUNT(*)        AS record_count,
    AVG(token_count) AS avg_token_count
FROM processed_data
GROUP BY split_set, platform, label_name;

-- View: So sánh hiệu năng các mô hình (lấy kết quả mới nhất)
CREATE OR REPLACE VIEW v_model_comparison AS
SELECT
    mer.model_id,
    mr.model_display_name,
    mr.model_type,
    mr.version,
    mer.accuracy,
    mer.macro_f1,
    mer.weighted_f1,
    mer.macro_precision,
    mer.macro_recall,
    mer.hate_f1         AS target_hate_f1,
    mer.offensive_f1    AS target_offensive_f1,
    mer.normal_f1       AS target_normal_f1,
    mer.confusion_matrix,
    mer.train_ratio,
    mer.test_ratio,
    mer.total_samples,
    mer.evaluated_at
FROM model_evaluation_results mer
JOIN model_registry mr ON mer.model_id = mr.model_id
WHERE mr.is_active = TRUE;

-- =============================================================
-- SAMPLE DATA: Seed data cho demo
-- =============================================================

-- Insert model registry
INSERT INTO model_registry VALUES
(
    'model-001', 'tfidf_svm', 'TF-IDF + SVM', 'traditional', 'v1.0',
    'TF-IDF vectorizer với SVM kernel RBF, C=1.0',
    '{"vectorizer":"tfidf","max_features":50000,"ngram_range":[1,2],"kernel":"rbf","C":1.0}',
    'ds-train-001', 'ds-test-001', 8000, 2000, 120.5,
    '/models/tfidf_svm_v1.pkl', CURRENT_TIMESTAMP, TRUE
),
(
    'model-002', 'tfidf_lr', 'TF-IDF + Logistic Regression', 'traditional', 'v1.0',
    'TF-IDF vectorizer với Logistic Regression, C=1.0, solver=lbfgs',
    '{"vectorizer":"tfidf","max_features":50000,"ngram_range":[1,2],"C":1.0,"solver":"lbfgs","max_iter":1000}',
    'ds-train-001', 'ds-test-001', 8000, 2000, 45.2,
    '/models/tfidf_lr_v1.pkl', CURRENT_TIMESTAMP, TRUE
),
(
    'model-003', 'phobert', 'PhoBERT + Classification Head', 'deep_learning', 'v1.0',
    'PhoBERT-base-v2 fine-tuned với classification head 3 lớp',
    '{"base_model":"vinai/phobert-base-v2","max_length":256,"learning_rate":2e-5,"epochs":5,"batch_size":32}',
    'ds-train-001', 'ds-test-001', 8000, 2000, 7200.0,
    '/models/phobert_v1/', CURRENT_TIMESTAMP, TRUE
);

-- Insert evaluation results
INSERT INTO model_evaluation_results VALUES
(
    'eval-001', 'model-001', 'tfidf_svm', CURRENT_TIMESTAMP,
    0.7823, 0.7615, 0.7702, 0.7798, 0.7750, 0.7823,
    0.7823, 0.7918,
    0.8234, 0.8012, 0.8122, 1520,
    0.7102, 0.7345, 0.7221, 312,
    0.6890, 0.6723, 0.6805, 168,
    '[[1254,178,88],[52,228,32],[28,24,116]]',
    0.80, 0.20, 10000, 'Baseline model'
),
(
    'eval-002', 'model-002', 'tfidf_lr', CURRENT_TIMESTAMP,
    0.8015, 0.7832, 0.7910, 0.8034, 0.7978, 0.8015,
    0.8015, 0.8312,
    0.8456, 0.8234, 0.8344, 1520,
    0.7234, 0.7512, 0.7370, 312,
    0.7012, 0.6934, 0.6973, 168,
    '[[1252,180,88],[45,234,33],[22,30,116]]',
    0.80, 0.20, 10000, 'Improved baseline'
),
(
    'eval-003', 'model-003', 'phobert', CURRENT_TIMESTAMP,
    0.8934, 0.8823, 0.8876, 0.8945, 0.8890, 0.8934,
    0.8934, 0.9123,
    0.9234, 0.9012, 0.9122, 1520,
    0.8623, 0.8845, 0.8732, 312,
    0.8612, 0.8612, 0.8612, 168,
    '[[1370,98,52],[22,276,14],[12,14,142]]',
    0.80, 0.20, 10000, 'Fine-tuned PhoBERT'
);
