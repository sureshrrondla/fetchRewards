# Data Warehouse Model for Receipts, Users, and Brands

## Overview
This document outlines the **relational data model** for structuring **Users, Receipts, and Brands** data in a **data warehouse**. The model is designed to support analytical queries efficiently by organizing data into **fact and dimension tables** with well-defined relationships.

---

## 📌 Table Schema and Column Details

### **1️⃣ `dim_users` (Users Table)**
| Column Name | Data Type | Description |
|-------------|-----------|-------------|
| `user_id` (PK) | UUID | Unique identifier for the user |
| `user_state` | VARCHAR(2) | State abbreviation where the user is located |
| `account_created_date` | TIMESTAMP | Date when the user account was created |
| `last_login_date` | TIMESTAMP | Last recorded login timestamp of the user |
| `user_role` | VARCHAR(20) | User role (e.g., 'consumer') |
| `is_active` | BOOLEAN | Whether the user account is active |

### **2️⃣ `fact_receipts` (Receipts Table)**
| Column Name | Data Type | Description |
|-------------|-----------|-------------|
| `receipt_id` (PK) | UUID | Unique identifier for the receipt |
| `receipt_user_id` (FK) | UUID | Foreign key linking to `dim_users.user_id` |
| `purchase_timestamp` | TIMESTAMP | Date and time when the purchase was made |
| `scanned_date` | TIMESTAMP | When the receipt was scanned by the user |
| `processing_finished_date` | TIMESTAMP | Date when the receipt processing was completed |
| `receipt_status` | VARCHAR(50) | Status of the receipt validation process |
| `total_amount_spent` | DECIMAL(10,2) | Total amount spent in the receipt |
| `items_purchased_count` | INTEGER | Number of items purchased in the receipt |
| `reward_points_earned` | INTEGER | Points earned for the purchase |
| `extra_bonus_points` | INTEGER | Additional bonus points awarded |
| `points_awarded_timestamp` | TIMESTAMP | Date when points were awarded |

### **3️⃣ `fact_receipt_items` (Receipt Items Table)**
| Column Name | Data Type | Description |
|-------------|-----------|-------------|
| `receipt_item_id` (PK) | UUID | Unique identifier for the receipt item |
| `item_receipt_id` (FK) | UUID | Foreign key linking to `fact_receipts.receipt_id` |
| `item_brand_id` (FK) | UUID | Foreign key linking to `dim_brands.brand_id` |
| `item_barcode` | VARCHAR(50) | Barcode of the purchased item |
| `item_quantity` | INTEGER | Number of units purchased for this item |
| `item_price` | DECIMAL(10,2) | Price per unit of the item |

### **4️⃣ `dim_brands` (Brands Table)**
| Column Name | Data Type | Description |
|-------------|-----------|-------------|
| `brand_id` (PK) | UUID | Unique identifier for the brand |
| `brand_title` | VARCHAR(255) | Brand name |
| `brand_category` | VARCHAR(100) | Category to which the brand belongs |
| `brand_category_code` | VARCHAR(50) | Category code for standardization |
| `brand_barcode` | VARCHAR(50) | Barcode associated with the brand |
| `is_top_brand` | BOOLEAN | Indicates if the brand is a featured 'top brand' |

---

## 🔗 Table Relationships
- **`fact_receipts.receipt_user_id`** → `dim_users.user_id` (**1-to-Many**)  
- **`fact_receipt_items.item_receipt_id`** → `fact_receipts.receipt_id` (**1-to-Many**)  
- **`fact_receipt_items.item_brand_id`** → `dim_brands.brand_id` (**Many-to-1**)  

This structure ensures **efficient querying and reporting** for insights like:
- **Total Spend per User**
- **Most Popular Brands**
- **Average Receipt Spend by State**

---

## 🛠️ Design Rationale
- **Separation of Facts & Dimensions:** Allows efficient queries for aggregations.
- **Primary & Foreign Keys:** Ensure referential integrity.
- **Denormalization in Fact Tables:** Improves performance for analytical workloads.

---

## 📌 Next Steps
### **1️⃣ Optimization & Indexing**
- Create **indexes on foreign keys** (`user_id`, `brand_id`, `receipt_id`).
- Consider **partitioning fact tables** for scalability.

### **2️⃣ Data Validation & Constraints**
- Ensure **`brand_code` is not NULL** in `dim_brands`.
- Enforce **referential integrity** between receipts and users.

### **3️⃣ ETL Pipeline Development**
- **Extract:** Load raw JSON data.
- **Transform:** Convert incorrect types, fill missing values.
- **Load:** Insert cleaned data into the warehouse.

---

## 📌 Conclusion
This data warehouse model is structured to ensure **efficient querying, data integrity, and scalability**. The combination of **fact and dimension tables** provides a solid foundation for reporting and analytics on **Users, Receipts, and Brands** data.

