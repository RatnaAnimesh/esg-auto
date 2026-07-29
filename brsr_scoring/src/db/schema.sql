-- SQLite Schema for BRSR Data Mapping & Scoring

CREATE TABLE IF NOT EXISTS Company_Master (
    cin TEXT PRIMARY KEY,
    name TEXT,
    date_of_incorporation TEXT,
    registered_office_address TEXT,
    corporate_office_address TEXT,
    email TEXT,
    telephone TEXT,
    website TEXT,
    financial_year_start TEXT,
    financial_year_end TEXT,
    stock_exchange TEXT,
    basic_industry TEXT,
    sector TEXT,
    business_activity TEXT
);

CREATE TABLE IF NOT EXISTS Question_Master (
    question_id TEXT PRIMARY KEY,
    question_text TEXT,
    data_type TEXT -- 'numeric', 'boolean', 'text'
);

-- Matrix A: Raw & Normalized Scores
CREATE TABLE IF NOT EXISTS Matrix_A (
    cin TEXT,
    question_id TEXT,
    raw_value TEXT,       -- original extracted text/value
    score REAL,           -- [0, 1] normalized or NLP-scored value
    PRIMARY KEY (cin, question_id),
    FOREIGN KEY (cin) REFERENCES Company_Master(cin),
    FOREIGN KEY (question_id) REFERENCES Question_Master(question_id)
);

-- Matrix B: Applicability
CREATE TABLE IF NOT EXISTS Matrix_B (
    cin TEXT,
    question_id TEXT,
    is_applicable INTEGER, -- 1 or 0
    PRIMARY KEY (cin, question_id),
    FOREIGN KEY (cin) REFERENCES Company_Master(cin),
    FOREIGN KEY (question_id) REFERENCES Question_Master(question_id)
);

-- Matrix C: Weights
CREATE TABLE IF NOT EXISTS Matrix_C (
    cin TEXT,
    question_id TEXT,
    weight REAL,          -- fractional weight
    PRIMARY KEY (cin, question_id),
    FOREIGN KEY (cin) REFERENCES Company_Master(cin),
    FOREIGN KEY (question_id) REFERENCES Question_Master(question_id)
);

-- Matrix P: Percentiles
CREATE TABLE IF NOT EXISTS Matrix_P (
    cin TEXT,
    question_id TEXT,
    percentile REAL,      -- [0, 1] percentile rank within sector
    PRIMARY KEY (cin, question_id),
    FOREIGN KEY (cin) REFERENCES Company_Master(cin),
    FOREIGN KEY (question_id) REFERENCES Question_Master(question_id)
);

-- Final Output
CREATE TABLE IF NOT EXISTS Final_Ratings (
    cin TEXT PRIMARY KEY,
    final_rating REAL,
    FOREIGN KEY (cin) REFERENCES Company_Master(cin)
);

-- Historical Scale: Baseline distribution of scores for FY 25-26 percentile evaluation
CREATE TABLE IF NOT EXISTS Historical_Scale (
    sector TEXT,
    question_id TEXT,
    historical_scores TEXT, -- JSON array of floats representing past distribution
    PRIMARY KEY (sector, question_id)
);
