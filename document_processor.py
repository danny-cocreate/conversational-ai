import os
from typing import List, Dict

class DocumentProcessor:
    def __init__(self, storage_dir: str = 'knowledge_base'):
        self.storage_dir = storage_dir
        os.makedirs(storage_dir, exist_ok=True)
        self.documents: Dict[str, str] = {}
    
    def add_document(self, doc_name: str, content: str) -> bool:
        """Add a document to the knowledge base."""
        try:
            file_path = os.path.join(self.storage_dir, f"{doc_name}.txt")
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            self.documents[doc_name] = file_path
            return True
        except Exception as e:
            print(f"Error adding document: {str(e)}")
            return False
    
    def get_document_content(self, doc_name: str) -> str:
        """Retrieve document content from the knowledge base."""
        try:
            file_path = os.path.join(self.storage_dir, f"{doc_name}.txt")
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    return f.read()
            return ""
        except Exception as e:
            print(f"Error reading document: {str(e)}")
            return ""
    
    def list_documents(self) -> List[str]:
        """List all documents in the knowledge base."""
        try:
            files = os.listdir(self.storage_dir)
            return [os.path.splitext(f)[0] for f in files if f.endswith('.txt')]
        except Exception as e:
            print(f"Error listing documents: {str(e)}")
            return []
    
    def remove_document(self, doc_name: str) -> bool:
        """Remove a document from the knowledge base."""
        try:
            file_path = os.path.join(self.storage_dir, f"{doc_name}.txt")
            if os.path.exists(file_path):
                os.remove(file_path)
                if doc_name in self.documents:
                    del self.documents[doc_name]
                return True
            return False
        except Exception as e:
            print(f"Error removing document: {str(e)}")
            return False