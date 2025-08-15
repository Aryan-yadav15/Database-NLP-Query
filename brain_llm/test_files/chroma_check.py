import chromadb
from chromadb.config import Settings as ChromaSettings # If you use specific settings
import os

# --- Configuration ---
# Option 1: If your chroma_db directory is in the same folder as this script
CHROMA_DB_RELATIVE_PATH = './chroma_db_pg_adventureworks' # Or your specific relative path
# Get the absolute path to ensure it's correct regardless of where you run the script from
CHROMA_DB_ABSOLUTE_PATH = os.path.abspath(CHROMA_DB_RELATIVE_PATH)

# Option 2: If you know the absolute path
# CHROMA_DB_ABSOLUTE_PATH = '/path/to/your/project/api_2_rag_llm_service/chroma_db_pg_adventureworks'
# CHROMA_DB_ABSOLUTE_PATH = 'C:\\path\\to\\your\\project\\api_2_rag_llm_service\\chroma_db_pg_adventureworks'

print(f"Attempting to connect to ChromaDB at: {CHROMA_DB_ABSOLUTE_PATH}")

try:
    # Initialize the ChromaDB client
    # If you used specific client settings when creating the DB (like anonymized_telemetry=False),
    # include them here too.
    client = chromadb.PersistentClient(
        path=CHROMA_DB_ABSOLUTE_PATH,
        settings=ChromaSettings(anonymized_telemetry=False) # Optional: if you used it
    )

    print("\n--- ChromaDB Client Initialized Successfully ---")

    # List all collections
    collections = client.list_collections()

    if not collections:
        print("\nNo collections found in this ChromaDB instance.")
    else:
        print(f"\nFound {len(collections)} collection(s):")
        for i, collection_obj in enumerate(collections):
            print(f"\n--- Collection #{i+1} ---")
            print(f"Name: {collection_obj.name}")
            print(f"ID: {collection_obj.id}")
            print(f"Metadata: {collection_obj.metadata}")

            # Get the collection to inspect its count and peek at data
            try:
                current_collection = client.get_collection(name=collection_obj.name)
                count = current_collection.count()
                print(f"Document Count: {count}")

                if count > 0:
                    print(f"Peeking at up to 2 documents from '{collection_obj.name}':")
                    peek_data = current_collection.peek(limit=2) # Shows IDs, embeddings (if asked), metadatas, documents
                    # For more specific data:
                    # peek_data = current_collection.get(limit=2, include=['documents', 'metadatas'])

                    if peek_data and peek_data.get('ids'):
                        for j in range(len(peek_data['ids'])):
                            print(f"  Document ID: {peek_data['ids'][j]}")
                            if peek_data.get('metadatas') and len(peek_data['metadatas']) > j:
                                print(f"  Metadata: {peek_data['metadatas'][j]}")
                            if peek_data.get('documents') and len(peek_data['documents']) > j:
                                doc_preview = peek_data['documents'][j]
                                print(f"  Document (preview): {doc_preview[:100] + '...' if len(doc_preview) > 100 else doc_preview}")
                            print("-" * 20)
                    else:
                        print("  Could not peek into the collection (or it's empty despite count > 0, which is unusual).")
                else:
                    print(f"  Collection '{collection_obj.name}' is empty.")
            except Exception as e_get_coll:
                print(f"  Error getting details for collection '{collection_obj.name}': {e_get_coll}")

except Exception as e:
    print(f"\nAn error occurred: {e}")
    print("Please ensure:")
    print(f"1. The ChromaDB path '{CHROMA_DB_ABSOLUTE_PATH}' is correct and the database directory exists.")
    print("2. You have the necessary permissions to access the directory.")
    print("3. The chromadb library is installed in your Python environment.")

print("\n--- Script Finished ---")