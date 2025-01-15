# Database Synchronization Tool

This script synchronizes data between a primary and secondary database, ensuring data consistency and providing synchronization tracking. It is built using Python and SQLAlchemy and supports PostgreSQL databases.

## Features

- Synchronizes data from specified tables in the primary database to the secondary database.
- Automatically creates tables in the secondary database if they do not exist.
- Tracks synchronization timestamps using a `sync_tracking` table.
- Detects the first run and performs a full data synchronization.
- Handles subsequent runs with incremental updates based on table changes.
- Logs all synchronization activities.

## Requirements

- Python 3.7+
- PostgreSQL
- Required Python libraries:
  - `SQLAlchemy`
  - `psycopg2`
  - `datetime`
  - `logging`

## Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/your-repo-name/db-sync-engine.git
   cd db-sync-engine
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Update database configurations:**
   Modify the `PRIMARY_DB_URL` and `SECONDARY_DB_URL` variables in the script to match your PostgreSQL database connection details.

   ```python
   PRIMARY_DB_URL = "postgresql+psycopg2://user:password@localhost/primary_db"
   SECONDARY_DB_URL = "postgresql+psycopg2://user:password@localhost/secondary_db"
   ```

4. **Specify tables to sync:**
   Update the `tables_to_sync` list with the names of tables you want to synchronize.

   ```python
   tables_to_sync = ['example_table', 'another_table']
   ```

## Usage

1. **Run the script:**
   ```bash
   python sync_db_changes.py
   ```

2. **First Run:**
   - On the first run, the script detects that it is running for the first time (based on the `sync_tracking` table) and performs a full data synchronization for all specified tables.

3. **Subsequent Runs:**
   - For subsequent runs, the script synchronizes only changes detected in the primary database.

## Synchronization Tracking

- A `sync_tracking` table is created in the secondary database to track the last synchronization timestamp for each table.
- If the `sync_tracking` table is empty or does not exist, the script considers it the first run and performs a full synchronization.

## Logging

- All synchronization activities and errors are logged.
- Logs are displayed in the console for real-time monitoring.

## Customization

- **Database Types:** Although the script is configured for PostgreSQL, you can modify the connection URLs to support other SQLAlchemy-compatible databases.
- **Table List:** Add or remove tables from the `tables_to_sync` list to control which tables are synchronized.

## License

This project is licensed under the MIT License. See the LICENSE file for details.

## Contributing

Contributions are welcome! Feel free to open issues or submit pull requests.

## Author

Created by [Your Name](https://github.com/your-profile).

