# src/create_knowledge_base.py
import json
import chromadb
import os
import sys

# Add parent directory to path to import from data folder
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def create_knowledge_base():
    # Load your metadata from data folder
    metadata_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'indian_deserts.json')
    
    with open(metadata_path) as f:
        metadata = json.load(f)
    
    # Initialize ChromaDB - store in project root
    chroma_path = os.path.join(os.path.dirname(__file__), '..', 'chroma_db')
    client = chromadb.PersistentClient(path=chroma_path)
    collection = client.get_or_create_collection(name="schema_knowledge_base")
    
    documents = []
    metadatas = []
    ids = []
    
    table_info = metadata["indian_desserts"]
    
    # Create documents for each column with rich descriptions
    for col_name, col_info in table_info["columns"].items():
        doc_text = f"""
        Table: indian_desserts
        Column: {col_name}
        Type: {col_info['type']}
        Description: {col_info['description']}
        Examples: {col_info['examples']}
        Business Domain: Food, Desserts, Indian Cuisine
        """
        
        documents.append(doc_text)
        metadatas.append({
            "table": "indian_desserts",
            "column": col_name,
            "type": col_info['type'],
            "domain": "Food/Desserts"
        })
        ids.append(f"indian_desserts_{col_name}")
    
    # Add a general table document
    table_doc = f"""
    Table: indian_desserts
    Description: {table_info['table_description']}
    Contains information about traditional Indian desserts, their ingredients, 
    preparation and cooking times, flavor profiles, and geographical regions.
    Business Domain: Food, Desserts, Indian Cuisine, Recipes
    Common Queries: Find desserts by region, filter by preparation time, 
    search by ingredients, find quick desserts, locate desserts by state.
    """
    
    documents.append(table_doc)
    metadatas.append({
        "table": "indian_desserts", 
        "column": "all",
        "type": "table",
        "domain": "Food/Desserts"
    })
    ids.append("indian_desserts_table")
    
    # Add to collection
    collection.add(
        documents=documents,
        metadatas=metadatas,
        ids=ids
    )
    
    print("✅ Knowledge base created successfully!")
    print(f"📍 Location: {chroma_path}")
    print(f"📊 Documents added: {len(documents)}")

if __name__ == "__main__":
    create_knowledge_base()