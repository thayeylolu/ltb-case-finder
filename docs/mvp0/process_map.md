# MVP 0 Process Map

Task 18. Where `docs/mvp0/architecture.md` describes the system at the
component level (and at the design stage, before some of it was built),
this doc traces actual, current function calls — file by file — so you
can answer "what code runs when X happens?" without reading every file
yourself. Keep this in sync with the code as it changes; if a function
here gets renamed, moved, or removed, update the diagram in the same
commit.

Two flows are covered: the offline data pipeline (run manually, never
during a request) and a tenant's search (everything that happens between
clicking **Search** and seeing a table or a "no results" message).

---

## 1. Data Pipeline: raw CSV → `data/ltb.db`

Entry point: `.venv/Scripts/python.exe scripts/ingest_catalogue.py`. Every
box below is a function in `scripts/ingest_catalogue.py` unless labeled
otherwise.

```mermaid
flowchart TD
    Start(["main()"]) --> FindCSV["_find_default_csv(RAW_DATA_DIR)<br/>(only if --csv wasn't passed)"]
    FindCSV --> LoadCat["load_catalogue(csv_path, db_path)"]

    LoadCat --> ReadRows["_read_rows(csv_path)"]
    ReadRows --> CleanHeader["clean_header(raw_header)<br/>for every column —<br/>strip bilingual '/French' suffix,<br/>rename 'ContentDownload URL' → 'View Order'"]
    CleanHeader --> Dedupe["_dedupe_header(cleaned_header)<br/>disambiguates the two same-named<br/>'Rental Unit Address' columns"]
    Dedupe --> DictReader["csv.DictReader yields one dict per row"]

    DictReader --> ForEachRow{"For each row..."}
    ForEachRow --> ReqCheck{"File Number, Applications,<br/>Document Type, Order Date,<br/>View Order all present?"}
    ReqCheck -- "No" --> Skip["skipped += 1<br/>logger.warning(...)"]
    Skip --> ForEachRow

    ReqCheck -- "Yes" --> ExtractURL["extract_view_order_url(view_order_raw)<br/>pulls URL out of the Excel<br/>=HYPERLINK(...) formula"]
    ExtractURL --> Merge["merge_rental_unit_address(<br/>row['Rental Unit Address 2'],<br/>row['Rental Unit Address'])<br/>→ rental_unit_address"]
    Merge --> DeriveType["derive_resident_type_and_address(<br/>rental_unit_address, complex_address)<br/>→ (resident_type, address)"]
    DeriveType --> DeriveCity["derive_city(address)<br/>→ city, or None"]
    DeriveCity --> Collect["append (file_number, order_date, issue_codes,<br/>document_type, city, resident_type,<br/>address, view_order_url) to rows_to_insert"]
    Collect --> ForEachRow

    ForEachRow -- "no rows left" --> Schema["connection.executescript(data/schema.sql)<br/>DROPs and recreates orders +<br/>order_issue_codes (safe re-run)"]
    Schema --> ForEachInsert{"For each collected row..."}
    ForEachInsert --> InsertOrder["INSERT INTO orders (...)"]
    InsertOrder --> SplitCodes["split_issue_codes(issue_codes)<br/>'T1;T2;T3' → ['T1','T2','T3'],<br/>deduped, order preserved"]
    SplitCodes --> InsertCodes["INSERT INTO order_issue_codes<br/>(order_id, code) — one row per code"]
    InsertCodes --> ForEachInsert

    ForEachInsert -- "no rows left" --> Commit["connection.commit()<br/>logger.info('Loaded N records...')"]
    Commit --> End(["return len(rows_to_insert)"])
```

**Where things can go sideways:** a row missing any required field is
skipped, not inserted (`ReqCheck` above) — it's counted but never reaches
the DB. Everything else in a row is best-effort: `derive_city` returns
`None` rather than raising when it can't find a city segment, and
`derive_resident_type_and_address` returns `("", "")` rather than raising
when neither address column has anything.

---

## 2. A Tenant's Search, Start to Finish

Entry point: clicking **Search** (`#search-button` in `frontend/index.html`).

