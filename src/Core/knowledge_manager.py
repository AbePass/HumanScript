from langchain_community.document_loaders import DirectoryLoader, WebBaseLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from dotenv import load_dotenv
import os
from Settings.config import *
import logging
import shutil

# Load environment variables
load_dotenv()

class KnowledgeManager:
    def __init__(self, root):
        self.root = root
        self.selected_kbs = []
        self.skills = {}  # {knowledge_base: [(skill_name, skill_path), ...]}
        self.instructions = {}

    def get_knowledge_bases(self):
        return [d for d in os.listdir(KB_PATH) if os.path.isdir(os.path.join(KB_PATH, d))]

    def update_selected_kbs(self, selected_kbs):
        # Remove skills and instructions from previously selected KBs
        previous_kbs = set(self.selected_kbs) - set(selected_kbs)
        for kb in previous_kbs:
            self.remove_skills(kb)
            self.remove_instructions(kb)
        
        # Add skills and instructions from newly selected KBs
        new_kbs = set(selected_kbs) - set(self.selected_kbs)
        for kb in new_kbs:
            self.load_skills_and_instructions(kb)
        
        self.selected_kbs = selected_kbs

    def remove_skills(self, knowledge_base):
        if knowledge_base in self.skills:
            del self.skills[knowledge_base]
            logging.info(f"Removed skills for {knowledge_base}")
        
        # Print available skills after removal
        print(f"Available Skills after removal: {self.get_available_skills()}")

    def remove_instructions(self, knowledge_base):
        if knowledge_base in self.instructions:
            del self.instructions[knowledge_base]
            logging.info(f"Removed instructions for {knowledge_base}")
            # Print instructions after removal
            print(f"Instructions after removal for '{knowledge_base}': {self.instructions}")

    def load_skills_and_instructions(self, knowledge_base):
        kb_path = os.path.join(KB_PATH, knowledge_base)
        skills_path = os.path.join(kb_path, "skills")
        instructions_file = os.path.join(kb_path, "instructions.txt")  # Changed to .txt as per the latest file

        # Load skills with their file paths
        if os.path.exists(skills_path):
            skill_files = [f for f in os.listdir(skills_path) if f.endswith('.md')]
            self.skills[knowledge_base] = [(f, os.path.join(skills_path, f)) for f in skill_files]
        else:
            self.skills[knowledge_base] = []

        # Load instructions
        if os.path.exists(instructions_file):
            with open(instructions_file, 'r') as f:
                self.instructions[knowledge_base] = f.read()
        else:
            self.instructions[knowledge_base] = ""

        # Print available skills after addition
        print(f"Available Skills after addition: {self.get_available_skills()}")

    def get_available_skills(self):
        # Collect skills and their paths from all selected knowledge bases
        skills = []
        for kb in self.selected_kbs:
            skills.extend(self.skills.get(kb, []))
        return skills

    def load_docs_folder(self, knowledge_base):
        kb_path = os.path.join(KB_PATH, knowledge_base)
        docs_path = os.path.join(kb_path, "docs")
        urls_file = os.path.join(kb_path, "urls.txt")

        # Load and process documents
        documents = self.load_documents(docs_path, urls_file)
        chunks = self.split_text(documents)
        self.save_to_chroma(chunks, knowledge_base)

    def load_documents(self, docs_path, urls_file):
        # Load local documents
        local_loader = DirectoryLoader(docs_path, glob="*.*")
        local_documents = local_loader.load()
        print(f"Loaded {len(local_documents)} local documents from {docs_path}")

        # Load URLs
        url_documents = self.load_urls(urls_file)
        
        # Combine local and URL documents
        all_documents = local_documents + url_documents
        print(f"Total documents loaded: {len(all_documents)}")
        return all_documents

    def load_urls(self, urls_file):
        if not os.path.exists(urls_file):
            print(f"No {urls_file} found. Skipping URL loading.")
            return []

        with open(urls_file, 'r') as file:
            urls = file.read().splitlines()

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

    def split_text(self, documents: list[Document]):
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
            add_start_index=True,
        )
        chunks = text_splitter.split_documents(documents)
        print(f"Split {len(documents)} documents into {len(chunks)} chunks.")
        return chunks

    def save_to_chroma(self, chunks: list[Document], knowledge_base: str):
        db_path = os.path.join(CHROMA_PATH, knowledge_base)
        embedding_function = OpenAIEmbeddings()
        
        # Check if the database already exists
        if os.path.exists(db_path):
            # Load the existing database
            db = Chroma(persist_directory=db_path, embedding_function=embedding_function)
            
            # Add new documents to the existing database
            db.add_documents(chunks)
        else:
            # Create a new database if it doesn't exist
            db = Chroma.from_documents(chunks, embedding_function, persist_directory=db_path)
        
        # Persist the changes
        db.persist()
        print(f"Updated database with {len(chunks)} chunks in {db_path}.")

    def build_vector_database(self, knowledge_base=None):
        if knowledge_base:
            kb_path = os.path.join(KB_PATH, knowledge_base)
            if os.path.isdir(kb_path):
                print(f"Processing knowledge base: {knowledge_base}")
                self.load_docs_folder(knowledge_base)
            else:
                print(f"Creating new knowledge base.")
                os.makedirs(os.path.join(kb_path, "docs"))
                with open(os.path.join(kb_path, "urls.txt"), 'w') as f:
                    pass  # Create an empty urls.txt file
                self.load_docs_folder(knowledge_base)
        else:
            # Update all knowledge bases
            knowledge_bases = self.get_knowledge_bases()
            
            for kb in knowledge_bases:
                print(f"Processing knowledge base: {kb}")
                self.load_docs_folder(kb)

    def add_to_knowledge_base(self, kb_name, url=None, file_path=None):
        kb_path = os.path.join(KB_PATH, kb_name)
        if not os.path.exists(kb_path):
            os.makedirs(os.path.join(kb_path, "docs"))
            with open(os.path.join(kb_path, "urls.txt"), 'w') as f:
                pass  # Create an empty urls.txt file

        if url:
            urls_file = os.path.join(kb_path, "urls.txt")
            with open(urls_file, 'a') as f:
                f.write(url + "\n")

        if file_path:
            docs_path = os.path.join(kb_path, "docs")
            os.makedirs(docs_path, exist_ok=True)
            file_name = os.path.basename(file_path)
            dest_path = os.path.join(docs_path, file_name)
            logging.info(f"Copying file from {file_path} to {dest_path}")
            shutil.copy2(file_path, dest_path)

        print(f"Added to knowledge base: {kb_name}")