# 📝 Data Analysis Queries for Receipts & Brands

## 📝 Overview
This document contains SQL queries to analyze trends and insights based on `fact_receipts`, `fact_receipt_items`, `dim_users`, and `dim_brands`. These queries help track **top brands, spending behavior, and user interactions**.

---

## 📌 Schema Overview
The queries are based on the following schema:

### **dim_users**
Stores user details.
```sql
CREATE TABLE dim_users (
    user_id UUID PRIMARY KEY,
    user_state VARCHAR(2),
    account_created_date TIMESTAMP NOT NULL,
    last_login_date TIMESTAMP,
    user_role VARCHAR(20) DEFAULT 'consumer',
    is_active BOOLEAN DEFAULT TRUE
);
```

### **fact_receipts**
Stores information about scanned receipts.
```sql
CREATE TABLE fact_receipts (
    receipt_id UUID PRIMARY KEY,
    receipt_user_id UUID REFERENCES dim_users(user_id) ON DELETE CASCADE,
    purchase_timestamp TIMESTAMP NOT NULL,
    scanned_date TIMESTAMP NOT NULL,
    processing_finished_date TIMESTAMP,
    receipt_status VARCHAR(50) NOT NULL,
    total_amount_spent DECIMAL(10,2) DEFAULT 0.00 CHECK (total_amount_spent >= 0),
    items_purchased_count INTEGER DEFAULT 0 CHECK (items_purchased_count >= 0),
    reward_points_earned INTEGER DEFAULT 0 CHECK (reward_points_earned >= 0),
    extra_bonus_points INTEGER DEFAULT 0 CHECK (extra_bonus_points >= 0),
    points_awarded_timestamp TIMESTAMP
);
```

### **fact_receipt_items**
Stores details about items purchased on receipts.
```sql
CREATE TABLE fact_receipt_items (
    receipt_item_id UUID PRIMARY KEY,
    item_receipt_id UUID REFERENCES fact_receipts(receipt_id) ON DELETE CASCADE,
    item_brand_id UUID REFERENCES dim_brands(brand_id) ON DELETE SET NULL,
    item_barcode VARCHAR(50),
    item_quantity INTEGER DEFAULT 1 CHECK (item_quantity > 0),
    item_price DECIMAL(10,2) DEFAULT 0.00 CHECK (item_price >= 0)
);
```

### **dim_brands**
Stores brand-related information.
```sql
CREATE TABLE dim_brands (
    brand_id UUID PRIMARY KEY,
    brand_title VARCHAR(255) NOT NULL,
    brand_category VARCHAR(100),
    brand_category_code VARCHAR(50),
    brand_barcode VARCHAR(50),
    is_top_brand BOOLEAN DEFAULT FALSE
);
```

---

## **📊 Analysis Queries**

### **1️⃣ Top 5 Brands by Receipts Scanned for the Most Recent Month**
```sql
SELECT
    b.brand_title AS brand_name,
    COUNT(r.receipt_id) AS receipt_count
FROM fact_receipts r
JOIN fact_receipt_items ri ON r.receipt_id = ri.item_receipt_id
JOIN dim_brands b ON ri.item_brand_id = b.brand_id
WHERE DATE_TRUNC('month', r.scanned_date) = (
    SELECT DATE_TRUNC('month', MAX(scanned_date)) FROM fact_receipts
)
GROUP BY b.brand_title
ORDER BY receipt_count DESC
LIMIT 5;
```

### **2️⃣ Compare the Ranking of the Top 5 Brands for the Recent and Previous Month**
```sql
WITH recent_month AS (
    SELECT
        b.brand_title AS brand_name,
        COUNT(r.receipt_id) AS receipt_count,
        RANK() OVER (ORDER BY COUNT(r.receipt_id) DESC) AS rank_current
    FROM fact_receipts r
    JOIN fact_receipt_items ri ON r.receipt_id = ri.item_receipt_id
    JOIN dim_brands b ON ri.item_brand_id = b.brand_id
    WHERE DATE_TRUNC('month', r.scanned_date) = (
        SELECT DATE_TRUNC('month', MAX(scanned_date)) FROM fact_receipts
    )
    GROUP BY b.brand_title
    ORDER BY receipt_count DESC
    LIMIT 5
),
previous_month AS (
    SELECT
        b.brand_title AS brand_name,
        COUNT(r.receipt_id) AS receipt_count,
        RANK() OVER (ORDER BY COUNT(r.receipt_id) DESC) AS rank_previous
    FROM fact_receipts r
    JOIN fact_receipt_items ri ON r.receipt_id = ri.item_receipt_id
    JOIN dim_brands b ON ri.item_brand_id = b.brand_id
    WHERE DATE_TRUNC('month', r.scanned_date) = (
        SELECT DATE_TRUNC('month', MAX(scanned_date)) - INTERVAL '1 month' FROM fact_receipts
    )
    GROUP BY b.brand_title
    ORDER BY receipt_count DESC
    LIMIT 5
)
SELECT
    rm.brand_name,
    rm.rank_current AS recent_rank,
    pm.rank_previous AS previous_rank
FROM recent_month rm
LEFT JOIN previous_month pm ON rm.brand_name = pm.brand_name
ORDER BY recent_rank;
```

### **3️⃣ Compare Average Spend for Receipts with 'Accepted' vs. 'Rejected' Status**
```sql
SELECT
    receipt_status,
    AVG(total_amount_spent) AS avg_spend
FROM fact_receipts
WHERE receipt_status IN ('Accepted', 'Rejected')
GROUP BY receipt_status;
```

### **4️⃣ Compare Total Number of Items Purchased for 'Accepted' vs. 'Rejected' Receipts**
```sql
SELECT
    r.receipt_status,
    SUM(ri.item_quantity) AS total_items_purchased
FROM fact_receipts r
JOIN fact_receipt_items ri ON r.receipt_id = ri.item_receipt_id
WHERE r.receipt_status IN ('Accepted', 'Rejected')
GROUP BY r.receipt_status;
```

### **5️⃣ Brand with the Most Spend Among Users Created in the Past 6 Months**
```sql
SELECT
    b.brand_title AS brand_name,
    SUM(r.total_amount_spent) AS total_spend
FROM fact_receipts r
JOIN dim_users u ON r.receipt_user_id = u.user_id
JOIN fact_receipt_items ri ON r.receipt_id = ri.item_receipt_id
JOIN dim_brands b ON ri.item_brand_id = b.brand_id
WHERE u.account_created_date >= NOW() - INTERVAL '6 months'
GROUP BY b.brand_title
ORDER BY total_spend DESC
LIMIT 1;
```

### **6️⃣ Brand with the Most Transactions Among Users Created in the Past 6 Months**
```sql
SELECT
    b.brand_title AS brand_name,
    COUNT(r.receipt_id) AS total_transactions
FROM fact_receipts r
JOIN dim_users u ON r.receipt_user_id = u.user_id
JOIN fact_receipt_items ri ON r.receipt_id = ri.item_receipt_id
JOIN dim_brands b ON ri.item_brand_id = b.brand_id
WHERE u.account_created_date >= NOW() - INTERVAL '6 months'
GROUP BY b.brand_title
ORDER BY total_transactions DESC
LIMIT 1;
```
