# Implementation Plan: db-tools-modularization

## Overview

Extract shared logic from `copy_table.py` and `compare_rowcounts.py` into an installable `db_tools` package with four modules (connection, cli, engine, safety), then refactor both tool scripts to import from the package. Uses `uv` for packaging, `pytest` + `hypothesis` for testing.

## Tasks

- [ ] 1. Create db_tools package with ConnectionParams dataclass
  - [ ] 1.1 Create `db_tools/__init__.py` and `db_tools/connection.py` with `ConnectionParams` dataclass and `build_url()` function
    - Define frozen `ConnectionParams` dataclass with fields: server, database, username, password, trusted
    - Implement `build_url()` that constructs `mssql+pyodbc:///?odbc_connect=...` URL with ODBC Driver 18, `TrustServerCertificate=yes`, URL-encoded ODBC string
    - Handle trusted (Windows Integrated Auth) vs SQL auth branching
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5_

  - [ ]* 1.2 Write property tests for `build_url()` — Property 1: Connection URL structure invariants
    - **Property 1: Connection URL structure invariants**
    - Generate random server/database/credential combos via `st.text()`. Assert URL starts with `mssql+pyodbc:///?odbc_connect=`, contains `ODBC+Driver+18+for+SQL+Server`, contains `TrustServerCertificate=yes`, and contains the provided server and database in the decoded ODBC string.
    - **Validates: Requirements 1.1, 1.4**

  - [ ]* 1.3 Write property tests for `build_url()` — Property 2: Auth mode matches trusted flag
    - **Property 2: Auth mode matches trusted flag**
    - Generate random ConnectionParams with `trusted` as `st.booleans()`. Assert trusted=True produces `Trusted_Connection=yes` without `uid=`/`pwd=`; trusted=False with credentials produces `uid=`/`pwd=` without `Trusted_Connection=yes`.
    - **Validates: Requirements 1.2, 1.3**

  - [ ]* 1.4 Write property tests for `build_url()` — Property 3: URL encoding round-trip
    - **Property 3: URL encoding round-trip**
    - Generate strings containing special characters (`; = & % +` space). Assert URL-decode of the `odbc_connect` parameter preserves original server, database, and password values verbatim.
    - **Validates: Requirements 1.5**

- [ ] 2. Implement CLI argument groups module
  - [ ] 2.1 Create `db_tools/cli.py` with `add_single_server_args()`, `add_dual_server_args()`, and `add_schema_arg()`
    - `add_single_server_args(parser, prefix="")` adds `--server`, `--database`, `--user`, `--password`, `--trusted` (or prefixed variants)
    - `add_dual_server_args(parser)` adds `--src-server`, `--src-db`, `--src-user`, `--src-pass`, `--dst-*` arguments
    - `add_schema_arg(parser, default="dbo")` adds `--schema` with default
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_

  - [ ]* 2.2 Write unit tests for CLI argument groups
    - Verify `add_single_server_args` adds expected argument names
    - Verify `add_dual_server_args` adds `--src-*` and `--dst-*` arguments
    - Verify `add_schema_arg` defaults to `"dbo"`
    - Verify prefixed single-server args produce correct dest names
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_

- [ ] 3. Implement engine factory and safety guard
  - [ ] 3.1 Create `db_tools/engine.py` with `create_engine_from_params()`
    - Accept `ConnectionParams`, delegate to `build_url()`, return `sqlalchemy.Engine`
    - _Requirements: 3.1, 3.2, 3.3_

  - [ ] 3.2 Create `db_tools/safety.py` with `check_same_server_database()`
    - Accept src and dst `ConnectionParams`, raise `ValueError` if server and database match case-insensitively
    - _Requirements: 7.1, 7.2_

  - [ ]* 3.3 Write property tests for engine factory — Property 4: Engine factory delegates to build_url
    - **Property 4: Engine factory delegates to build_url**
    - Generate random ConnectionParams. Assert engine URL string equals `build_url()` output for the same params.
    - **Validates: Requirements 3.1, 3.2**

  - [ ]* 3.4 Write property tests for engine factory — Property 5: Engine creation is deterministic
    - **Property 5: Engine creation is deterministic**
    - Generate random ConnectionParams. Call `create_engine_from_params()` twice, assert URL strings are identical.
    - **Validates: Requirements 3.3**

  - [ ]* 3.5 Write property tests for safety guard — Property 6: Same-server-database detection
    - **Property 6: Same-server-database detection**
    - Generate random server/database strings. Construct two ConnectionParams with same values (varying case), assert `check_same_server_database()` raises `ValueError`. Generate two with differing values, assert it does not raise.
    - **Validates: Requirements 7.1, 7.2**

- [ ] 4. Finalize package structure and installability
  - [ ] 4.1 Update `db_tools/__init__.py` to re-export public API and update `pyproject.toml`
    - Re-export: `build_url`, `ConnectionParams`, `create_engine_from_params`, `add_single_server_args`, `add_dual_server_args`, `add_schema_arg`, `check_same_server_database`
    - Update `pyproject.toml`: rename project or add `db_tools` as a package, declare `sqlalchemy>=2.0` and `pyodbc>=5.0` dependencies, add `pytest` and `hypothesis` as dev dependencies
    - _Requirements: 4.1, 4.2, 4.3_

- [ ] 5. Checkpoint — Verify package tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 6. Refactor copy_table.py to use db_tools package
  - [ ] 6.1 Rewrite `copy_table.py` to import from `db_tools`
    - Remove inline `build_url()` function
    - Use `add_dual_server_args()` + `add_schema_arg()` for CLI argument parsing
    - Use `create_engine_from_params()` for engine creation
    - Use `check_same_server_database()` for safety guard (replace inline check)
    - Keep `copy_table()` function and tool-specific logic in the script
    - Ensure no `--create` flag exists, no DDL statements
    - Exit with error if destination table doesn't exist
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 7.3, 8.1, 8.2_

  - [ ]* 6.2 Write unit tests for refactored copy_table.py
    - Verify `--create` flag is not accepted (argparse rejects it)
    - Verify missing destination table produces expected error message (mock inspect)
    - _Requirements: 5.4, 5.5, 8.1, 8.2_

- [ ] 7. Refactor compare_rowcounts.py to use db_tools package
  - [ ] 7.1 Rewrite `compare_rowcounts.py` to import from `db_tools`
    - Remove inline `build_url()` function
    - Use `add_single_server_args()` twice with prefixes `"server1"` and `"server2"` + `add_schema_arg()` for CLI argument parsing
    - Use `create_engine_from_params()` for engine creation
    - Keep `get_rowcounts()` and reporting logic in the script
    - Preserve identical behavior: same output format, same exit codes
    - _Requirements: 6.1, 6.2, 6.3, 6.4_

  - [ ]* 7.2 Write unit tests for refactored compare_rowcounts.py
    - Verify CLI args parse correctly after refactor
    - Verify output format and exit codes match original behavior
    - _Requirements: 6.4_

- [ ] 8. Final checkpoint — Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Property tests use Hypothesis with `@settings(max_examples=100)` minimum
- Each property test must be tagged with `# Feature: db-tools-modularization, Property N: <title>`
- The data-only principle is enforced throughout: no DDL in any tool or package module
- Git conventions: make atomic commits with conventional prefixes after each logical unit
