# Bowerbird

A suite of data-only tools for SQL Server. These tools operate strictly on data — schema is managed separately via a declarative SQL Server Database Project.

## Tools

### copy-table

Copies all rows from a table on one server to the same table on another server. Handles identity columns automatically.

```
uv run copy-table --trusted --src-server SRV1 --src-db MyDB --dst-server SRV2 --dst-db MyDB --schema dbo --table my_table
```

### compare-rowcounts

Compares row counts for every table in a schema across two servers. Exits with code 1 if any differences are found.

```
uv run compare-rowcounts --trusted --server1 SRV1 --server2 SRV2 --database MyDB --schema dbo
```

## Authentication

All tools support two authentication modes:

- `--trusted` — Windows Integrated Authentication
- `--user` / `--password` — SQL Server authentication

## Requirements

- Python 3.10+
- ODBC Driver 18 for SQL Server
- Network access to target SQL Server instances

## Install

```
uv sync
```

## Principles

- Data only — no CREATE TABLE, DROP TABLE, or ALTER TABLE
- Schema is owned by the SQL Server Database Project
- If a target table doesn't exist, the tool errors with a clear message
