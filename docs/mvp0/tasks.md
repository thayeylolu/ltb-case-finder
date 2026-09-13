# MVP 0 Task Backlog

Each task is scoped to be completable in a single session and self-contained enough to hand to someone who has not read the other tasks (assume they have read `docs/mvp0/plan.md`). Tasks are listed in a reasonable build order, but each description includes enough context to be understood on its own.

---

## 1. Project Setup with an Empty Passing Test
Goal: Establish a working Python project skeleton with a passing test so future tasks have a stable foundation.
Description: Initialize the project structure (e.g. `backend/`, `frontend/`, `data/`, `tests/` folders), set up a virtual environment, and add a dependency file (`requirements.txt` or `pyproject.toml`) including FastAPI and pytest. Add one trivial test that passes when running the test suite, confirming the test runner and project layout work end to end.


## 2. Acquire and Store a Local Snapshot of the LTB Order Catalogue
Goal: Obtain a local, versioned copy of the Ontario Open Data LTB Order Catalogue for development use.
Description: Download the current LTB Order Catalogue (CSV or JSON) from the Ontario Open Data portal and save it under `data/raw/`. Document the exact source URL, download date, and file format in a short README so the snapshot can be reproduced or refreshed later.

## 3. Define the Issue Taxonomy Mapping
Goal: Create the authoritative mapping between user-facing issue names and official LTB application codes.
Description: Produce a config file (e.g. JSON) listing the 9 MVP 0 issue categories (for instance Maintenance and Housing Conditions, Tenant Rights) and their corresponding official LTB application codes. Document the source used to determine each mapping is from the LTB website list of categories/applications.


## 4. Design the SQLite Database Schema
Goal: Define the SQLite table schema that will store the processed LTB catalogue data.
Description: Write a schema (SQL file or migration script) for a table containing only the fields required by MVP 0: file number, order date, issue codes, city, document type, and document URL. Add short comments explaining why each field is needed, per `plan.md` section 7.

## 5. Build the Catalogue Ingestion Script
Goal: Load the raw LTB catalogue csv file into the SQLite database using the schema from Task 4.
Description: Write a standalone script that reads the raw catalogue csv file, for each column  deleting the everything after the / include the /. This basically retains the english names because the columns are writen as english / french for inclusivity. Rename "ContentDownload URL" column to "View Order" - extracts the required fields,  and inserts them into the SQLite database. The script should be safely re-runnable (e.g. clears and reloads the table) and should log how many records were loaded.

## 6. Implement Issue Code Normalization in the Data Pipeline
Goal: Ensure each stored order retains a clean, queryable list of its issue codes.
Description: Extend the ingestion pipeline so the raw issue/application code field (which may contain multiple codes, e.g. `T1;T2;T3`) is parsed and stored in a normalized, queryable format (a join table or a consistently delimited column). Include a small test verifying that a sample multi-code row is parsed correctly.

## 7. Build the FastAPI Application Skeleton
Goal: Stand up a minimal FastAPI app with a working health-check endpoint.
Description: Create the FastAPI app entry point with a `GET /health` endpoint returning a simple status response. Add a test using FastAPI's test client confirming the endpoint returns HTTP 200. This establishes the backend server structure later endpoints will build on.

## 8. Implement the Issue-to-Code Lookup Service
Goal: Provide a backend function that translates user-selected issue names into their LTB application codes.
Description: Using the mapping from Task 3, implement a function that takes one or more user-facing issue names and returns the corresponding official codes. Include tests covering a single issue, multiple issues, and an unknown issue name.

## 9. Implement the Case Filtering Query
Goal: Write the database query logic that retrieves cases matching a given set of issue codes.
Description: Implement a function that, given a list of LTB application codes, queries the SQLite database and returns matching case records. Cover two query modes: cases containing ALL given codes, and cases containing AT LEAST ONE given code, per `plan.md` section 4. Include tests using a small seeded test database.

## 10. Implement Result Ranking and Limiting Logic
Goal: Combine "all issues matched" and "any issue matched" results into a single ranked, capped list.
Description: Implement the ranking logic from `plan.md` section 4: return cases matching all selected issues first (sorted by most recent order date), then fill remaining slots with cases matching at least one issue (also sorted by date), capped at a maximum of 20 total results. Include a test covering the "fewer than 20 full matches" fallback scenario.

## 11. Implement the POST /search API Endpoint
Goal: Expose the search functionality as a JSON API endpoint.
Description: Add a `POST /search` endpoint to the FastAPI app that accepts a list of selected issue names, uses the lookup (Task 8), filtering (Task 9), and ranking (Task 10) logic, and returns up to 20 case results with human-readable issue names. Define request/response schemas with Pydantic and add an integration test covering a real search.

## 12. Build the Frontend Issue Selection UI
Goal: Create the HTML/CSS page allowing a tenant to select one or more issues.
Description: Build a static HTML page with a multi-select control (e.g. checkboxes) for the 9 MVP 0 issue categories and a "Search" button, styled with basic CSS per `plan.md` section 9. No JavaScript logic is required beyond capturing the selected values.

## 13. Implement Frontend Search Submission and API Integration
Goal: Wire the frontend "Search" button to call the backend `/search` endpoint.
Description: Write the JavaScript that collects the selected issues from Task 12, sends them to `POST /search` via `fetch`, and handles the JSON response including empty/error states. Logging the response to the console is sufficient to verify the integration; rendering happens in Task 14.

## 14. Build the Results Table Rendering
Goal: Display search results in a table matching the plan's required columns.
Description: Implement the JavaScript/HTML logic to render the API response from Task 13 into a table with columns File Number, Order Date, Issues, City, Document Type, and View Order, per `plan.md` section 9. The "View Order" cell should be a link to the order's document URL, opening in a new tab.

## 15. Add No-Results and Legal Disclaimer Messaging
Goal: Handle the empty-results case and communicate the tool's legal boundaries to users.
Description: Add a clear "No matching orders found" message shown when the API returns zero results, and add a persistent, visible disclaimer stating the tool does not provide legal advice and that past orders do not guarantee similar outcomes, per `plan.md` section 10.

## 16. Write an End-to-End Backend Smoke Test
Goal: Verify the full flow works from a seeded database through the API to a response.
Description: Write an automated test using FastAPI's test client against a seeded test SQLite database that submits a known issue selection to `/search` and asserts the response contains the expected case fields and respects the 20-result cap. This is a backend-level test, not a browser UI test.

## 17. Write Project Setup and Run Instructions
Goal: Document how to install dependencies, load data, and run the application locally.
Description: Update the README.md soit give a projec overiew like a product manager.. summaries what the project is all about. you may want to look at the docs/mvp0/plan.md for that. Then it the README.md covering environment setup, how to run the ingestion pipeline (Tasks 3-6), how to start the FastAPI server, and how to open the frontend in a browser. A new developer should be able to get the app running without asking questions.
