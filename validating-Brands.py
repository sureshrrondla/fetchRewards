import json
import pandas as pd
import uuid
from collections import defaultdict

# Load JSON safely (Handles NDJSON & standard JSON)
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

# Process and validate brand data
def process_brands_data(df):
    brands_data = []
    issues = defaultdict(int)

    for _, row in df.iterrows():
        brand_id = row["_id"]["$oid"] if "_id" in row and "$oid" in row["_id"] else str(uuid.uuid4())

        brand_record = {
            "brand_id": brand_id,
            "name": row.get("name", None),
            "category": row.get("category", None),
            "category_code": row.get("categoryCode", None),
            "barcode": row.get("barcode", None),
            "brand_code": row.get("brandCode", None),
            "top_brand": row.get("topBrand", False),  # Default to False if missing
            "cpg_id": row["cpg"]["$id"]["$oid"] if "cpg" in row and "$id" in row["cpg"] and "$oid" in row["cpg"]["$id"] else None,
        }

        brands_data.append(brand_record)

        # Validate fields
        if not brand_record["brand_id"]:
            issues["missing_brand_id"] += 1
        if not brand_record["name"]:
            issues["missing_brand_name"] += 1
        if not brand_record["category"]:
            issues["missing_category"] += 1
        if not brand_record["category_code"]:
            issues["missing_category_code"] += 1
        if not brand_record["barcode"]:
            issues["missing_barcode"] += 1
        if not brand_record["brand_code"]:
            issues["missing_brand_code"] += 1
        if not brand_record["cpg_id"]:
            issues["missing_cpg_id"] += 1

    return pd.DataFrame(brands_data), issues

# Load the data
brands_df = load_json_data("brands.json")

# Process and validate brand data
brands_data, issues_found = process_brands_data(brands_df)

# Print validation issues
print("Brands Data Quality Issues:")
for issue, count in issues_found.items():
    print(f"{issue}: {count} occurrences")

# Display extracted brand data
print("\nExtracted Brands Data:")
print(brands_data.head())
