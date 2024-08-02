from langchain_community.document_loaders import DirectoryLoader, WebBaseLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from dotenv import load_dotenv
import os
import shutil

# Load environment variables
load_dotenv()

CHROMA_PATH = "db"
DOCS_PATH = "corpus"
URLS_FILE = "corpus/urls.txt"

def load_docs_folder():
    skills_folder_path = os.path.join(os.getcwd(), "corpus")
    os.makedirs(skills_folder_path, exist_ok=True)

    # Load and process documents
    documents = load_documents()
    chunks = split_text(documents)
    save_to_chroma(chunks)

def load_documents():
    # Load local documents
    local_loader = DirectoryLoader(DOCS_PATH, glob="*.*")
    local_documents = local_loader.load()
    print(f"Loaded {len(local_documents)} local documents from {DOCS_PATH}")

    # Load URLs
    url_documents = load_urls()
    
    # Combine local and URL documents
    all_documents = local_documents + url_documents
    print(f"Total documents loaded: {len(all_documents)}")
    return all_documents

def load_urls():
    if not os.path.exists(URLS_FILE):
        print(f"No {URLS_FILE} found. Skipping URL loading.")
        return []

    with open(URLS_FILE, 'r') as file:
        urls = [line.strip() for line in file if line.strip()]

    url_documents = []
    for url in urls:
        try:
            loader = WebBaseLoader(url)
            url_documents.extend(loader.load())
            print(f"Loaded content from: {url}")
        except Exception as e:
            print(f"Error loading {url}: {e}")

    print(f"Loaded {len(url_documents)} documents from URLs")
    return url_documents

def split_text(documents: list[Document]):
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        length_function=len,
        add_start_index=True,
    )
    chunks = text_splitter.split_documents(documents)
    print(f"Split {len(documents)} documents into {len(chunks)} chunks.")
    return chunks

def save_to_chroma(chunks: list[Document]):
    # Remove existing DB files
    if os.path.exists(CHROMA_PATH):
        shutil.rmtree(CHROMA_PATH)
    
    # Create a new DB from the documents
    embedding_function = OpenAIEmbeddings()
    db = Chroma.from_documents(
        chunks, embedding_function, persist_directory=CHROMA_PATH
    )
    db.persist()
    print(f"Saved {len(chunks)} chunks to {CHROMA_PATH}.")

if __name__ == "__main__":
    load_docs_folder()