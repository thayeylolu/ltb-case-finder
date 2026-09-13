# Issue Taxonomy

`issue_taxonomy.json` is the authoritative mapping between LTB application codes and the 14 user-facing issue categories used by MVP 0 (see `docs/mvp0/plan.md` section 3.2).

## Structure

Each entry has:

* `code` — the official LTB application code (e.g. `L1`, `T6`, `C4`)
* `name` — a short description of what the application is for
* `categories` — one or more of the 14 MVP 0 issue categories this code belongs to (a code can belong to more than one category)

## Sources

* **L, A, and T codes** (landlord and tenant application forms): [tribunalsontario.ca/ltb/forms-filing-and-fees](https://tribunalsontario.ca/ltb/forms-filing-and-fees/#panel1)
* **C codes** (non-profit co-op eviction applications — C1–C4): [tribunalsontario.ca/ltb/non-profit-co-op-evictions](https://tribunalsontario.ca/ltb/non-profit-co-op-evictions/)

The 14 category names themselves (`Rent and Payment`, `Tenancy Eviction`, `Notice`, etc.) are not verbatim labels from either source page — both pages group forms by audience (landlord/tenant) and form type (notice/application), not by issue. The categories are a classification layer applied on top of the official codes, based on each code's stated purpose.

## Category → code reference

| Category | Codes |
| --- | --- |
| Rent and Payment | L1, L2, L9, L10, T1 |
| Tenancy Eviction | L1, L2, L4, T5, C1, C2, C3, C4 |
| Tenancy Ending | L3 |
| Notice | L3, T5 |
| Breached Conditions | L4, T4, T5, C4 |
| Rent Change | L5, A4, T3, T4 |
| Maintenance | L6, T6 |
| Care Home Tenancies | L7 |
| Locks and Access | L8 |
| Tenancy Agreements | A1, A2 |
| Tenant Rights | T2 |
| Suite Meters | T7 |
| Co-op Housing | C1, C2, C3, C4 |
| Arrears | C1 |
