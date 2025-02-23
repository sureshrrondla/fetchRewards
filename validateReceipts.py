import json
import pandas as pd
import uuid
from datetime import datetime

# Function to load JSON safely (Handles NDJSON & standard JSON)
def load_json_data(file_path):
    data = []
    with open(file_path, 'r') as file:
        first_char = file.read(1)  # Check first character to detect format
        file.seek(0)  # Reset file read position

        if first_char == "[":  # Standard JSON array
            data = json.load(file)
        else:  # NDJSON (one JSON object per line)
            for line in file:
                try:
                    data.append(json.loads(line.strip()))
                except json.JSONDecodeError as e:
                    print(f"Error decoding JSON: {e}")

    return pd.DataFrame(data)

# Function to parse MongoDB-style timestamps
def parse_mongo_date(date_field):
    """Converts MongoDB $date fields to datetime format."""
    if isinstance(date_field, dict) and "$date" in date_field:
        return pd.to_datetime(date_field["$date"], unit='ms')
    return None

# Function to separate receipts and receipt items
def separate_receipts_data(df):
    receipts_data = []
    receipt_items_data = []

    for _, row in df.iterrows():
        receipt_id = str(uuid.uuid4())  # Generate a unique receipt_id
        user_id = row.get("userId", None)

        # Extract and transform the main receipt data
        receipt_record = {
            "receipt_id": receipt_id,
            "user_id": user_id,
            "purchase_date": parse_mongo_date(row.get("purchaseDate")),
            "date_scanned": parse_mongo_date(row.get("dateScanned")),
            "finished_date": parse_mongo_date(row.get("finishedDate")),
            "rewards_receipt_status": row.get("rewardsReceiptStatus"),
            "total_spent": pd.to_numeric(row.get("totalSpent"), errors='coerce'),
            "purchased_item_count": pd.to_numeric(row.get("purchasedItemCount"), errors='coerce'),
            "points_earned": pd.to_numeric(row.get("pointsEarned"), errors='coerce'),
            "bonus_points_earned": pd.to_numeric(row.get("bonusPointsEarned"), errors='coerce'),
            "points_awarded_date": parse_mongo_date(row.get("pointsAwardedDate")),
        }
        receipts_data.append(receipt_record)

        # Extract receipt items
        if "rewardsReceiptItemList" in row and isinstance(row["rewardsReceiptItemList"], list):
            for item in row["rewardsReceiptItemList"]:
                receipt_item_record = {
                    "receipt_item_id": str(uuid.uuid4()),  # Unique ID for item
                    "receipt_id": receipt_id,  # FK to Receipts table
                    "brand_id": item.get("partnerItemId", None),
                    "barcode": item.get("barcode", None),
                    "quantity": pd.to_numeric(item.get("quantityPurchased"), errors='coerce'),
                    "price": pd.to_numeric(item.get("itemPrice"), errors='coerce'),
                }
                receipt_items_data.append(receipt_item_record)

    return pd.DataFrame(receipts_data), pd.DataFrame(receipt_items_data)

# Function to validate data quality issues
def validate_data(df):
    issues = {
        "missing_values": df.isna().sum().to_dict(),  # Count of missing values
        "incorrect_types": {},  # Track type errors
        "duplicate_records": df.duplicated().sum(),  # Count duplicates
    }

    # Check for incorrect data types
    expected_types = {
        "total_spent": float,
        "purchased_item_count": int,
        "points_earned": int,
        "bonus_points_earned": int,
    }
    for col, expected_type in expected_types.items():
        if col in df.columns:
            incorrect_rows = df[~df[col].apply(lambda x: isinstance(x, (expected_type, type(None))))].shape[0]
            if incorrect_rows > 0:
                issues["incorrect_types"][col] = incorrect_rows

    return issues

# Load and process the data
receipts_df = load_json_data("receipts.json")
receipts_data, receipt_items_data = separate_receipts_data(receipts_df)

# Validate and print data quality issues
receipt_issues = validate_data(receipts_data)
receipt_item_issues = validate_data(receipt_items_data)

print("Receipts Data Quality Issues:", receipt_issues)
print("Receipt Items Data Quality Issues:", receipt_item_issues)
