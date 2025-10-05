# 🍨 Agentic SQL Assistant on Indian Desserts Data  

### 🚀 Intelligent LangGraph Workflow with Iterative SQL Validation  
**Done by: Person A & Person B**

---

## 🧠 Project Overview  

This project demonstrates an **agentic application** built using **LangGraph** and **Google Gemini (via `langchain-google-genai`)**, which allows natural language queries to be converted into SQL queries and executed against a **SQLite database**.  

The key highlight is its **iterative validation loop** — the system automatically detects and corrects invalid or hallucinated SQL queries using feedback from a validator node before execution.  

---

## ⚙️ Key Features  

- 🧩 **Agentic Workflow:** Uses LangGraph to orchestrate nodes for SQL generation, validation, and execution.  
- 🔁 **Iterative Feedback Loop:** Automatically regenerates SQL if validation fails (column mismatch or syntax error).  
- 🤖 **Google Gemini Integration:** Generates SQL queries from user intent.  
- 🗃️ **SQLite Integration:** Executes validated SQL queries on a local database (`desserts.db`).  
- 🧾 **Metadata Awareness:** Uses column-level metadata for schema validation.  
- 🧠 **LLM Guardrails:** Reduces hallucinations by enforcing schema-based constraints.  

---

## 🏗️ Architecture Overview  

### **Workflow Nodes**

| Node | Description |
|------|--------------|
| 🧠 **generate_sql** | Uses Gemini to generate (or regenerate) SQL from natural language input and feedback. |
| 🧩 **validate_sql** | Checks for column validity, schema correctness, and syntax. |
| ⚙️ **execute_sql** | Runs the validated query on the SQLite database. |
| 🏁 **END** | Outputs the final query results. |

---

### **Flowchart**

User Query
↓
generate_sql (Gemini)
↓
validate_sql (Schema & Syntax Checker)
↓
┌───────────────┐
│ SQL Valid ? │
└──────┬────────┘
│
Yes ↓ No
execute_sql ←───── regenerate_sql
↓
END

---

## 🗂️ Project Structure  

📂 agentic-sql-assistant/
│
├── desserts.db # SQLite database
├── indian_desserts_metadata.json # Metadata file (schema info)
├── agentic_sql_agent.py # Main workflow code
├── requirements.txt # Dependencies
└── README.md # Documentation

---


---

## 🧩 Metadata File Example (`indian_desserts_metadata.json`)

```json
{
  "table_name": "indian_desserts",
  "columns": {
    "name": {"type": "TEXT", "example": "Gulab Jamun"},
    "ingredients": {"type": "TEXT", "example": "Milk powder, sugar, ghee"},
    "diet": {"type": "TEXT", "example": "vegetarian"},
    "prep_time": {"type": "INTEGER", "example": 15},
    "cook_time": {"type": "INTEGER", "example": 30},
    "flavor_profile": {"type": "TEXT", "example": "sweet"},
    "course": {"type": "TEXT", "example": "dessert"},
    "state": {"type": "TEXT", "example": "West Bengal"},
    "region": {"type": "TEXT", "example": "East"}
  }
}
```

## 🧱 Tech Stack  

| Component | Library / Tool |
|------------|----------------|
| **LLM** | Google Gemini (`langchain-google-genai`) |
| **Workflow Engine** | LangGraph |
| **Database** | SQLite |
| **Language** | Python 3.10+ |
| **Data Source** | Indian Desserts Dataset (CSV → SQLite) |

---

## ⚙️ Installation  

### 1️⃣ Clone the Repository
```bash
git clone https://github.com/<your-username>/agentic-sql-assistant.git
cd agentic-sql-assistant
```

2️⃣ Install Dependencies
```bash
pip install -r requirements.txt
```

3️⃣ Create the SQLite Database (if not present)

```
import pandas as pd
import sqlite3

df = pd.read_csv("indian_desserts.csv")
conn = sqlite3.connect("desserts.db")
df.to_sql("indian_desserts", conn, if_exists="replace", index=False)
conn.close()
```

🚀 Running the Agent
Run the main workflow:
```
python agentic_sql_agent.py
```

Then, type your query:
```
Enter your question: Show all desserts from the North region.
```

Output Example:


🧠 Generated SQL: SELECT name FROM indian_desserts WHERE region='North';
✅ SQL Validated Successfully.
📊 Query Result: [('Gajar ka halwa',), ('Jalebi',), ('Phirni',)]
🎯 Final Result:
[('Gajar ka halwa',), ('Jalebi',), ('Phirni',)]

If SQL is invalid, the validator node automatically feeds back corrections and Gemini regenerates a new SQL query.


🔁 Example Iterative Correction
❌ First Attempt
```
SELECT name FROM indian_desserts WHERE area='North';
```

Error: Column area doesn’t exist.
🔁 Feedback to Gemini

Invalid column: area. Use column region instead.

✅ Regenerated Query
```
SELECT name FROM indian_desserts WHERE region='North';
```
