# cli.py
import argparse
import os
from data_handler.csv_parser import clean_sbi_transaction_csv, clean_sbi_cash_flow_csv
from data_handler.db_manager import insert_new_rows, insert_cash_flows, init_db, clear_db, clear_cash_flows, fetch_summary

UPLOAD_FOLDER = "uploads"

def import_csvs():
    csv_files = [f for f in os.listdir(UPLOAD_FOLDER) if f.endswith('.csv')]
    if not csv_files:
        print("No CSV files found in 'uploads/' folder.")
        return
    for file in csv_files:
        path = os.path.join(UPLOAD_FOLDER, file)
        try:
            print(f"📂 Importing {file}...")
            df = clean_sbi_transaction_csv(path)
            insert_new_rows(df)
            print(f"✅ Done: {file}")
        except Exception as e:
            print(f"❌ Failed to import {file}: {e}")

def import_cash_flows(file_path):
    try:
        print(f"📂 Importing cash flows from {file_path}...")
        df = clean_sbi_cash_flow_csv(file_path)
        insert_cash_flows(df)
        print(f"✅ Done: {file_path}")
    except Exception as e:
        print(f"❌ Failed to import {file_path}: {e}")

def reset_db():
    db_path = "data/portfolio.db"
    if os.path.exists(db_path):
        os.remove(db_path)
    init_db(db_path)
    print("Database reset and initialized.")

def main():
    parser = argparse.ArgumentParser(description="Stock Portfolio CLI Tool")
    subparsers = parser.add_subparsers(dest="command", help="Sub-commands")

    # init-db
    subparsers.add_parser("init-db", help="Initialize the database")

    # clear-db
    subparsers.add_parser("clear-db", help="Clear all data in the database")
    # clear-cash
    subparsers.add_parser("clear-cash", help="Clear cash_flows table")

    # import
    subparsers.add_parser("import", help="Import CSVs from uploads folder")
    # import-cash
    import_cash = subparsers.add_parser("import-cash", help="Import cash flow CSV")
    import_cash.add_argument("file", help="Path to cash flow CSV file")

    # summary
    subparsers.add_parser("summary", help="Show portfolio summary (total buy/sell)")

    # reset-db
    subparsers.add_parser("reset-db", help="Delete and re-initialize the database")

    args = parser.parse_args()

    if args.command == "init-db":
        init_db()
        print("✅ Database initialized.")
    elif args.command == "clear-db":
        clear_db()
        print("🧹 Database cleared.")
    elif args.command == "clear-cash":
        clear_cash_flows()
        print("🧹 Cash flows cleared.")
    elif args.command == "import":
        import_csvs()
    elif args.command == "import-cash":
        import_cash_flows(args.file)
    elif args.command == "summary":
        summary = fetch_summary()
        print("📊 Portfolio Summary:")
        for row in summary:
            print(row)
    elif args.command == "reset-db":
        reset_db()
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
