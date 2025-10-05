from langgraph.graph import StateGraph, START, END
from langchain_google_genai import ChatGoogleGenerativeAI
from typing import TypedDict
import sqlite3
import json
import os
import re
from dotenv import load_dotenv

load_dotenv()

model = ChatGoogleGenerativeAI(
    model = 'gemini-2.5-flash',
    google_api_key = os.getenv('GEMINI_API_KEY')
)
# Assuming you have AgentState and model defined
class AgentState(TypedDict):
    user_query: str
    sql_query: str
    validation_passed: bool
    feedback: str
    result: str
    iteration_count: int  # NEW: Track iterations

# -----------------------------
# 1️⃣ Node 1 - Generate SQL (FIXED)
# -----------------------------
def generate_sql(state: AgentState):
    with open("indian_deserts.json") as f:
        metadata = json.load(f)

    table = "indian_desserts"
    schema_info = metadata[table]
    
    # Build richer schema description
    schema_desc = []
    for col_name, col_info in schema_info["columns"].items():
        schema_desc.append(
            f"- {col_name} ({col_info['type']}): {col_info['description']}"
        )
    schema_text = "\n".join(schema_desc)

    prompt = f"""
You are a SQL expert. Generate a valid SQLite query for the user's request.

**Table:** {table}
**Schema:**
{schema_text}

**User Query:** {state['user_query']}
**Validator Feedback:** {state.get('feedback', 'None')}

**CRITICAL INSTRUCTIONS:**
- Return ONLY the raw SQL query with NO extra text, explanations, or prefixes
- Do NOT include markdown code blocks or backticks
- Do NOT end the query with a semicolon
- Use proper SQLite syntax
- If feedback is provided, fix the issues mentioned
- **IMPORTANT: When asked about desserts, ALWAYS filter by course = 'dessert' to exclude main courses**

Example format: SELECT name, state FROM indian_desserts WHERE course = 'dessert' AND prep_time < 30
"""

    response = model.invoke(prompt)
    
    # IMPROVED CLEANING: Remove common LLM artifacts
    sql_query = response.content.strip()
    
    # Remove markdown code blocks
    sql_query = re.sub(r'^```sql\s*', '', sql_query, flags=re.IGNORECASE)
    sql_query = re.sub(r'^```\s*', '', sql_query)
    sql_query = re.sub(r'```$', '', sql_query)
    
    # Remove common prefixes
    sql_query = re.sub(r'^\s*sql\s*', '', sql_query, flags=re.IGNORECASE)
    sql_query = re.sub(r'^\s*sqlite\s*', '', sql_query, flags=re.IGNORECASE)
    
    # Remove trailing semicolon and whitespace
    sql_query = sql_query.rstrip('; \n\t')
    
    # Remove any leading non-SELECT text (like "ite")
    if not sql_query.upper().startswith('SELECT'):
        match = re.search(r'\bSELECT\b', sql_query, re.IGNORECASE)
        if match:
            sql_query = sql_query[match.start():]
    
    sql_query = sql_query.strip()

    print(f"\n🧠 Generated SQL (Iteration {state['iteration_count']}): {sql_query}")
    
    return {
        **state, 
        "sql_query": sql_query,
        "iteration_count": state["iteration_count"] + 1
    }

