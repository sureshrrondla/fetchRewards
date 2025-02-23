# 📜 Receipts Data Quality Report

## 📝 Overview
This report documents the **data quality issues** identified while processing the **Receipts (`fact_receipts`)** and **Receipt Items (`fact_receipt_items`)** datasets. The issues were found during **data extraction, validation, and insertion into PostgreSQL**.

---

## ⚠️ Summary of Data Quality Issues

### 🛒 **Receipts Table (`fact_receipts`)**
| Issue Type         | Column                 | Occurrences | Description |
|--------------------|-----------------------|------------|-------------|
| **Missing Values** | `purchase_date`        | 448        | Missing purchase timestamp. |
|                   | `finished_date`        | 551        | Processing finished timestamp missing. |
|                   | `total_spent`          | 435        | No total amount recorded for receipts. |
|                   | `purchased_item_count` | 484        | Missing number of items purchased. |
|                   | `points_earned`        | 510        | No points awarded for receipt. |
|                   | `bonus_points_earned`  | 575        | No bonus points recorded. |
|                   | `points_awarded_date`  | 582        | Points awarded timestamp missing. |
| **Incorrect Data Types** | `purchased_item_count` | 1119  | Stored as a **string** instead of an **integer**. |
|                   | `points_earned`        | 1119       | Stored as **string** instead of **integer**. |
|                   | `bonus_points_earned`  | 1119       | Stored as **string** instead of **integer**. |
| **Duplicate Records** | -                     | 0          | No duplicate receipts found. |

---

### 🏷️ **Receipt Items Table (`fact_receipt_items`)**
| Issue Type         | Column       | Occurrences | Description |
|--------------------|-------------|------------|-------------|
| **Missing Values** | `barcode`    | 3851       | Item barcode missing, unable to link product. |
|                   | `quantity`   | 174        | No quantity specified for the receipt item. |
|                   | `price`      | 174        | Missing price per unit for an item. |
| **Incorrect Data Types** | -       | 0          | No incorrect types found. |
| **Duplicate Records** | -         | 0          | No duplicate items found. |

---

## 🔍 Additional Issues & Fixes

### 1️⃣ `receipt_id` Missing or Invalid
**Issue:** Some rows had missing or invalid `_id` values.  
✅ **Fix:** Generated a new **UUID** when `_id` was missing or invalid.

### 2️⃣ `userId` Missing or Invalid
**Issue:** Some receipts had an **unknown or missing** `userId`.  
✅ **Fix:** Assigned **DEFAULT_USER_ID** → `"00000000-0000-0000-0000-000000000000"`.

### 3️⃣ `brandId` Missing or Invalid
**Issue:** Some receipt items had an **unknown brand** (`partnerItemId`).  
✅ **Fix:** Assigned **DEFAULT_BRAND_ID** → `"00000000-0000-0000-0000-000000000000"`.

### 4️⃣ `NaN` Values in Numeric Columns
**Issue:** Some numeric fields contained **NaN (null values)**.  
✅ **Fix:** Replaced **NaN with `0`** for:
   - `purchased_item_count`
   - `points_earned`
   - `bonus_points_earned`
   - `total_spent`
   - `quantity`
   - `price`

### 5️⃣ Incorrect Data Types
**Issue:** Some fields were stored as **strings instead of numbers**.  
✅ **Fix:** Converted:
   - `purchased_item_count` → `INTEGER`
   - `points_earned` → `INTEGER`
   - `bonus_points_earned` → `INTEGER`

### 6️⃣ Foreign Key Constraint Violations
**Issue:** Some `receipt_user_id` values didn't exist in `dim_users`.  
✅ **Fix:** Before inserting `fact_receipts`, checked **valid users** in `dim_users`.

**Issue:** Some `item_brand_id` values didn’t exist in `dim_brands`.  
✅ **Fix:** Before inserting `fact_receipt_items`, checked **valid brands** in `dim_brands`.

---

## 📌 Final Data Cleaning & Insertion Fixes

### ✅ Data Cleaning Steps Applied
1. **Ensured all `receipt_id` values were valid UUIDs.**
2. **Assigned default user (`DEFAULT_USER_ID`) if `userId` was missing.**
3. **Assigned default brand (`DEFAULT_BRAND_ID`) if `partnerItemId` was missing.**
4. **Replaced `NaN` values with `0` for numeric fields.**
5. **Converted incorrect string data types into proper numeric types.**
6. **Validated foreign keys (`receipt_user_id`, `item_brand_id`) before insertion.**

---

## 🛠️ Final Fixes in Database Insertions

### ✅ `fact_receipts` Insert Query
```sql
INSERT INTO fact_receipts (
    receipt_id, receipt_user_id, purchase_timestamp, scanned_date,
    processing_finished_date, receipt_status, total_amount_spent,
    items_purchased_count, reward_points_earned, extra_bonus_points,
    points_awarded_timestamp
)
VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
ON CONFLICT (receipt_id) DO NOTHING;
```

### ✅ fact_receipt_items Insert Query
```sql
INSERT INTO fact_receipt_items (
    receipt_item_id, item_receipt_id, item_brand_id, item_barcode,
    item_quantity, item_price
)
VALUES (%s, %s, %s, %s, %s, %s)
ON CONFLICT (receipt_item_id) DO NOTHING;
```

### 📌 Conclusion
✅ All major data quality issues have been identified and fixed.
✅ Default values have been used where necessary (DEFAULT_USER_ID, DEFAULT_BRAND_ID).
✅ NaN values have been replaced with valid numbers (0).
✅ Database insertions now work without errors or constraint violations.

🎯 The fact_receipts and fact_receipt_items tables are now correctly structured, clean, and ready for analytics!

