import argparse
from urllib.parse import quote_plus
import sys
from sqlalchemy import create_engine, text, inspect, MetaData

def build_url(server, database, username=None, password=None, trusted=False):
    driver = "ODBC+Driver+18+for+SQL+Server"
    params = f"driver={driver};server={server};database={database};TrustServerCertificate=yes"
    if trusted:
        params += ";Trusted_Connection=yes"
    else:
        params += f";uid={username};pwd={password}"
    return f"mssql+pyodbc:///?odbc_connect={quote_plus(params)}"

def copy_table(src_engine, dst_engine, table_name, schema="dbo"):
    dst_insp = inspect(dst_engine)
    if not dst_insp.has_table(table_name, schema=schema):
        sys.exit(f"Error: {schema}.{table_name} does not exist on destination. Schema must be deployed separately.")

    src_insp = inspect(src_engine)
    available = src_insp.get_table_names(schema=schema)
    if table_name not in available:
        # Try case-insensitive match
        match = next((t for t in available if t.lower() == table_name.lower()), None)
        if match:
            sys.exit(f"Error: {schema}.{table_name} not found on source. Did you mean '{match}'?")
        else:
            sys.exit(f"Error: {schema}.{table_name} not found on source. Available tables in {schema}: {', '.join(available[:20])}")

    src_meta = MetaData()
    src_meta.reflect(bind=src_engine, schema=schema, only=[table_name])
    src_table = src_meta.tables[f"{schema}.{table_name}"]
    col_names = [c.name for c in src_table.columns]
    qualified = f"[{schema}].[{table_name}]"
    col_list = ", ".join(f"[{c}]" for c in col_names)

    with src_engine.connect() as src_conn:
        rows = src_conn.execute(text(f"SELECT {col_list} FROM {qualified}")).fetchall()

    has_identity = any(c.autoincrement is True or (c.autoincrement == "auto" and c.primary_key)
                       for c in src_table.columns if hasattr(c, 'autoincrement'))

    with dst_engine.begin() as dst_conn:
        dst_conn.execute(text(f"DELETE FROM {qualified}"))
        if rows:
            if has_identity:
                dst_conn.execute(text(f"SET IDENTITY_INSERT {qualified} ON"))
            placeholders = ", ".join(f":{c}" for c in col_names)
            insert = f"INSERT INTO {qualified} ({col_list}) VALUES ({placeholders})"
            dst_conn.execute(text(insert), [dict(zip(col_names, row)) for row in rows])
            if has_identity:
                dst_conn.execute(text(f"SET IDENTITY_INSERT {qualified} OFF"))

    print(f"Copied {len(rows)} rows to {qualified}")

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--server1", required=True)
    p.add_argument("--database1", required=True)
    p.add_argument("--server2", required=True)
    p.add_argument("--database2", required=True)
    p.add_argument("--table", required=True)
    p.add_argument("--schema", default="dbo")
    p.add_argument("--user1")
    p.add_argument("--password1")
    p.add_argument("--user2")
    p.add_argument("--password2")
    p.add_argument("--trusted", action="store_true")
    args = p.parse_args()

    if args.server1.lower() == args.server2.lower() and args.database1.lower() == args.database2.lower():
        sys.exit("Error: source and destination are the same server/database. Aborting to protect data.")

    src_engine = create_engine(build_url(args.server1, args.database1, args.user1, args.password1, args.trusted))
    dst_engine = create_engine(build_url(args.server2, args.database2, args.user2, args.password2, args.trusted))

    copy_table(src_engine, dst_engine, args.table, args.schema)

if __name__ == "__main__":
    main()