# -----------------------------
# 2️⃣ Node 2 - Validate SQL (FIXED)
# -----------------------------
def validate_sql(state: AgentState) -> AgentState:
    sql_query = state['sql_query']
    feedback = []
    validation_passed = True
    
    # Load metadata
    with open("indian_deserts.json") as f:
        metadata = json.load(f)
    
    valid_columns = set(metadata["indian_desserts"]["columns"].keys())
    
    # ------------------------------------------------
    # 1️⃣ Extract column names from SQL query (FIXED)
    # ------------------------------------------------
    try:
        select_match = re.search(r'SELECT\s+(.*?)\s+FROM', sql_query, re.IGNORECASE | re.DOTALL)
        
        if select_match:
            columns_str = select_match.group(1)
            
            # Handle SELECT *
            if columns_str.strip() == '*':
                extracted_columns = valid_columns  # All columns valid for SELECT *
                print(f"🔍 Extracted columns: * (all columns)")
            else:
                extracted_columns = set()
                for col in columns_str.split(','):
                    col_clean = col.strip().split()[0].strip('`"\'')
                    col_clean = re.sub(r'\w+\((.*?)\)', r'\1', col_clean).strip()
                    if col_clean and col_clean != '*':
                        extracted_columns.add(col_clean)
                print(f"🔍 Extracted columns: {extracted_columns}")
        else:
            extracted_columns = set()
            feedback.append("Could not parse SELECT clause")
            validation_passed = False
            
    except Exception as e:
        feedback.append(f"Failed to parse column names: {str(e)}")
        validation_passed = False
        extracted_columns = set()
    
    # ------------------------------------------------
    # 2️⃣ Validate column names
    # ------------------------------------------------
    invalid_columns = extracted_columns - valid_columns
    
    if invalid_columns:
        feedback.append(f"Invalid columns: {invalid_columns}. Valid: {valid_columns}")
        validation_passed = False
        print(f"❌ Invalid columns: {invalid_columns}")
    else:
        print(f"✅ All columns are valid")
    
    # ------------------------------------------------
    # 3️⃣ Dry run (FIXED - no semicolon before LIMIT)
    # ------------------------------------------------
    try:
        conn = sqlite3.connect("desserts.db")
        cursor = conn.cursor()
        
        # Add LIMIT only if not present
        test_query = sql_query.strip().rstrip(';')  # Remove trailing semicolon first
        if 'LIMIT' not in test_query.upper():
            test_query += " LIMIT 5"
        
        cursor.execute(test_query)
        results = cursor.fetchall()
        
        print(f"✅ Dry run successful. Sample: {results[:2] if results else 'No results'}")
        conn.close()
        
    except sqlite3.Error as e:
        feedback.append(f"SQL error: {str(e)}. Remove any semicolons and check syntax.")
        validation_passed = False
        print(f"❌ SQL Error: {str(e)}")
    
    # ------------------------------------------------
    # Return with feedback
    # ------------------------------------------------
    feedback_str = " | ".join(feedback) if feedback else "All validations passed"
    
    return {
        **state,
        "validation_passed": validation_passed,
        "feedback": feedback_str
    }

# -----------------------------
# 3️⃣ Node 3 - Execute SQL
# -----------------------------
def execute_sql(state: AgentState):
    conn = sqlite3.connect("desserts.db")
    cursor = conn.cursor()
    try:
        # Remove trailing semicolon before execution
        clean_query = state["sql_query"].strip().rstrip(';')
        cursor.execute(clean_query)
        rows = cursor.fetchall()
        result = rows if rows else "No results found."
        print("📊 Query Result:", result)
    except Exception as e:
        result = f"Execution Error: {e}"
        print(result)
    finally:
        conn.close()

    return {**state, "result": str(result)}

# -----------------------------
# 4️⃣ Conditional routing (FIXED - add max iterations)
# -----------------------------
def validation_check(state: AgentState):
    # CRITICAL: Prevent infinite loops
    MAX_ITERATIONS = 5
    
    if state["iteration_count"] >= MAX_ITERATIONS:
        print(f"⚠️ Max iterations ({MAX_ITERATIONS}) reached. Stopping.")
        return "execute_sql"  # Force execution even if invalid
    
    return "execute_sql" if state["validation_passed"] else "generate_sql"

# -----------------------------
# 5️⃣ Define Graph Structure
# -----------------------------
graph = StateGraph(AgentState)

graph.add_node("generate_sql", generate_sql)
graph.add_node("validate_sql", validate_sql)
graph.add_node("execute_sql", execute_sql)

graph.add_edge(START, "generate_sql")
graph.add_edge("generate_sql", "validate_sql")
graph.add_conditional_edges("validate_sql", validation_check)
graph.add_edge("execute_sql", END)

workflow = graph.compile()

# -----------------------------
# 6️⃣ Main execution
# -----------------------------
if __name__ == "__main__":
    print("🍰 Welcome to the Indian Desserts SQL Agent!")
    user_query = input("Enter your question: ")

    initial_state = {
        "user_query": user_query,
        "sql_query": "",
        "validation_passed": False,
        "feedback": "",
        "result": "",
        "iteration_count": 0  # NEW: Start at 0
    }

    result = workflow.invoke(initial_state)

    print("\n🎯 Final Query:", result["sql_query"])
    print("📈 Final Result:", result["result"])