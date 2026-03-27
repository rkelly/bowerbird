---
inclusion: always
---

# Data-Only Principle

- These tools operate on data only — never alter schema (no CREATE TABLE, DROP TABLE, ALTER TABLE, etc.)
- Schema is managed by a separate declarative SQL Server Database Project
- If a target table doesn't exist, the tool should error with a clear message directing the user to deploy schema separately
