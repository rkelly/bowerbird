# Requirements Document

## Introduction

The Bowerbird suite is a collection of data-only CLI tools for SQL Server. As the suite grows beyond its current two tools (compare_rowcounts.py and copy_table.py), a consistent naming convention for CLI arguments and internal variable names is essential. This spec codifies the naming patterns established during the recent refactor so that all future tools follow the same conventions, and existing tools remain the reference implementation.

## Glossary

- **Bowerbird_Tool**: Any Python CLI tool in the Bowerbird suite that operates on SQL Server data, registered as a script entry point in pyproject.toml
- **CLI_Argument**: A command-line parameter defined via argparse and passed by the user when invoking a Bowerbird_Tool
- **Internal_Variable**: A Python variable used inside a Bowerbird_Tool's source code to hold runtime state (engines, connections, inspectors, metadata, etc.)
- **Numbered_Suffix**: The digit `1` or `2` appended to a CLI_Argument or Internal_Variable to distinguish source vs. destination (e.g., `--server1`, `engine2`)
- **Shared_Argument**: A CLI_Argument that applies identically to both source and destination and therefore carries no Numbered_Suffix (e.g., `--database`, `--schema`)
- **Two_Server_Tool**: A Bowerbird_Tool that connects to both a source and a destination SQL Server instance
- **Single_Server_Tool**: A Bowerbird_Tool that connects to only one SQL Server instance
- **Connection_Builder**: The `build_url` function that constructs a SQLAlchemy connection URL from CLI_Arguments

## Requirements

### Requirement 1: Server CLI Arguments

**User Story:** As a Bowerbird developer, I want all two-server tools to use the same `--server1`/`--server2` argument names, so that users learn one pattern and apply it everywhere.

#### Acceptance Criteria

1. THE Two_Server_Tool SHALL accept `--server1` and `--server2` as required CLI_Arguments identifying the source and destination SQL Server hostnames.
2. THE Single_Server_Tool SHALL accept `--server` as a required CLI_Argument identifying the target SQL Server hostname.
3. WHEN a Bowerbird_Tool accepts server CLI_Arguments, THE Bowerbird_Tool SHALL use lowercase with no separators for the argument names (e.g., `--server1`, not `--server-1` or `--Server1`).

### Requirement 2: Database CLI Arguments

**User Story:** As a Bowerbird developer, I want database arguments to follow the same numbered/shared pattern as server arguments, so that the CLI is predictable.

#### Acceptance Criteria

1. WHEN a Two_Server_Tool connects to different databases on each server, THE Two_Server_Tool SHALL accept `--database1` and `--database2` as required CLI_Arguments.
2. WHEN a Two_Server_Tool connects to the same database name on both servers, THE Two_Server_Tool SHALL accept a single `--database` Shared_Argument instead of numbered variants.
3. THE Single_Server_Tool SHALL accept `--database` as a required CLI_Argument.

### Requirement 3: Authentication CLI Arguments

**User Story:** As a Bowerbird developer, I want authentication arguments to follow the numbered/shared pattern, so that credential handling is consistent across tools.

#### Acceptance Criteria

1. THE Bowerbird_Tool SHALL accept `--trusted` as an optional boolean CLI_Argument to enable Windows Integrated Authentication.
2. WHEN a Two_Server_Tool requires per-server SQL credentials, THE Two_Server_Tool SHALL accept `--user1`/`--password1` and `--user2`/`--password2` as CLI_Arguments.
3. WHEN a Two_Server_Tool uses shared SQL credentials for both servers, THE Two_Server_Tool SHALL accept `--user` and `--password` as Shared_Arguments.
4. THE Single_Server_Tool SHALL accept `--user` and `--password` as CLI_Arguments for SQL Server authentication.
5. IF neither `--trusted` nor credential CLI_Arguments are provided, THEN THE Bowerbird_Tool SHALL exit with a clear error message indicating that authentication is required.

### Requirement 4: Schema and Table CLI Arguments

**User Story:** As a Bowerbird developer, I want schema and table arguments to be consistent, so that users always know how to target specific objects.

#### Acceptance Criteria

1. WHEN a Bowerbird_Tool operates on a specific schema, THE Bowerbird_Tool SHALL accept `--schema` as an optional CLI_Argument defaulting to `dbo`.
2. WHEN a Bowerbird_Tool operates on a specific table, THE Bowerbird_Tool SHALL accept `--table` as a required CLI_Argument.
3. THE Bowerbird_Tool SHALL treat `--schema` and `--table` as Shared_Arguments that apply to both source and destination.

