import argparse
import sys
from urllib.parse import quote_plus
from sqlalchemy import create_engine, text, inspect

def build_url(server, database, username=None, password=None, trusted=False):
    driver = "ODBC+Driver+18+for+SQL+Server"
    params = f"driver={driver};server={server};database={database};TrustServerCertificate=yes"
    if trusted:
        params += ";Trusted_Connection=yes"
    else:
        params += f";uid={username};pwd={password}"
    return f"mssql+pyodbc:///?odbc_connect={quote_plus(params)}"

def get_rowcounts(engine, schema):
    insp = inspect(engine)
    tables = insp.get_table_names(schema=schema)
    counts = {}
    with engine.connect() as conn:
        for t in tables:
            row = conn.execute(text(f"SELECT COUNT(*) FROM [{schema}].[{t}]")).scalar()
            counts[t] = row
    return counts

def main():
    p = argparse.ArgumentParser(description="Compare row counts between two servers for a given database/schema.")
    p.add_argument("--server1", required=True)
    p.add_argument("--server2", required=True)
    p.add_argument("--database", required=True)
    p.add_argument("--schema", default="dbo")
    p.add_argument("--user")
    p.add_argument("--password")
    p.add_argument("--trusted", action="store_true")
    args = p.parse_args()

    engine1 = create_engine(build_url(args.server1, args.database, args.user, args.password, args.trusted))
    engine2 = create_engine(build_url(args.server2, args.database, args.user, args.password, args.trusted))

    counts1 = get_rowcounts(engine1, args.schema)
    counts2 = get_rowcounts(engine2, args.schema)

    all_tables = sorted(set(counts1) | set(counts2))
    if not all_tables:
        sys.exit("No tables found in the specified schema.")

    name_width = max(len(t) for t in all_tables)
    header = f"{'Table':<{name_width}}  {'Server1':>10}  {'Server2':>10}  {'Diff':>10}  Status"
    print(header)
    print("-" * len(header))

    mismatches = 0
    for t in all_tables:
        c1 = counts1.get(t)
        c2 = counts2.get(t)
        if c1 is None:
            print(f"{t:<{name_width}}  {'MISSING':>10}  {c2:>10}  {'':>10}  ← only on server2")
            mismatches += 1
        elif c2 is None:
            print(f"{t:<{name_width}}  {c1:>10}  {'MISSING':>10}  {'':>10}  ← only on server1")
            mismatches += 1
        else:
            diff = c2 - c1
            status = "OK" if diff == 0 else "MISMATCH"
            if diff != 0:
                mismatches += 1
            print(f"{t:<{name_width}}  {c1:>10}  {c2:>10}  {diff:>+10}  {status}")

    print()
    print(f"{len(all_tables)} tables compared, {mismatches} difference(s) found.")
    sys.exit(1 if mismatches else 0)

if __name__ == "__main__":
    main()
