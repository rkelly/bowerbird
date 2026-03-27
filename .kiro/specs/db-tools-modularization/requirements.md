# Requirements Document

## Introduction

The project currently consists of two standalone Python scripts (`copy_table.py` and `compare_rowcounts.py`) that interact with SQL Server databases via SQLAlchemy and pyodbc. Both scripts duplicate common logic: ODBC connection-string construction, argparse CLI setup for server/auth arguments, and SQLAlchemy engine creation. This feature refactors the shared logic into a reusable `db_tools` package so that existing and future database tools can be composed from common building blocks without code duplication.

## Glossary

- **DB_Tools_Package**: A Python package (`db_tools/`) that contains shared modules for connection management, CLI argument parsing, and engine creation.
- **Connection_Builder**: A module within DB_Tools_Package responsible for constructing ODBC connection strings for SQL Server using ODBC Driver 18.
- **CLI_Module**: A module within DB_Tools_Package that provides reusable argparse argument groups for server, database, authentication, and schema parameters.
- **Engine_Factory**: A module within DB_Tools_Package that creates SQLAlchemy engine instances from connection parameters.
- **Tool_Script**: An individual command-line tool (e.g., copy-table, compare-rowcounts) that imports shared logic from DB_Tools_Package.
- **Connection_Parameters**: A structured representation (dataclass or dict) of server, database, username, password, and trusted-connection flag.

## Requirements

### Requirement 1: Connection String Construction

**User Story:** As a tool developer, I want a single reusable function for building SQL Server ODBC connection URLs, so that connection logic is defined once and stays consistent across all tools.

#### Acceptance Criteria

1. THE Connection_Builder SHALL accept server, database, username, password, and trusted-connection flag as inputs and return a valid SQLAlchemy connection URL for SQL Server with ODBC Driver 18.
2. WHEN the trusted-connection flag is set to true, THE Connection_Builder SHALL produce a connection string that uses Windows Integrated Authentication and omits username and password.
3. WHEN the trusted-connection flag is false and username and password are provided, THE Connection_Builder SHALL produce a connection string that uses SQL Server authentication with the supplied credentials.
4. THE Connection_Builder SHALL set `TrustServerCertificate=yes` in every generated connection string.
5. THE Connection_Builder SHALL URL-encode the ODBC parameter string so that special characters in server names, passwords, or database names are handled correctly.

### Requirement 2: Reusable CLI Argument Groups

**User Story:** As a tool developer, I want pre-built argparse argument groups for common database parameters, so that every new tool gets a consistent CLI interface without duplicating argument definitions.

#### Acceptance Criteria

1. THE CLI_Module SHALL provide a function that adds server, database, username, password, and trusted-connection arguments to a given argparse.ArgumentParser for a single server connection.
2. THE CLI_Module SHALL provide a function that adds source and destination server/database/credential arguments to a given argparse.ArgumentParser for dual-server tools.
3. THE CLI_Module SHALL provide a function that adds a schema argument with a default value of `dbo` to a given argparse.ArgumentParser.
4. WHEN a tool uses the single-server argument group, THE CLI_Module SHALL use argument names consistent with `--server`, `--database`, `--user`, `--password`, and `--trusted`.
5. WHEN a tool uses the dual-server argument group, THE CLI_Module SHALL use argument names prefixed with `--src-` and `--dst-` for source and destination parameters respectively.

### Requirement 3: Engine Factory

**User Story:** As a tool developer, I want a helper that creates a SQLAlchemy engine from connection parameters, so that engine creation is standardized and I don't repeat boilerplate.

#### Acceptance Criteria

1. THE Engine_Factory SHALL accept Connection_Parameters and return a configured SQLAlchemy engine instance.
2. THE Engine_Factory SHALL delegate connection-string construction to the Connection_Builder.
3. WHEN called with the same Connection_Parameters, THE Engine_Factory SHALL produce an engine that connects to the same server and database each time.

### Requirement 4: Package Structure and Installability

**User Story:** As a developer, I want the shared code organized as an installable Python package, so that tools can import it cleanly and the project can be installed with standard tooling.

#### Acceptance Criteria

1. THE DB_Tools_Package SHALL be structured as a Python package with an `__init__.py` that exposes Connection_Builder, CLI_Module, and Engine_Factory functionality.
2. THE DB_Tools_Package SHALL be installable via `pyproject.toml` using standard Python packaging (pip or uv).
3. THE DB_Tools_Package SHALL declare `sqlalchemy>=2.0` and `pyodbc>=5.0` as dependencies.

### Requirement 5: Refactor copy-table Tool

**User Story:** As a developer, I want the existing copy-table script refactored to use DB_Tools_Package, so that it no longer contains duplicated connection/CLI logic.

#### Acceptance Criteria

1. THE copy-table Tool_Script SHALL import connection-string construction from Connection_Builder instead of defining its own `build_url` function.
2. THE copy-table Tool_Script SHALL use CLI_Module to define its source/destination server arguments and schema argument.
3. THE copy-table Tool_Script SHALL use Engine_Factory to create source and destination SQLAlchemy engines.
4. WHEN the destination table does not exist, THE copy-table Tool_Script SHALL exit with an error message directing the user to deploy schema separately.
5. THE copy-table Tool_Script SHALL NOT accept a `--create` flag or issue any DDL statements.

### Requirement 6: Refactor compare-rowcounts Tool

**User Story:** As a developer, I want the existing compare-rowcounts script refactored to use DB_Tools_Package, so that it no longer contains duplicated connection/CLI logic.

#### Acceptance Criteria

1. THE compare-rowcounts Tool_Script SHALL import connection-string construction from Connection_Builder instead of defining its own `build_url` function.
2. THE compare-rowcounts Tool_Script SHALL use CLI_Module to define its server, database, authentication, and schema arguments.
3. THE compare-rowcounts Tool_Script SHALL use Engine_Factory to create SQLAlchemy engines for both servers.
4. WHEN invoked with the same arguments as before refactoring, THE compare-rowcounts Tool_Script SHALL produce identical behavior (same output format, same exit codes).

### Requirement 7: Safety Guard for Same-Source-Destination

**User Story:** As a tool user, I want the shared module to provide a reusable safety check that prevents accidentally running a destructive tool against the same source and destination, so that data is protected consistently across tools.

#### Acceptance Criteria

1. THE DB_Tools_Package SHALL provide a validation function that compares source and destination Connection_Parameters and determines whether they refer to the same server and database (case-insensitive comparison).
2. WHEN source and destination Connection_Parameters refer to the same server and database, THE validation function SHALL raise an error or return a failure indicator.
3. THE copy-table Tool_Script SHALL invoke the shared validation function instead of implementing its own inline check.

### Requirement 8: Data-Only Principle

**User Story:** As a tool user, I want these tools to only operate on data and never modify database schema, so that schema management stays under the control of our declarative SQL Server Database Project.

#### Acceptance Criteria

1. NO Tool_Script SHALL issue DDL statements such as CREATE TABLE, DROP TABLE, or ALTER TABLE.
2. WHEN a required table does not exist on the target server, THE Tool_Script SHALL exit with a clear error message indicating that schema must be deployed separately.
3. THE DB_Tools_Package SHALL NOT provide any helper functions that create, drop, or alter database objects.