### Requirement 5: Internal Variable Naming for Engines and Connections

**User Story:** As a Bowerbird developer, I want internal variable names to mirror the CLI numbering pattern, so that reading the code is straightforward.

#### Acceptance Criteria

1. THE Two_Server_Tool SHALL name SQLAlchemy engine variables `engine1` and `engine2` corresponding to `--server1` and `--server2`.
2. THE Two_Server_Tool SHALL name connection variables `conn1` and `conn2` corresponding to `engine1` and `engine2`.
3. THE Single_Server_Tool SHALL name the SQLAlchemy engine variable `engine` and the connection variable `conn` with no numeric suffix.

### Requirement 6: Internal Variable Naming for Inspectors and Metadata

**User Story:** As a Bowerbird developer, I want inspector and metadata variables to follow the same numbered pattern, so that the codebase reads consistently.

#### Acceptance Criteria

1. WHEN a Two_Server_Tool uses SQLAlchemy inspectors, THE Two_Server_Tool SHALL name inspector variables `insp1` and `insp2` corresponding to `engine1` and `engine2`.
2. WHEN a Two_Server_Tool uses SQLAlchemy MetaData objects, THE Two_Server_Tool SHALL name metadata variables `meta1` and `meta2` corresponding to `engine1` and `engine2`.
3. WHEN a Two_Server_Tool reflects table objects, THE Two_Server_Tool SHALL name table variables `table1` and `table2` corresponding to `meta1` and `meta2`.
4. THE Single_Server_Tool SHALL name inspector, metadata, and table variables `insp`, `meta`, and `table_obj` with no numeric suffix.

### Requirement 7: Result Variable Naming

**User Story:** As a Bowerbird developer, I want result variables (row counts, data sets) to follow the numbered pattern, so that source vs. destination data is always clear.

#### Acceptance Criteria

1. WHEN a Two_Server_Tool collects per-server results, THE Two_Server_Tool SHALL name result variables with a Numbered_Suffix matching the server (e.g., `counts1`/`counts2`, `rows1`/`rows2`).
2. THE Single_Server_Tool SHALL name result variables without a numeric suffix.

### Requirement 8: Connection Builder Function

**User Story:** As a Bowerbird developer, I want every tool to build connection URLs the same way, so that connection logic is uniform and easy to refactor later.

#### Acceptance Criteria

1. THE Bowerbird_Tool SHALL use a function named `build_url` to construct SQLAlchemy connection URLs.
2. THE Connection_Builder SHALL accept parameters named `server`, `database`, `username`, `password`, and `trusted`.
3. THE Connection_Builder SHALL use ODBC Driver 18 for SQL Server as the driver string.
4. THE Connection_Builder SHALL set `TrustServerCertificate=yes` in the ODBC connection string.

### Requirement 9: Argument Naming Format Rules

**User Story:** As a Bowerbird developer, I want explicit formatting rules for argument names, so that there is no ambiguity when adding new arguments.

#### Acceptance Criteria

1. THE Bowerbird_Tool SHALL use lowercase-only CLI_Argument names with no hyphens or underscores between the base name and the Numbered_Suffix (e.g., `--server1`, not `--server-1`).
2. THE Bowerbird_Tool SHALL use a double-hyphen prefix for all CLI_Arguments (long-form only, no single-letter short flags).
3. WHEN a CLI_Argument name consists of multiple words, THE Bowerbird_Tool SHALL separate words with a single hyphen before the Numbered_Suffix (e.g., `--output-dir1`, not `--outputdir1`).
4. THE Bowerbird_Tool SHALL place the Numbered_Suffix at the very end of the CLI_Argument name.

### Requirement 10: Numbered Suffix Semantics

**User Story:** As a Bowerbird developer, I want the meaning of `1` and `2` to be consistent, so that users and developers always know which is source and which is destination.

#### Acceptance Criteria

1. THE Bowerbird_Tool SHALL use suffix `1` to denote the source server and suffix `2` to denote the destination server in all CLI_Arguments and Internal_Variables.
2. THE Bowerbird_Tool SHALL document the source/destination meaning of `1` and `2` in the tool's argparse description or help text.
