# LTB Case Discovery Tool

## 1. Project Overview

A simple web application that helps Ontario residential tenants find Landlord and Tenant Board decisions related to their rental issue.

The application uses the Ontario Open Data LTB Order Catalogue as its primary data source.

MVP 0 will focus on **structured case discovery**. Users select one or more predefined LTB issue categories and receive up to 20 matching LTB orders.

The application does not provide legal advice or determine whether a user's situation has a particular legal outcome.

---

## 2. Target User

The primary user is an **Ontario residential tenant** who wants to find previous LTB orders related to a rental issue.

The user may not know the relevant legal terminology or LTB application code.

The application therefore presents issue categories in user friendly language while maintaining the official LTB application codes internally.

---

# 3. MVP 0

## 3.1 Goal

Allow a tenant to quickly find LTB orders associated with one or more selected issues without requiring the application to read or analyse the contents of the order documents.

MVP 0 is intentionally limited to structured filtering using metadata available in the Ontario LTB Order Catalogue.

---

## 3.2 User Flow

### Step 1: Select an issue

The user selects at least one issue from a predefined list.

The initial issue categories are:

* Rent and Payment
* Tenancy Eviction
* Tenancy Ending
* Notice
* Breached Conditions
* Rent Change
* Maintenance
* Care Home Tenancies
* Locks and Access
* Tenancy Agreements
* Tenant Rights
* Suite Meters
* Co-op Housing
* Arrears

Multiple issues can be selected.

There is no `Other` option.

The application should use the official LTB issue/application categories as the underlying source for these selections.

The user facing names and their corresponding LTB application codes will be documented separately in the implementation plan.

### Step 2: Search

The user submits their selected issue(s).

MVP 0 does not include a free text description of the user's situation.

### Step 3: View results

The application returns up to 20 matching LTB orders.

Each result displays:

* File Number
* Order Date
* Issues
* City
* Document Type
* View Order

The `Issues` field displays human readable issue names rather than application codes.

For example:

`Maintenance · Tenant Rights · Rent and Payment`

rather than:

`T1;T2;T3`

The application codes remain available internally for filtering and ranking.

---

# 4. MVP 0 Search Logic

The application will use the application/issue codes contained in the Ontario LTB Order Catalogue.

The system will identify all occurrences of the selected issue codes in the relevant catalogue fields.

### Multiple selected issues

When the user selects multiple issues, cases containing **all selected issues** are considered the strongest matches.

For example, if the user selects:

`Maintenance + Tenant Rights`

the system first retrieves cases containing both corresponding issue codes.

These cases are ordered by most recent Order Date.

If fewer than 20 cases contain all selected issues, the system then retrieves cases containing at least one of the selected issues.

The remaining results are ordered by most recent Order Date until a maximum of 20 results is reached.

### Maximum results

The application will return a maximum of **20 cases per search**.

This keeps the MVP simple and limits unnecessary database and server processing.

### No results

If there are no matching cases, the application returns no results.

MVP 0 does not attempt an alternative search or generate recommendations.

---

# 5. Data Source

## Primary Source

Ontario Open Data LTB Order Catalogue.

The catalogue provides metadata associated with LTB orders, including information required to identify and link to orders.

The application will use the catalogue rather than initially processing the contents of the order PDFs.

## Order Documents

MVP 0 does **not** download, extract, parse, OCR, or analyse the contents of LTB order documents.

Instead, the application uses the document URL provided by the catalogue.

When the user selects `View Order`, they can access the corresponding order document.

---

# 6. Data Processing

The initial data pipeline will:

1. Obtain the Ontario LTB Order Catalogue
2. Load the catalogue into the application's database
3. Identify the relevant metadata fields
4. Identify application/issue codes
5. Map official codes to user facing issue names
6. Store the processed records
7. Use the stored records to perform issue based searches

The application should preserve the original application codes because they are required for filtering and future processing.

---

# 7. Database

## MVP 0 Database

SQLite will be used for MVP 0.

The database should contain the catalogue information required to:

* Identify an LTB order
* Identify its application/issue codes
* Determine its order date
* Determine its city
* Determine its document type
* Access the original order
* Display the human readable issue names

The database schema should avoid storing unnecessary information that is not required by MVP 0.

---

# 8. Backend

FastAPI will provide the backend API.

The backend will be responsible for:

* Loading and accessing case metadata
* Mapping user selected issues to LTB application codes
* Filtering cases
* Ranking matching cases
* Limiting results to 20
* Returning case metadata to the frontend

The frontend should not directly query the SQLite database.

---

# 9. Frontend

MVP 0 will use simple HTML, CSS, and JavaScript.

The frontend will contain:

### Issue Selection

A multi select interface allowing the tenant to select one or more issues.

### Search

A button to submit the selected issues.

### Results

A table displaying:

| File Number | Order Date | Issues | City | Document Type | View Order |
| ----------- | ---------- | ------ | ---- | ------------- | ---------- |

The interface should remain simple and functional.

No authentication or user account is required for MVP 0.

---

# 10. Legal and Product Boundaries

The application is a **case discovery and research tool**.

It does not:

* Provide legal advice
* Predict the outcome of a tenant's case
* Determine whether a tenant has a valid claim
* Recommend a specific legal remedy
* Interpret an LTB order for the user
* Represent that a previous decision will apply to the user's situation

The application should make it clear that finding a similar LTB order does not mean that the same outcome will apply to the user's circumstances.

---

# 11. Explicit MVP 0 Exclusions

The following are outside the scope of MVP 0:

* Free text case descriptions
* TF IDF
* Cosine similarity
* LLM integration
* Case text extraction
* PDF text processing
* OCR
* CanLII integration
* User accounts
* Authentication
* Personal case history
* Legal advice
* Automated legal recommendations
* Case outcome prediction
* Complex filtering
* Infinite scrolling
* Returning more than 20 results

---
# 13. Technology Stack

| Component                | Technology                            |
| ------------------------ | ------------------------------------- |
| Data source              | Ontario Open Data LTB Order Catalogue |
| Backend                  | FastAPI                               |
| Database                 | SQLite                                |
| Frontend                 | HTML, CSS, JavaScript                 |
| MVP 0 search             | Structured metadata filtering         |


---

# 14. MVP 0 Success Criteria

MVP 0 is successful if a tenant can:

1. Open the application
2. Select one or more LTB issues
3. Submit the search
4. Receive matching LTB orders
5. See the relevant metadata for each order
6. Open the original order
7. Receive no more than 20 results

The application should work without requiring the tenant to understand LTB application codes.

The primary purpose of MVP 0 is to establish the **data pipeline, issue taxonomy, search logic, backend API, and basic user experience** before introducing document processing and text based relevance in MVP 1.
