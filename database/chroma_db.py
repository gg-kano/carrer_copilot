import chromadb
from typing import List, Dict, Optional
from datetime import datetime
import os
import sys

# Add parent directory to path for imports
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)

from utils.logger import get_logger, log_execution_time
from utils.exceptions import (
    DatabaseError,
    DatabaseConnectionError,
    DocumentNotFoundError,
    DuplicateDocumentError,
    ChunkStorageError
)

# Initialize logger
logger = get_logger(__name__)

class ChromaDBStorage:

    def __init__(self, persist_directory: str = None):
        """
        Initialize ChromaDB storage with collections

        Args:
            persist_directory: Directory to persist the database

        Raises:
            DatabaseConnectionError: If connection to ChromaDB fails
        """
        if persist_directory is None:
            from config import Config
            persist_directory = Config.CHROMA_DB_PATH

        try:
            logger.info(f"Initializing ChromaDB at {persist_directory}")
            self.client = chromadb.PersistentClient(path=persist_directory)

            self.documents_collection = self.client.get_or_create_collection(
                name="documents",
                metadata={"description": "FOR DOCUMENT STORAGE"}
            )
            logger.debug("Documents collection initialized")

            self.chunks_collection = self.client.get_or_create_collection(
                name="chunks",
                metadata={"description": "FOR CHUNK STORAGE"}
            )
            logger.debug("Chunks collection initialized")

            # Create PDF storage directory
            from config import Config
            self.pdf_storage_dir = Config.PDF_STORAGE_DIR
            os.makedirs(self.pdf_storage_dir, exist_ok=True)
            logger.debug(f"PDF storage directory created at {self.pdf_storage_dir}")

            logger.info("ChromaDB initialization completed successfully")

        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB: {str(e)}", exc_info=True)
            raise DatabaseConnectionError(
                f"Failed to initialize ChromaDB: {str(e)}",
                details={'persist_directory': persist_directory}
            )
    
    @log_execution_time(logger)
    def store_document(
        self,
        document_id: str,
        document_type: str,
        raw_text: str,
        user_id: Optional[str] = None,
        pdf_bytes: Optional[bytes] = None,
        summary: Optional[str] = None
    ):
        """
        Store document with optional PDF file and summary

        Args:
            document_id: Unique identifier
            document_type: Type of document (resume, job_description)
            raw_text: Extracted text content
            user_id: Optional user identifier
            pdf_bytes: Optional PDF file bytes to store
            summary: Optional professional summary (for resumes)

        Raises:
            DatabaseError: If document storage fails
        """
        try:
            logger.info(
                f"Storing document: {document_id} (type: {document_type})",
                extra={'document_id': document_id, 'document_type': document_type, 'has_pdf': pdf_bytes is not None}
            )

            metadata = {
                "document_type": document_type,
                "user_id": user_id or "",
                "created_at": str(datetime.now())
            }

            # Store summary if provided
            if summary:
                metadata["summary"] = summary
                logger.debug(f"Summary added for document {document_id}")

            # Store PDF file if provided
            if pdf_bytes:
                pdf_filename = f"{document_id}.pdf"
                pdf_path = os.path.join(self.pdf_storage_dir, pdf_filename)

                try:
                    with open(pdf_path, 'wb') as f:
                        f.write(pdf_bytes)
                    metadata["pdf_path"] = pdf_path
                    metadata["has_pdf"] = "true"
                    logger.info(f"PDF file stored at: {pdf_path}")
                except Exception as e:
                    logger.warning(f"Failed to store PDF for {document_id}: {str(e)}")
                    metadata["has_pdf"] = "false"
            else:
                metadata["has_pdf"] = "false"

            self.documents_collection.add(
                ids=[document_id],
                documents=[raw_text],
                metadatas=[metadata]
            )

            logger.info(f"Document {document_id} stored successfully")

        except Exception as e:
            logger.error(f"Failed to store document {document_id}: {str(e)}", exc_info=True)
            raise DatabaseError(
                f"Failed to store document: {str(e)}",
                details={'document_id': document_id, 'document_type': document_type}
            )
    
    @log_execution_time(logger)
    def store_chunks(self, chunks: List[Dict]):
        """
        Store multiple chunks in the database

        Args:
            chunks: List of chunk dictionaries

        Raises:
            ChunkStorageError: If chunk storage fails
        """
        if not chunks:
            logger.warning("No chunks provided for storage")
            return

        try:
            logger.info(f"Storing {len(chunks)} chunks")

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

            logger.info(f"{len(chunks)} chunks stored successfully")

        except Exception as e:
            logger.error(f"Failed to store chunks: {str(e)}", exc_info=True)
            raise ChunkStorageError(
                f"Failed to store chunks: {str(e)}",
                details={'chunk_count': len(chunks)}
            )
    
    @log_execution_time(logger)
    def search_similar_chunks(
        self,
        query_text: str,
        document_type: Optional[str] = None,
        field: Optional[str] = None,
        top_k: int = 10
    ) -> List[Dict]:
        """
        Search for similar chunks using semantic search

        Args:
            query_text: Query string to search for
            document_type: Filter by document type (optional)
            field: Filter by field name (optional)
            top_k: Maximum number of results to return

        Returns:
            List of matching chunks with similarity scores

        Raises:
            DatabaseError: If search operation fails
        """
        try:
            logger.debug(
                f"Searching chunks: top_k={top_k}, document_type={document_type}, field={field}",
                extra={'query_length': len(query_text), 'top_k': top_k}
            )

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

            logger.info(f"Search completed: found {len(formatted_results)} results")
            return formatted_results

        except Exception as e:
            logger.error(f"Search failed: {str(e)}", exc_info=True)
            raise DatabaseError(
                f"Search operation failed: {str(e)}",
                details={'top_k': top_k, 'document_type': document_type}
            )
    
    def get_document(self, document_id: str) -> Optional[Dict]:
        """
        Retrieve a document by ID

        Args:
            document_id: Document identifier

        Returns:
            Document dictionary if found, None otherwise
        """
        try:
            logger.debug(f"Fetching document: {document_id}")

            result = self.documents_collection.get(
                ids=[document_id],
                include=["documents", "metadatas"]
            )

            if result['ids']:
                logger.info(f"Document {document_id} retrieved successfully")
                return {
                    "id": result['ids'][0],
                    "raw_text": result['documents'][0],
                    "metadata": result['metadatas'][0]
                }
            else:
                logger.warning(f"Document {document_id} not found")
                return None

        except Exception as e:
            logger.error(f"Failed to retrieve document {document_id}: {str(e)}", exc_info=True)
            return None

    def get_pdf_file(self, document_id: str) -> Optional[bytes]:
        """
        Get PDF file bytes for a document if it exists

        Args:
            document_id: Document identifier

        Returns:
            PDF bytes if file exists, None otherwise
        """
        try:
            logger.debug(f"Fetching PDF for document: {document_id}")

            document = self.get_document(document_id)
            if not document:
                logger.warning(f"Cannot fetch PDF: document {document_id} not found")
                return None

            pdf_path = document['metadata'].get('pdf_path')
            if not pdf_path:
                logger.debug(f"No PDF path in metadata for document {document_id}")
                return None

            if not os.path.exists(pdf_path):
                logger.warning(f"PDF file not found at path: {pdf_path}")
                return None

            with open(pdf_path, 'rb') as f:
                pdf_bytes = f.read()

            logger.info(f"PDF retrieved for document {document_id} ({len(pdf_bytes)} bytes)")
            return pdf_bytes

        except Exception as e:
            logger.error(f"Failed to read PDF for {document_id}: {str(e)}", exc_info=True)
            return None
    
    def get_chunks_by_document(self, document_id: str) -> List[Dict]:
        """
        Retrieve all chunks for a specific document

        Args:
            document_id: Document identifier

        Returns:
            List of chunk dictionaries
        """
        try:
            logger.debug(f"Fetching chunks for document: {document_id}")

            results = self.chunks_collection.get(
                where={"document_id": document_id},
                include=["documents", "metadatas"]
            )

            chunks = [
                {
                    "chunk_id": results['ids'][i],
                    "content": results['documents'][i],
                    "metadata": results['metadatas'][i]
                }
                for i in range(len(results['ids']))
            ]

            logger.info(f"Retrieved {len(chunks)} chunks for document {document_id}")
            return chunks

        except Exception as e:
            logger.error(f"Failed to retrieve chunks for {document_id}: {str(e)}", exc_info=True)
            return []
    
    def delete_document(self, document_id: str):
        """
        Delete a document and all its associated chunks

        Args:
            document_id: Document identifier

        Raises:
            DatabaseError: If deletion fails
        """
        try:
            logger.info(f"Deleting document: {document_id}")

            # Get document to check for PDF file
            document = self.get_document(document_id)
            pdf_path = None
            if document:
                pdf_path = document['metadata'].get('pdf_path')

            # Delete document from collection
            try:
                self.documents_collection.delete(ids=[document_id])
                logger.debug(f"Document {document_id} deleted from collection")
            except Exception as e:
                logger.warning(f"Failed to delete document from collection: {str(e)}")

            # Delete associated chunks
            try:
                self.chunks_collection.delete(where={"document_id": document_id})
                logger.debug(f"Chunks for {document_id} deleted")
            except Exception as e:
                logger.warning(f"Failed to delete chunks: {str(e)}")

            # Delete PDF file if exists
            if pdf_path and os.path.exists(pdf_path):
                try:
                    os.remove(pdf_path)
                    logger.debug(f"PDF file deleted: {pdf_path}")
                except Exception as e:
                    logger.warning(f"Failed to delete PDF file: {str(e)}")

            logger.info(f"Document {document_id} deleted successfully")

        except Exception as e:
            logger.error(f"Failed to delete document {document_id}: {str(e)}", exc_info=True)
            raise DatabaseError(
                f"Failed to delete document: {str(e)}",
                details={'document_id': document_id}
            )
    
    def count_documents(self, document_type: Optional[str] = None) -> int:
        """
        Count documents, optionally filtered by type

        Args:
            document_type: Filter by document type (optional)

        Returns:
            Number of documents
        """
        try:
            where_filter = {"document_type": document_type} if document_type else None
            results = self.documents_collection.get(where=where_filter)
            count = len(results['ids'])
            logger.debug(f"Document count (type: {document_type or 'all'}): {count}")
            return count
        except Exception as e:
            logger.error(f"Failed to count documents: {str(e)}", exc_info=True)
            return 0

    def list_all_documents(self, document_type: Optional[str] = None) -> List[Dict]:
        """
        List all documents, optionally filtered by type

        Args:
            document_type: Filter by document type (optional)

        Returns:
            List of document metadata dictionaries
        """
        try:
            logger.debug(f"Listing documents (type: {document_type or 'all'})")

            where_filter = {"document_type": document_type} if document_type else None

            results = self.documents_collection.get(
                where=where_filter,
                include=["metadatas"]
            )

            documents = [
                {
                    "id": results['ids'][i],
                    "metadata": results['metadatas'][i]
                }
                for i in range(len(results['ids']))
            ]

            logger.info(f"Listed {len(documents)} documents (type: {document_type or 'all'})")
            return documents

        except Exception as e:
            logger.error(f"Failed to list documents: {str(e)}", exc_info=True)
            return []
