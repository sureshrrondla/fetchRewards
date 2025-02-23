import json
import pandas as pd
import uuid
import psycopg2
from psycopg2.extras import execute_batch

# 📌 PostgreSQL Connection Details
db_params = {
    "dbname": "fetchRewards",
    "user": "postgres",
    "password": "<password>",
    "host": "localhost",
    "port": "5432"
}

# Default UUIDs for missing values
DEFAULT_USER_ID = "00000000-0000-0000-0000-000000000000"
DEFAULT_BRAND_ID = "00000000-0000-0000-0000-000000000000"

# Function to validate and format UUID
def validate_uuid(value):
    try:
        return str(uuid.UUID(value))  # Convert to valid UUID
    except (ValueError, TypeError):
        return None  # Return None if invalid

# Function to safely extract timestamps
def extract_timestamp(value):
    if isinstance(value, dict) and "$date" in value:
        return pd.to_datetime(value["$date"], unit="ms")
    return None  # Return None if the value is not valid

# Load JSON data
def load_json_data(file_path):
    data = []
    with open(file_path, 'r') as file:
        for line in file:
            try:
                data.append(json.loads(line.strip()))
            except json.JSONDecodeError as e:
                print(f"Error decoding JSON: {e}")
    return pd.DataFrame(data)

# Fetch valid user IDs from dim_users
def get_valid_user_ids():
    conn = psycopg2.connect(**db_params)
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM dim_users;")
    valid_users = {row[0] for row in cursor.fetchall()}  # Set for quick lookup
    cursor.close()
    conn.close()
    return valid_users

# Fetch valid brand IDs from dim_brands
def get_valid_brand_ids():
    conn = psycopg2.connect(**db_params)
    cursor = conn.cursor()
    cursor.execute("SELECT brand_id FROM dim_brands;")
    valid_brands = {row[0] for row in cursor.fetchall()}  # Set for quick lookup
    cursor.close()
    conn.close()
    return valid_brands

# Process receipts data
def process_receipts_data(df, valid_user_ids, valid_brand_ids):
    receipts_data = []
    receipt_items_data = []

    for _, row in df.iterrows():
        try:
            # 🔹 Ensure `receipt_id` is never NULL
            receipt_id = None
            if isinstance(row.get("_id"), dict) and "$oid" in row["_id"]:
                receipt_id = validate_uuid(row["_id"]["$oid"])
            if not receipt_id:
                receipt_id = str(uuid.uuid4())  # Generate a new UUID if missing
                print(f"⚠️ Missing or invalid `_id`. Generated new UUID: {receipt_id}")

            receipt_user_id = validate_uuid(row.get("userId"))
            if not receipt_user_id or receipt_user_id not in valid_user_ids:
                print(f"⚠️ Receipt {receipt_id} has an unknown user {receipt_user_id}. Assigning to default user.")
                receipt_user_id = DEFAULT_USER_ID

            purchase_timestamp = extract_timestamp(row.get("purchaseDate"))
            scanned_date = extract_timestamp(row.get("dateScanned"))
            processing_finished_date = extract_timestamp(row.get("finishedDate"))
            points_awarded_timestamp = extract_timestamp(row.get("pointsAwardedDate"))

            total_amount_spent = float(row.get("totalSpent") or 0.0)
            items_purchased_count = int(float(row.get("purchasedItemCount") or 0))
            reward_points_earned = int(float(row.get("pointsEarned") or 0))
            extra_bonus_points = int(float(row.get("bonusPointsEarned") or 0))
            receipt_status = row.get("rewardsReceiptStatus", "UNKNOWN")

            receipts_data.append((
                receipt_id, receipt_user_id, purchase_timestamp, scanned_date,
                processing_finished_date, receipt_status, total_amount_spent,
                items_purchased_count, reward_points_earned, extra_bonus_points,
                points_awarded_timestamp
            ))

            # Process receipt items
            if isinstance(row.get("rewardsReceiptItemList"), list):
                for item in row["rewardsReceiptItemList"]:
                    try:
                        item_id = str(uuid.uuid4())
                        item_receipt_id = receipt_id
                        item_brand_id = validate_uuid(item.get("partnerItemId"))

                        if not item_brand_id or item_brand_id not in valid_brand_ids:
                            print(f"⚠️ Receipt item {item_id} has an unknown brand {item_brand_id}. Assigning default brand.")
                            item_brand_id = DEFAULT_BRAND_ID  

                        item_barcode = item.get("barcode", None)
                        item_quantity = int(float(item.get("quantityPurchased") or 1))
                        item_price = float(item.get("finalPrice") or 0.00)

                        receipt_items_data.append((
                            item_id, item_receipt_id, item_brand_id, item_barcode, item_quantity, item_price
                        ))
                    except Exception as e:
                        print(f"Skipping receipt item due to error: {e}")

        except Exception as e:
            print(f"Skipping receipt due to error: {e}")

    return receipts_data, receipt_items_data

# Insert data into PostgreSQL
def insert_data(table_name, data, query):
    if not data:
        print(f"⚠️ No data to insert into {table_name}.")
        return

    conn = psycopg2.connect(**db_params)
    cursor = conn.cursor()

    try:
        print(f"🔹 Attempting to insert {len(data)} records into {table_name}...")
        execute_batch(cursor, query, data)
        conn.commit()
        print(f"✅ Successfully inserted {len(data)} records into {table_name}.")
    except Exception as e:
        conn.rollback()
        print(f"❌ Error inserting into {table_name}: {e}")
    
    cursor.close()
    conn.close()

# Load and process receipts.json
receipts_df = load_json_data("receipts.json")
valid_user_ids = get_valid_user_ids()
valid_brand_ids = get_valid_brand_ids()
receipts_data, receipt_items_data = process_receipts_data(receipts_df, valid_user_ids, valid_brand_ids)

# DEBUG: Check extracted receipts data
print(f"🔍 Extracted {len(receipts_data)} receipts and {len(receipt_items_data)} receipt items before insertion.")

# Insert receipts
insert_data("fact_receipts", receipts_data, """
    INSERT INTO fact_receipts (receipt_id, receipt_user_id, purchase_timestamp, scanned_date,
        processing_finished_date, receipt_status, total_amount_spent, items_purchased_count,
        reward_points_earned, extra_bonus_points, points_awarded_timestamp)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    ON CONFLICT (receipt_id) DO NOTHING;
""")

# Insert receipt items
insert_data("fact_receipt_items", receipt_items_data, """
    INSERT INTO fact_receipt_items (receipt_item_id, item_receipt_id, item_brand_id, item_barcode,
        item_quantity, item_price)
    VALUES (%s, %s, %s, %s, %s, %s)
    ON CONFLICT (receipt_item_id) DO NOTHING;
""")
