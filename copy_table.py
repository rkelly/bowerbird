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

def copy_table(src_engine, dst_engine, table_name, schema="dbo", create=False):
    dst_insp = inspect(dst_engine)
    dst_exists = dst_insp.has_table(table_name, schema=schema)

    if not dst_exists and not create:
        sys.exit(f"Error: {schema}.{table_name} does not exist on destination. Pass --create to auto-create it.")

    src_meta = MetaData()
    src_meta.reflect(bind=src_engine, schema=schema, only=[table_name])
    src_table = src_meta.tables[f"{schema}.{table_name}"]
    col_names = [c.name for c in src_table.columns]
    qualified = f"[{schema}].[{table_name}]"
    col_list = ", ".join(f"[{c}]" for c in col_names)

    if not dst_exists:
        src_table.create(bind=dst_engine)
        print(f"Created {qualified} on destination")

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
    p.add_argument("--src-server", required=True)
    p.add_argument("--src-db", required=True)
    p.add_argument("--dst-server", required=True)
    p.add_argument("--dst-db", required=True)
    p.add_argument("--table", required=True)
    p.add_argument("--schema", default="dbo")
    p.add_argument("--src-user")
    p.add_argument("--src-pass")
    p.add_argument("--dst-user")
    p.add_argument("--dst-pass")
    p.add_argument("--trusted", action="store_true")
    p.add_argument("--create", action="store_true")
    args = p.parse_args()

    if args.src_server.lower() == args.dst_server.lower() and args.src_db.lower() == args.dst_db.lower():
        sys.exit("Error: source and destination are the same server/database. Aborting to protect data.")

    src_engine = create_engine(build_url(args.src_server, args.src_db, args.src_user, args.src_pass, args.trusted))
    dst_engine = create_engine(build_url(args.dst_server, args.dst_db, args.dst_user, args.dst_pass, args.trusted))

    copy_table(src_engine, dst_engine, args.table, args.schema, args.create)

if __name__ == "__main__":
    main()
