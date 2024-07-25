from langchain_community.document_loaders import DirectoryLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
import openai 
from dotenv import load_dotenv
import os
import shutil

# Load environment variables. Assumes that project contains .env file with API keys
load_dotenv()
# Set OpenAI API key
openai.api_key = os.environ["OPENAI_API_KEY"]

CHROMA_PATH = "rag_files"
SKILLS_PATH = "skills"

def load_skills_folder():
    # Create the skills folder
    skills_folder_path = os.path.join(os.getcwd(), "skills")
    os.makedirs(skills_folder_path, exist_ok=True)

    # Load the contents of the skills folder and add them to the vector database
    documents = load_documents()
    print(f"Loaded {len(documents)} documents from {SKILLS_PATH}")
    chunks = split_text(documents)
    print(f"Split {len(documents)} documents into {len(chunks)} chunks.")
    save_to_chroma(chunks)

def load_documents():
    loader = DirectoryLoader(SKILLS_PATH, glob="*.py")
    documents = loader.load()
    print(f"Loaded {len(documents)} documents from {SKILLS_PATH}")
    return documents

def split_text(documents: list[Document]):
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=5000,
        chunk_overlap=0,
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
    db = Chroma.from_documents(
        chunks, OpenAIEmbeddings(), persist_directory=CHROMA_PATH
    )
    db.persist()
    print(f"Saved {len(chunks)} chunks to {CHROMA_PATH}.")

# Load the skills folder and add contents to the vector database
load_skills_folder()
