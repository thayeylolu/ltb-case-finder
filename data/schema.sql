-- MVP 0 SQLite schema for the LTB Case Discovery Tool.
-- Populated by the ingestion script (Task 5) from data/raw/*.csv into data/ltb.db.
-- Holds only the fields required to serve POST /search per plan.md section 7 —
-- no landlord/tenant/co-op member names or addresses are carried over from the
-- raw catalogue, even though the source CSV includes them.

DROP TABLE IF EXISTS order_issue_codes;
DROP TABLE IF EXISTS orders;

CREATE TABLE orders (
    -- Surrogate key. The raw catalogue is one row per document, and the same
    -- file_number recurs across multiple documents (e.g. an initial Order,
    -- an ExParte Order, and a later Review Order for one case), so
    -- file_number alone cannot be the primary key.
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    -- "File Number" (raw column "File Number/Numéro de dossier"). Identifies
    -- the LTB case and is shown to the user as-is (plan.md section 3, Step 3).
    file_number TEXT NOT NULL,

    -- "Order Date" (raw column "Order Date/Date de l'ordonnance"), stored as
    -- ISO 8601 (YYYY-MM-DD) so it sorts correctly as text. Drives the
    -- most-recent-first ranking in plan.md section 4 and is shown to the user.
    order_date TEXT NOT NULL,

    -- LTB application/issue codes for this order (raw column
    -- "Applications/Requêtes"), e.g. "T1;T2;T3". Kept as-is here for display;
    -- Task 6 additionally explodes this into the order_issue_codes table
    -- below so filtering by code doesn't require a LIKE '%T1%' scan (which
    -- would also wrongly match "T10", "T11", ...).
    issue_codes TEXT NOT NULL,

    -- "Document Type" (raw column "Document Type/Type de document"), e.g.
    -- Order, ExParte Order, Review Order. Shown in the results table so the
    -- user knows what kind of document they're viewing (plan.md section 9).
    document_type TEXT NOT NULL,

    -- City the rental unit/complex is located in, derived from `address`
    -- below during ingestion (the catalogue has no dedicated city column).
    -- Required for the results table (plan.md section 9).
    city TEXT,

    -- Whether `address` below came from the raw "Rental Unit Address" or
    -- "Complex Address" column (Task 5 rework): "Rental Unit" when a rental
    -- unit address is present and no complex address is given, "Complex"
    -- when a complex address is given (taking priority when both are
    -- present), or "" when neither raw column had a value.
    resident_type TEXT NOT NULL DEFAULT '',

    -- The merged, single address value described above — the raw catalogue
    -- has two separately-named "Rental Unit Address" columns (only one of
    -- which is ever populated per row) plus a "Complex Address" column, and
    -- this is whichever of those actually had a value. "" when none did.
    address TEXT NOT NULL DEFAULT '',

    -- Link to the original order document (raw column "ContentDownload
    -- URL/URL de téléchargement du contenu", renamed "View Order" per Task 5).
    -- The app never fetches/stores the PDF itself — only this link
    -- (plan.md section 5, "Order Documents").
    view_order_url TEXT NOT NULL
);

-- Search ranking always sorts by most recent order_date (plan.md section 4).
CREATE INDEX idx_orders_order_date ON orders (order_date);

-- Lets a user's file-number lookup (or future case-level grouping across an
-- order's Order/ExParte Order/Review Order rows) avoid a full table scan.
CREATE INDEX idx_orders_file_number ON orders (file_number);

-- Task 6: normalized issue codes, one row per (order, code) pair, e.g. the
-- orders.issue_codes value "T1;T2;T3" becomes three rows here. This is what
-- Task 9's ALL-match / ANY-match filtering queries against.
CREATE TABLE order_issue_codes (
    order_id INTEGER NOT NULL REFERENCES orders (id),
    code TEXT NOT NULL
);

-- Task 9 filters by code (WHERE code IN (...)), so this is the index that
-- matters for search performance.
CREATE INDEX idx_order_issue_codes_code ON order_issue_codes (code);

-- Lets a lookup go the other way — from an order back to all of its codes —
-- without a full table scan.
CREATE INDEX idx_order_issue_codes_order_id ON order_issue_codes (order_id);
