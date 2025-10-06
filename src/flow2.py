from langgraph.graph import StateGraph, START, END
from langchain_google_genai import ChatGoogleGenerativeAI
import sqlite3
import pandas as pd
import os
from dotenv import load_dotenv
from typing import TypedDict,Literal
from pydantic import BaseModel,Field
 
load_dotenv()
model = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    google_api_key=os.getenv("GEMINI_API_KEY")
)
DB_PATH = "hr_analytics.sqlite"
 
def get_connection():
    """Return a connection to the local SQLite DB."""
    return sqlite3.connect(DB_PATH)
 
def get_table_schema(conn, table_name="employees"):
    """Return list of tuples: (column_name, data_type)"""
    cursor = conn.execute(f"PRAGMA table_info({table_name});")
    return [(row[1], row[2]) for row in cursor.fetchall()]
 
 
class SQLState(TypedDict):
    user_query: str
    sql_query: str
    query_result: str
    feedback: str
    validation: Literal["valid", "invalid"]
 
class validationSchema(BaseModel):
    validation: Literal["valid", "invalid"] = Field(
        description="Indicates whether the SQL query is valid or invalid."
    )
 
structuredModel1=model.with_structured_output(validationSchema)
 
def get_user_Query(state: SQLState):
    cleaned_query = state["user_query"].strip().lower()
    return {"user_query": cleaned_query}
 
def generate_sql_query(state: SQLState):
    conn = get_connection()
    schema_info = get_table_schema(conn, "employees")
    conn.close()
 
    """
    Generate SQL query from user natural language input using Gemini.
    """
    # Convert schema to string for GPT prompt
    schema_str = ", ".join([f"{col} {dtype}" for col, dtype in schema_info])
 
    prompt = f"""
    You are an HR analytics assistant.
    Database schema:
    {schema_str}
 
    User query:
    {state['user_query']}
 
    Task:
    Generate a valid SQL query for the above database schema.
    Only return SQL, no explanation.
    """
 
    response = model.invoke(prompt)
   
    # ROBUST CLEANING
    import re
    sql_query = response.content.strip()  # remove leading/trailing whitespace
   
    # Remove markdown code blocks
    sql_query = re.sub(r'^```sql\s*', '', sql_query, flags=re.IGNORECASE)
    sql_query = re.sub(r'^```\s*', '', sql_query)
    sql_query = re.sub(r'```$', '', sql_query)
   
    # Remove common prefixes
    sql_query = re.sub(r'^\s*sql\s*', '', sql_query, flags=re.IGNORECASE)
    sql_query = re.sub(r'^\s*sqlite\s*', '', sql_query, flags=re.IGNORECASE)
   
    # Remove trailing semicolon
    sql_query = sql_query.rstrip('; \n\t')
   
    return {"sql_query": sql_query}
 
 
def validate_sql_query(state: SQLState):
    """
    Validate the generated SQL query using Gemini.
    """
    prompt = f"""
    You are an expert SQL validator.
    Here is a SQL query:
    {state['sql_query']}
 
    Task:
    Check if the SQL query is valid.
    Respond with "valid" or "invalid" only.
    """
 
    # Call Gemini with structured output
    response = structuredModel1.invoke(prompt)
    validation = response.validation  # should be "valid" or "invalid"
 
    # Update workflow state
    return {"validation": validation}
 
def route_validation(state: SQLState):
    """
    Route based on validation result.
    Must return 'valid' or 'invalid' to match edges.
    """
    return state["validation"]
 
def get_feedback(state: SQLState):
    """
    Get user feedback on the SQL query result.
    """
    prompt = f"""
    The SQL query executed was:
    {state['sql_query']}
 
    The result of the query is:
    {state['query_result']}
 
    Please provide feedback on whether this result answers your original question:
    {state['user_query']}
    """
 
    response = model.invoke(prompt)
    feedback = response.content.strip()
 
    return {"feedback": feedback}
 
def execute_sql_query(state: SQLState):
    """
    Execute the generated SQL query and return the results.
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(state["sql_query"])
        rows = cursor.fetchall()
        # Convert rows to a string representation
        result_str = "\n".join([str(row) for row in rows])
    except Exception as e:
        result_str = f"Error executing query: {e}"
    finally:
        conn.close()
 
    return {"query_result": result_str}
 
graph =StateGraph(SQLState)
 
graph.add_node('get_user_Query',get_user_Query)
graph.add_node('generate_sql_query',generate_sql_query)
graph.add_node('valiadate_sql_query',validate_sql_query)
graph.add_node('get_feedback',get_feedback)
graph.add_node('execute_sql_query',execute_sql_query)
 
graph.add_edge(START, 'get_user_Query')
graph.add_edge('get_user_Query', 'generate_sql_query')
graph.add_edge('generate_sql_query', 'valiadate_sql_query')
graph.add_conditional_edges(
    'valiadate_sql_query',
    route_validation,  # returns "valid" or "invalid"
    {
        "valid": "execute_sql_query",
        "invalid": "get_feedback",
    },
)
 
# Loop feedback back into generation
graph.add_edge('get_feedback', 'generate_sql_query')
graph.add_edge('execute_sql_query', END)
 
workflow = graph.compile()
from IPython.display import Image
Image(workflow.get_graph().draw_mermaid_png())