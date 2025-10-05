import pandas as pd
import sqlite3

# Step 1: Read CSV into DataFrame
df = pd.read_csv("indian_food.csv")

# Step 2: Connect to SQLite (creates file if not exists)
conn = sqlite3.connect("desserts.db")

# Step 3: Write the DataFrame to a SQL table
df.to_sql("indian_desserts", conn, if_exists="replace", index=False)

# Step 4: Test - Read few rows back
test_df = pd.read_sql_query("SELECT * FROM indian_desserts LIMIT 5;", conn)
print(test_df)

# Step 5: Close connection (optional)
conn.close()

print("✅ CSV data successfully loaded into desserts.db!")
