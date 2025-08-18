# create_db_with_batches.py
import os
os.environ["CHROMA_TELEMETRY_ENABLED"] = "FALSE"

import pandas as pd
import chromadb

import shutil
import logging
import sys
import tqdm  # Import the progress bar library

# Configure logging to be very verbose
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    stream=sys.stdout,
)

# --- IMPORTANT: Ensure you have the required libraries ---
# pip install pandas chromadb "langchain-community>=0.2.7" "langchain-ollama>=0.3.2" tqdm
try:
    from langchain_community.embeddings import OllamaEmbeddings
except ImportError:
    logging.error("Required libraries not found.")
    logging.error("Please run: pip install pandas chromadb 'langchain-community>=0.2.7' 'langchain-ollama>=0.3.2' tqdm")
    sys.exit(1)


# --- Configuration ---
CSV_FILE = "dqrules.csv"
DB_PATH = "chroma_db_dq_rules"
COLLECTION_NAME = "dq_rulebook_collection"
EMBEDDING_MODEL = "nomic-embed-text"
BATCH_SIZE = 32  # Process 32 documents at a time. You can adjust this.

def create_database_in_batches():
    """
    Reads the CSV, generates embeddings in batches with a progress bar,
    and populates a new ChromaDB database.
    """
    # 1. --- Pre-flight Check: Verify CSV exists ---
    if not os.path.exists(CSV_FILE):
        logging.error(f"FATAL: The rules file '{CSV_FILE}' was not found in this directory.")
        return

    logging.info(f"Found rules file: {CSV_FILE}")

    # 2. --- Clean Slate: Remove old database ---
    if os.path.exists(DB_PATH):
        logging.warning(f"Removing existing database at '{DB_PATH}' for a clean build.")
        shutil.rmtree(DB_PATH)

    # 3. --- Load and Process Data ---
    try:
        df_rules = pd.read_csv(CSV_FILE)
        logging.info(f"Loaded {len(df_rules)} rows from CSV.")
        
        df_rules.columns = [
            'Domain', 'SAP_Module', 'Data_Type', 'Rule_ID', 
            'Description', 'Quality_Dimension', 'Attribute_Group'
        ]
        df_rules['Rule_ID'] = df_rules['Rule_ID'].astype(str)
        df_rules.dropna(subset=['Domain', 'Rule_ID', 'Description'], inplace=True)
        total_docs = len(df_rules)
        logging.info(f"After cleaning, preparing to process {total_docs} valid rules.")

        documents, metadatas, ids = [], [], []
        for index, row in df_rules.iterrows():
            doc_text = (
                f"Rule for {row['Domain']}. "
                f"Category: {row['Attribute_Group']}. "
                f"Description: {row['Description']}"
            )
            documents.append(doc_text)
            metadatas.append(row.to_dict())
            ids.append(f"rule_row_{index}")
            
    except Exception as e:
        logging.error(f"Error processing CSV file: {e}", exc_info=True)
        return

    # 4. --- Initialize Models and DB ---
    try:
        logging.info(f"Initializing embedding model: {EMBEDDING_MODEL} (Ollama)")
        embedding_model = OllamaEmbeddings(model=EMBEDDING_MODEL)

        client = chromadb.PersistentClient(path=DB_PATH)
        collection = client.get_or_create_collection(name=COLLECTION_NAME)
        logging.info(f"ChromaDB client initialized. Collection '{COLLECTION_NAME}' is ready.")
        
    except Exception as e:
        logging.error(f"Failed to initialize models or ChromaDB. Is your Ollama server running?", exc_info=True)
        return

    # 5. --- Generate Embeddings and Add to DB IN BATCHES ---
    try:
        logging.info(f"--- STARTING BATCH EMBEDDING for {total_docs} documents ---")
        
        # This loop processes the documents in chunks of BATCH_SIZE
        # tqdm creates the visual progress bar
        for i in tqdm.tqdm(range(0, total_docs, BATCH_SIZE), desc="Embedding Batches"):
            # Get the slice for the current batch
            batch_documents = documents[i:i + BATCH_SIZE]
            batch_metadatas = metadatas[i:i + BATCH_SIZE]
            batch_ids = ids[i:i + BATCH_SIZE]

            # Embed only this smaller batch
            batch_embeddings = embedding_model.embed_documents(batch_documents)

            # Add this batch to the collection immediately
            collection.add(
                embeddings=batch_embeddings,
                documents=batch_documents,
                metadatas=batch_metadatas,
                ids=batch_ids
            )
        
        logging.info("--- EMBEDDING AND DATABASE POPULATION COMPLETE ---")

    except Exception as e:
        logging.error(f"An error occurred during batch processing: {e}", exc_info=True)
        logging.error("Check if your Ollama server is still running.")
        return

    # 6. --- Final Verification ---
    count = collection.count()
    logging.info(f"Verification: Collection now contains {count} items.")
    if count == total_docs:
        logging.info(f"\n✅ SUCCESS! Database created at '{DB_PATH}' with {count} rules.")
    else:
        logging.warning(f"Mismatch in counts. Expected {total_docs} but found {count}.")


if __name__ == "__main__":
    create_database_in_batches()