import json
import pandas as pd
import uuid
import psycopg2
from psycopg2.extras import execute_batch

# 📌 Corrected PostgreSQL Connection Details for psycopg2
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

# Process and format brands data
def process_brands_data(df):
    brands_data = []

    for _, row in df.iterrows():
        try:
            # Validate and format brand_id
            brand_id = validate_uuid(row["_id"]["$oid"]) if "_id" in row and "$oid" in row["_id"] else str(uuid.uuid4())

            brand_record = (
                brand_id,  # UUID
                row.get("name", "Unknown Brand"),  # Brand title
                row.get("category", None),  # Category
                row.get("categoryCode", None),  # Category code
                row.get("barcode", None),  # Barcode
                bool(row.get("topBrand", False))  # Ensure boolean type
            )

            brands_data.append(brand_record)

        except Exception as e:
            print(f"Skipping row due to error: {e}")

    return brands_data

# Load and process brands.json
brands_df = load_json_data("brands.json")
brands_data = process_brands_data(brands_df)

# Insert data into PostgreSQL table using psycopg2 execute_batch
try:
    # Connect to PostgreSQL using psycopg2 with corrected DSN format
    conn = psycopg2.connect(**db_params)
    cursor = conn.cursor()

    insert_query = """
        INSERT INTO dim_brands (brand_id, brand_title, brand_category, brand_category_code, brand_barcode, is_top_brand)
        VALUES (%s, %s, %s, %s, %s, %s)
        ON CONFLICT (brand_id) DO NOTHING;
    """

    execute_batch(cursor, insert_query, brands_data)  # Perform batch insert

    conn.commit()
    cursor.close()
    conn.close()

    print(f"{len(brands_data)} records attempted for insertion into dim_brands.")

except Exception as e:
    print(f"Error inserting data: {e}")
