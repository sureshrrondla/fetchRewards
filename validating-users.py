import json
import pandas as pd
import uuid
from datetime import datetime
from collections import defaultdict

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

# Function to process and validate users data
def process_users_data(df):
    users_data = []
    issues = defaultdict(int)

    for _, row in df.iterrows():
        user_id = row["_id"]["$oid"] if "_id" in row and "$oid" in row["_id"] else str(uuid.uuid4())  # Generate UUID if missing

        user_record = {
            "user_id": user_id,
            "state": row.get("state", None),
            "created_date": parse_mongo_date(row.get("createdDate")),
            "last_login": parse_mongo_date(row.get("lastLogin")),
            "role": row.get("role", None),
            "active": row.get("active", None),
            "sign_up_source": row.get("signUpSource", None),
        }
        users_data.append(user_record)

        # Validate fields
        if not user_record["user_id"]:
            issues["missing_user_id"] += 1
        if pd.isna(user_record["created_date"]):
            issues["missing_created_date"] += 1
        if pd.isna(user_record["last_login"]):
            issues["missing_last_login"] += 1
        if user_record["state"] not in ["AL", "AK", "AZ", "AR", "CA", "WI", None]:  # Example state validation
            issues["invalid_state"] += 1
        if user_record["role"] and user_record["role"].lower() != "consumer":
            issues["invalid_role"] += 1

    return pd.DataFrame(users_data), issues

# Load the data
users_df = load_json_data("users.json")

# Process and validate users data
users_data, issues_found = process_users_data(users_df)

# Print validation issues
print("Users Data Quality Issues:")
for issue, count in issues_found.items():
    print(f"{issue}: {count} occurrences")

# Display extracted user data
print("\nExtracted Users Data:")
print(users_data.head())
