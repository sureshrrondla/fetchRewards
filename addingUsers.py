import json
import pandas as pd
import uuid
import psycopg2
from psycopg2.extras import execute_batch

# 📌 PostgreSQL Connection Details (Corrected DSN Format for psycopg2)
db_params = {
    "dbname": "fetchRewards",
    "user": "postgres",
    "password": "<password>",
    "host": "localhost",
    "port": "5432"
}

# Function to load JSON safely
def load_json_data(file_path):
    data = []
    with open(file_path, 'r') as file:
        first_char = file.read(1)
        file.seek(0)

        if first_char == "[":  # JSON Array
            data = json.load(file)
        else:  # NDJSON (one JSON object per line)
            for line in file:
                try:
                    data.append(json.loads(line.strip()))
                except json.JSONDecodeError as e:
                    print(f"Error decoding JSON: {e}")

    return pd.DataFrame(data)

# Function to validate and format UUID
def validate_uuid(value):
    try:
        return str(uuid.UUID(value))  # Converts valid UUID to a standard format
    except (ValueError, TypeError):
        return str(uuid.uuid4())  # Generates a new UUID if invalid

# Function to clean and process users data
def process_users_data(df):
    users_data = []

    for _, row in df.iterrows():
        try:
            # Ensure "_id" exists and is iterable
            row["_id"] = row.get("_id", {})
            user_id = validate_uuid(row["_id"].get("$oid", str(uuid.uuid4())))

            # Ensure "state" is a string and only 2 characters long
            user_state = str(row.get("state", "")).strip()[:2] if isinstance(row.get("state"), str) else None

            # Convert timestamps correctly
            account_created_date = pd.to_datetime(row["createdDate"]["$date"], unit="ms") if "createdDate" in row and isinstance(row["createdDate"], dict) else None
            last_login_date = pd.to_datetime(row["lastLogin"]["$date"], unit="ms") if "lastLogin" in row and isinstance(row["lastLogin"], dict) else None

            # Assign role and active status with default values
            user_role = row.get("role", "consumer")
            is_active = bool(row.get("active", True))  # Convert to boolean

            user_record = (user_id, user_state, account_created_date, last_login_date, user_role, is_active)
            users_data.append(user_record)

        except Exception as e:
            print(f"Skipping row due to error: {e}")

    return users_data

# Load and process users.json
users_df = load_json_data("users.json")
users_data = process_users_data(users_df)

# Insert data into PostgreSQL table using psycopg2 execute_batch
try:
    # Connect to PostgreSQL using psycopg2
    conn = psycopg2.connect(**db_params)
    cursor = conn.cursor()

    insert_query = """
        INSERT INTO dim_users (user_id, user_state, account_created_date, last_login_date, user_role, is_active)
        VALUES (%s, %s, %s, %s, %s, %s)
        ON CONFLICT (user_id) DO NOTHING;
    """

    execute_batch(cursor, insert_query, users_data)  # Perform batch insert

    conn.commit()
    cursor.close()
    conn.close()

    print(f"{len(users_data)} records attempted for insertion into dim_users.")

except Exception as e:
    print(f"Error inserting data: {e}")
