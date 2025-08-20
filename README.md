# sbi_stock_analysis

A project for analyzing stock portfolios using transaction CSV files downloaded from SBI Securities.  
Currently designed for Japan-only formats.

## Features

- Upload and clean SBI Securities transaction CSVs
- Store transactions in a SQLite database
- Analyze portfolio performance (realized/unrealized profit, etc.)
- Visualize metrics and transaction history with Dash web app
- Supports stock name changes, duplicate handling, and more

## Usage

1. **Clone the repository:**
    ```bash
    git clone https://github.com/hiepqvbn/sbi_stock_analysis.git
    cd sbi_stock_analysis
    ```

2. **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

3. **Initialize the database:**
    ```bash
    python cli.py init-db
    ```

4. **Run the Dash app:**
    ```bash
    python app.py
    ```

5. **Upload your SBI CSV files via the web interface.**

## Notes

- Data files (`*.csv`, `*.db`) are excluded from the repository.
- Only SBI Securities Japan CSV format is supported.
- See `.gitignore` for excluded files/folders.

## License
MIT License