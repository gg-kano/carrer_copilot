import chromadb
from typing import List, Dict, Optional
from datetime import datetime

class ChromaDBStorage:

    def __init__(self, persist_directory: str = "./chroma_db"):
        self.client = chromadb.PersistentClient(path=persist_directory)

        self.documents_collection = self.client.get_or_create_collection(
            name="documents",
            metadata={"description": "FOR DOCUMENT STORAGE"}
        )

        self.chunks_collection = self.client.get_or_create_collection(
            name="chunks",
            metadata={"description": "FOR CHUNK STORAGE"}
        )

        print("✅ ChromaDB Init completed")
    
    def store_document(
        self,
        document_id: str,
        document_type: str,
        raw_text: str,
        user_id: Optional[str] = None
    ):

        self.documents_collection.add(
            ids=[document_id],
            documents=[raw_text],
            metadatas=[{
                "document_type": document_type,
                "user_id": user_id or "",
                "created_at": str(datetime.now())
            }]
        )

        print(f"✅ Document {document_id} Stored Successfully")
    
    def store_chunks(self, chunks: List[Dict]):

        if not chunks:
            return
        
        ids = [chunk['chunk_id'] for chunk in chunks]
        documents = [chunk['content'] for chunk in chunks]
        metadatas = [
            {
                **chunk['metadata'],
                "field": chunk['field']
            }
            for chunk in chunks
        ]
        
        self.chunks_collection.add(
            ids=ids,
            documents=documents,
            metadatas=metadatas
        )
        
        print(f"✅ {len(chunks)} chunks stored successfully")
    
    def search_similar_chunks(
        self,
        query_text: str,
        document_type: Optional[str] = None,
        field: Optional[str] = None,
        top_k: int = 10
    ) -> List[Dict]:

        where_filter = {}

        conditions = []
        if document_type:
            conditions.append({"document_type": {"$eq": document_type}})
        if field:
            conditions.append({"field": {"$eq": field}})

        if len(conditions) == 1:
            where_filter = conditions[0]
        elif len(conditions) > 1:
            where_filter = {"$and": conditions}
        else:
            where_filter = None

        results = self.chunks_collection.query(
            query_texts=[query_text],
            n_results=top_k,
            where=where_filter
        )

        formatted_results = []
        for i in range(len(results['ids'][0])):
            formatted_results.append({
                "chunk_id": results['ids'][0][i],
                "content": results['documents'][0][i],
                "metadata": results['metadatas'][0][i],
                "distance": results['distances'][0][i],
                "similarity": 1 - results['distances'][0][i]
            })

        return formatted_results
    
    def get_document(self, document_id: str) -> Optional[Dict]:
        try:
            result = self.documents_collection.get(
                ids=[document_id],
                include=["documents", "metadatas"]
            )
            
            if result['ids']:
                return {
                    "id": result['ids'][0],
                    "raw_text": result['documents'][0],
                    "metadata": result['metadatas'][0]
                }
        except Exception as e:
            print(f"Failed getting document: {e}")
        
        return None
    
    def get_chunks_by_document(self, document_id: str) -> List[Dict]:
        results = self.chunks_collection.get(
            where={"document_id": document_id},
            include=["documents", "metadatas"]
        )
        
        return [
            {
                "chunk_id": results['ids'][i],
                "content": results['documents'][i],
                "metadata": results['metadatas'][i]
            }
            for i in range(len(results['ids']))
        ]
    
    def delete_document(self, document_id: str):
        try:
            self.documents_collection.delete(ids=[document_id])
        except:
            pass

        try:
            self.chunks_collection.delete(where={"document_id": document_id})
        except:
            pass
        
        print(f"✅ Document {document_id} Already Deleted")
    
    def list_all_documents(self, document_type: Optional[str] = None) -> List[Dict]:
        where_filter = {"document_type": document_type} if document_type else None
        
        results = self.documents_collection.get(
            where=where_filter,
            include=["metadatas"]
        )
        
        return [
            {
                "id": results['ids'][i],
                "metadata": results['metadatas'][i]
            }
            for i in range(len(results['ids']))
        ]
