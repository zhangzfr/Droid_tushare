# Manual Table Definition Guide (schema.py)

This guide explains how to manually add new DuckDB table structure definitions to the `src/tushare_duckdb/schema.py` file.

---

## 1. Why Define Manually?

While the system supports automatic generation from configurations, manual definition is recommended for:

- **Complex Data Types**: Tables with many non-primary key string fields (e.g., bank names, remarks).
- **Composite Primary Keys**: Defining uniqueness across multiple columns (e.g., `ts_code` + `ann_date`).
- **In-code Documentation**: Keeping field meanings in the code via comments.

---

## 2. Preparation

Before starting, ensure you have:

1. **Table Name**: e.g., `pledge_stat`.
2. **Field List**: All column names.
3. **Primary Key(s)**: The columns that uniquely identify a record.

---

## 3. Implementation Steps

### Step 1: Open the file

Location: `src/tushare_duckdb/schema.py`

### Step 2: Locate Insertion Point

Find the `TABLE_SCHEMAS = {` dictionary. Insert your new definition as a key-value pair.

### Step 3: Write the SQL Template

```python
    'table_name': """
        CREATE TABLE table_name (
            ts_code VARCHAR NOT NULL,   -- Stock Code
            trade_date VARCHAR NOT NULL, -- Trade Date
            close DOUBLE,                -- Close Price
            last_updated VARCHAR,        -- Reserved field for sync tracking
            PRIMARY KEY (ts_code, trade_date)
        )
    """,
```

---

## 4. Key Rules

| Item | Description | Advice |
| :--- | :--- | :--- |
| **Quotes** | SQL statements must be wrapped in `"""` (triple quotes). | Ensure proper indentation. |
| **VARCHAR** | String type. Use for dates, TS codes, and names. | Dates MUST be VARCHAR for consistency. |
| **DOUBLE** | Double-precision float. Use for all numeric data. | Preferred for financial metrics. |
| **PRIMARY KEY** | Uniqueness constraint. The system uses this for deduplication. | Crucial for `insert_new` mode. |

---

## 5. FAQ

**Q: I used the wrong type. How do I fix it?**
A: Changing `schema.py` won't update an existing table. You must `DROP TABLE table_name` in DuckDB first, then rerun the sync script.

**Q: Do I need the `last_updated` field?**
A: Highly recommended. The system automatically populates this with the synchronization timestamp.