```mermaid
flowchart TD
    Click(["User clicks Search button<br/>(frontend/index.html #search-button)"]) --> Handle["handleSearchClick()<br/>(frontend/app.js)"]
    Handle --> GetIssues["getSelectedIssues()<br/>reads checked input[name=issues]"]
    GetIssues --> IssuesEmpty{"issues.length === 0?"}

    IssuesEmpty -- "Yes" --> Warn["console.warn(...); return<br/>— NO network call is made"]

    IssuesEmpty -- "No" --> SearchCases["searchCases(issues)<br/>fetch POST /search<br/>body: {issues}"]
    SearchCases --> Backend["FastAPI receives the request"]

    subgraph BE["Backend (backend/)"]
        Backend --> Validate{"Pydantic validates SearchRequest<br/>(issues: non-empty list of str)"}
        Validate -- "invalid, e.g. []" --> Http422["HTTP 422<br/>(FastAPI's own validation error,<br/>not app code)"]
        Validate -- "valid" --> Route["search()<br/>(backend/routes/search.py)"]

        Route --> GetCodes["get_codes_for_issues(request.issues)<br/>(backend/taxonomy.py)"]
        GetCodes --> KnownIssue{"every issue name recognized?"}
        KnownIssue -- "No" --> ValueErr["raises ValueError"]
        ValueErr --> Http400["caught in search() →<br/>HTTPException(400)"]

        KnownIssue -- "Yes" --> QueryAll["find_orders_matching_all_codes(<br/>connection, codes)<br/>(backend/queries.py)"]
        QueryAll --> QueryAny["find_orders_matching_any_code(<br/>connection, codes)<br/>(backend/queries.py)"]
        QueryAny --> Rank["rank_and_limit_results(<br/>all_match_results, any_match_results)<br/>(backend/ranking.py)"]

        Rank --> RankDetail["_sorted_by_recent_date on each set;<br/>ANY-match rows already in ALL-match<br/>are excluded; ALL-match sorted rows<br/>+ ANY-match sorted rows,<br/>sliced to MAX_RESULTS=20"]

        RankDetail --> ForEachRecord{"For each of the<br/>(≤20) ranked records..."}
        ForEachRecord --> SplitCodes2["split record['issue_codes']<br/>on ';'"]
        SplitCodes2 --> GetNames["get_issue_names_for_codes(codes)<br/>(backend/taxonomy.py)<br/>→ human-readable issues[]"]
        GetNames --> BuildResult["CaseResult(...)<br/>(backend/schemas.py):<br/>file_number, order_date, issues,<br/>forms=codes, city (Title Cased<br/>or None), resident_type,<br/>document_type, view_order_url"]
        BuildResult --> ForEachRecord

        ForEachRecord -- "no records left" --> Response["SearchResponse(results=[...])<br/>→ HTTP 200 JSON"]
    end

    Http422 --> FrontendCatch
    Http400 --> FrontendCatch["response.ok is false →<br/>searchCases() throws →<br/>caught in handleSearchClick() →<br/>console.error(error)<br/>(nothing rendered)"]

    Response --> Render["renderResults(data.results)<br/>(frontend/app.js)"]
    Render --> ResultsEmpty{"results.length === 0?"}
    ResultsEmpty -- "Yes" --> NoResults["append 'No matching orders found.'<br/>(#no-results-message) to #results"]
    ResultsEmpty -- "No" --> BuildTable["build a table with RESULT_COLUMNS headers<br/>(File Number, Order Date, Issues, Forms,<br/>City, Resident Type, Document Type,<br/>View Order) and one row per result"]
    BuildTable --> ViewOrderLink["View Order cell is an &lt;a&gt; to<br/>result.view_order_url,<br/>target=_blank rel=noopener"]
```

**The three branch points called out in Task 18, concretely:**

* **No issues selected** — caught client-side in `handleSearchClick()`
  (`IssuesEmpty`). No request ever reaches the backend.
* **An issue name `/search` doesn't recognize** — `get_codes_for_issues()`
  raises `ValueError`, which `search()` turns into an HTTP 400. The
  frontend's `fetch` sees `response.ok === false`, throws, and the error
  lands in `console.error` — nothing renders.
* **Zero matching cases** — `rank_and_limit_results()` returns `[]`,
  `SearchResponse.results` is `[]`, and `renderResults([])` shows the
  "No matching orders found." message (Task 15) instead of a table.
