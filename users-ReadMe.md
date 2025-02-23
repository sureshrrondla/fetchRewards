# Data Quality Analysis for Users Dataset

## Overview
This project analyzes the data quality of a users dataset, identifying missing values, incorrect data types, and potential issues that could affect data integrity and analytics.

## Data Sources
The dataset consists of JSON files containing user information. The data is parsed and stored in the **Users Table**, which includes details such as user ID, state, account creation date, last login, role, and status.

---

## 🛠️ Data Quality Issues Identified
The analysis revealed several **data quality issues**, summarized below:

### 1️⃣ **Missing Values**
| Field | Missing Count | Impact |
|--------|--------------|--------|
| `last_login` | **62** | Some users have never logged in, making it difficult to track engagement. |

### 2️⃣ **Invalid Values**
| Field | Invalid Count | Impact |
|--------|--------------|--------|
| `state` | **87** | Some users have invalid or unrecognized state values, which affects regional analytics. |
| `role` | **82** | Some users have roles other than "consumer," which may affect role-based access or segmentation. |

---

## 🔍 How Were These Data Quality Issues Discovered?
A Python script was used to analyze the dataset for:
1. **Missing Values** – Checked for `NaN` or empty `last_login` fields.
2. **Invalid Data Entries** – Verified if `state` and `role` values match expected formats.

Example code snippet:
```python
missing_values = users_df.isnull().sum()
invalid_state_count = users_df[~users_df['state'].isin(valid_states)].shape[0]
invalid_role_count = users_df[users_df['role'].str.lower() != 'consumer'].shape[0]
```

---

## 🛠 Resolving Data Quality Issues
### **1️⃣ Handling Missing Values**
👉 **Imputation Strategies**
- `last_login`: If missing, default to `created_date` or flag users as "Inactive."

### **2️⃣ Fixing Invalid Values**
- **State Validation:** Replace invalid state values with "Unknown" or a default valid state.
- **Role Correction:** Convert all roles to "consumer" to ensure data consistency.

Example fix:
```python
users_df['state'] = users_df['state'].apply(lambda x: x if x in valid_states else 'Unknown')
users_df['role'] = 'consumer'  # Standardize role values
```

### **3️⃣ Performance & Scaling Considerations**
- **Preprocess JSON before loading into DB** to correct errors early.
- Use **batch processing** for large datasets.
- Implement **data validation checks** at the ingestion stage.

---

## 🔮 Next Steps
### **1️⃣ What Additional Information is Needed?**
- **State Standardization Rules**: Should missing `state` values be inferred or defaulted?
- **Role Classification**: Should any roles other than "consumer" exist in the dataset?

### **2️⃣ What Are the Next Steps for Optimization?**
- **Data Cleaning Pipeline**: Automate `last_login` imputation and role correction.
- **Database Constraints**: Enforce `NOT NULL` where applicable.
- **Logging & Monitoring**: Track errors in real-time for better data governance.

### **3️⃣ Future Performance Considerations**
- **Scalability**: JSON processing should be optimized for high-volume ingestion.
- **Storage Optimization**: Large missing value counts can bloat databases.
- **Query Speed**: Missing `last_login` affects engagement tracking.

---

## 📉 Conclusion
This analysis highlights key **data integrity issues** and proposes solutions for **data cleaning, transformation, and validation**. Addressing these problems will **improve user engagement tracking, consistency, and overall system performance**.

