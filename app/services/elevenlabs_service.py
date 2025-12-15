"""Service for ElevenLabs API interactions."""
import logging
import asyncio
from typing import Optional
import httpx
from config import Config

logger = logging.getLogger(__name__)

# Constants for RAG
ELEVENLABS_BASE_URL = "https://api.elevenlabs.io/v1"
RAG_EMBEDDING_MODEL = "e5_mistral_7b_instruct"
ALLOWED_FILE_EXTENSIONS = {".pdf", ".txt", ".doc", ".docx", ".md"}
MAX_FILE_SIZE_MB = 50


class ElevenLabsService:
    """Service for ElevenLabs API operations."""
    
    @staticmethod
    def _get_headers() -> dict:
        """Get common headers for ElevenLabs API requests."""
        Config.validate_elevenlabs_config()
        return {"xi-api-key": Config.ELEVENLABS_API_KEY}
    
    @staticmethod
    async def get_signed_url() -> str:
        """
        Get a signed WebSocket URL for authenticated ElevenLabs conversations.
        
        Returns:
            str: The signed WebSocket URL
            
        Raises:
            Exception: If the API request fails
        """
        Config.validate_elevenlabs_config()
        
        url = f"https://api.elevenlabs.io/v1/convai/conversation/get_signed_url?agent_id={Config.ELEVENLABS_AGENT_ID}"
        headers = {
            "xi-api-key": Config.ELEVENLABS_API_KEY
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, headers=headers)
            
            if response.status_code != 200:
                logger.error(f"[ElevenLabs] Failed to get signed URL: {response.status_code}")
                raise Exception(f"Failed to get signed URL: {response.status_code} - {response.text}")
            
            data = response.json()
            return data["signed_url"]
    
    @staticmethod
    async def upload_knowledge_base_document(
        file_content: bytes,
        filename: str
    ) -> dict:
        """
        Upload a document to ElevenLabs knowledge base.
        
        Args:
            file_content: The file content as bytes
            filename: The name of the file
            
        Returns:
            dict: Response containing document id and name
            
        Raises:
            Exception: If the upload fails
        """
        headers = ElevenLabsService._get_headers()
        url = f"{ELEVENLABS_BASE_URL}/convai/knowledge-base/file"
        
        async with httpx.AsyncClient(timeout=120.0) as client:
            files = {"file": (filename, file_content)}
            response = await client.post(url, headers=headers, files=files)
            
            if response.status_code != 200:
                logger.error(f"[ElevenLabs] Failed to upload document: {response.status_code} - {response.text}")
                raise Exception(f"Failed to upload document: {response.status_code} - {response.text}")
            
            data = response.json()
            logger.info(f"[ElevenLabs] Document uploaded successfully: {data.get('id')}")
            return data
    
    @staticmethod
    async def compute_rag_index(
        document_id: str,
        model: str = RAG_EMBEDDING_MODEL
    ) -> dict:
        """
        Trigger RAG indexing for a document.
        
        Args:
            document_id: The document ID to index
            model: The embedding model to use
            
        Returns:
            dict: Response containing indexing status
            
        Raises:
            Exception: If the request fails
        """
        headers = ElevenLabsService._get_headers()
        headers["Content-Type"] = "application/json"
        url = f"{ELEVENLABS_BASE_URL}/convai/knowledge-base/{document_id}/rag-index"
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(url, headers=headers, json={"model": model})
            
            if response.status_code != 200:
                logger.error(f"[ElevenLabs] Failed to trigger RAG indexing: {response.status_code} - {response.text}")
                raise Exception(f"Failed to trigger RAG indexing: {response.status_code} - {response.text}")
            
            data = response.json()
            logger.info(f"[ElevenLabs] RAG indexing triggered for document {document_id}: status={data.get('status')}")
            return data
    
    @staticmethod
    async def get_rag_index_status(document_id: str) -> dict:
        """
        Check the RAG indexing status for a document.
        
        Args:
            document_id: The document ID to check
            
        Returns:
            dict: Response containing current indexing status
            
        Raises:
            Exception: If the request fails
        """
        headers = ElevenLabsService._get_headers()
        headers["Content-Type"] = "application/json"
        url = f"{ELEVENLABS_BASE_URL}/convai/knowledge-base/{document_id}/rag-index"
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Use POST to check status (same endpoint triggers or returns status)
            response = await client.post(
                url, 
                headers=headers, 
                json={"model": RAG_EMBEDDING_MODEL}
            )
            
            if response.status_code != 200:
                logger.error(f"[ElevenLabs] Failed to get RAG status: {response.status_code}")
                raise Exception(f"Failed to get RAG indexing status: {response.status_code}")
            
            return response.json()
    
    @staticmethod
    async def wait_for_rag_indexing(
        document_id: str,
        max_wait_seconds: int = 300,
        poll_interval: int = 5
    ) -> dict:
        """
        Wait for RAG indexing to complete.
        
        Args:
            document_id: The document ID to monitor
            max_wait_seconds: Maximum time to wait in seconds
            poll_interval: Time between status checks in seconds
            
        Returns:
            dict: Final indexing status
            
        Raises:
            Exception: If indexing fails or times out
        """
        elapsed = 0
        last_status = None
        
        while elapsed < max_wait_seconds:
            status_data = await ElevenLabsService.get_rag_index_status(document_id)
            status = status_data.get("status", "").lower()
            progress = status_data.get("progress_percentage", 0)
            
            logger.info(f"[ElevenLabs] RAG indexing status: {status}, progress: {progress}%")
            last_status = status_data
            
            if status == "succeeded":
                logger.info(f"[ElevenLabs] RAG indexing completed for document {document_id}")
                return status_data
            elif status in ["failed", "rag_limit_exceeded", "document_too_small", "cannot_index_folder"]:
                raise Exception(f"RAG indexing failed with status: {status}")
            
            await asyncio.sleep(poll_interval)
            elapsed += poll_interval
        
        raise Exception(f"RAG indexing timed out after {max_wait_seconds} seconds. Last status: {last_status}")
    
    @staticmethod
    async def list_knowledge_base_documents(
        page_size: int = 100,
        search: Optional[str] = None
    ) -> dict:
        """
        List documents in the knowledge base.
        
        Args:
            page_size: Number of documents to return
            search: Optional search query
            
        Returns:
            dict: Response containing list of documents
            
        Raises:
            Exception: If the request fails
        """
        headers = ElevenLabsService._get_headers()
        url = f"{ELEVENLABS_BASE_URL}/convai/knowledge-base"
        params = {"page_size": page_size}
        if search:
            params["search"] = search
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, headers=headers, params=params)
            
            if response.status_code != 200:
                logger.error(f"[ElevenLabs] Failed to list documents: {response.status_code}")
                raise Exception(f"Failed to list knowledge base documents: {response.status_code}")
            
            return response.json()
    
    @staticmethod
    async def get_knowledge_base_document(document_id: str) -> dict:
        """
        Get details of a specific document.
        
        Args:
            document_id: The document ID
            
        Returns:
            dict: Document details
            
        Raises:
            Exception: If the request fails
        """
        headers = ElevenLabsService._get_headers()
        url = f"{ELEVENLABS_BASE_URL}/convai/knowledge-base/{document_id}"
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, headers=headers)
            
            if response.status_code != 200:
                logger.error(f"[ElevenLabs] Failed to get document: {response.status_code}")
                raise Exception(f"Failed to get document: {response.status_code}")
            
            return response.json()
    
    @staticmethod
    async def get_agent(agent_id: Optional[str] = None) -> dict:
        """
        Get the current agent configuration.
        
        Args:
            agent_id: The agent ID (defaults to configured ELEVENLABS_AGENT_ID)
            
        Returns:
            dict: Agent configuration
            
        Raises:
            Exception: If the request fails
        """
        headers = ElevenLabsService._get_headers()
        agent_id = agent_id or Config.ELEVENLABS_AGENT_ID
        url = f"{ELEVENLABS_BASE_URL}/convai/agents/{agent_id}"
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, headers=headers)
            
            if response.status_code != 200:
                logger.error(f"[ElevenLabs] Failed to get agent: {response.status_code} - {response.text}")
                raise Exception(f"Failed to get agent: {response.status_code}")
            
            return response.json()
    
    @staticmethod
    async def add_document_to_agent(
        document_id: str,
        document_name: str,
        document_type: str = "file",
        agent_id: Optional[str] = None
    ) -> dict:
        """
        Add a document to the agent's knowledge base.
        
        This updates the agent configuration to include the document
        in its knowledge base for RAG queries.
        
        Args:
            document_id: The document ID to add
            document_name: The document name
            document_type: The document type (file, url, text)
            agent_id: The agent ID (defaults to configured ELEVENLABS_AGENT_ID)
            
        Returns:
            dict: Updated agent configuration
            
        Raises:
            Exception: If the request fails
        """
        headers = ElevenLabsService._get_headers()
        headers["Content-Type"] = "application/json"
        agent_id = agent_id or Config.ELEVENLABS_AGENT_ID
        url = f"{ELEVENLABS_BASE_URL}/convai/agents/{agent_id}"
        
        # First, get the current agent configuration
        current_agent = await ElevenLabsService.get_agent(agent_id)
        
        # Extract the full prompt config (we need to preserve all fields)
        conv_config = current_agent.get("conversation_config", {})
        agent_config = conv_config.get("agent", {})
        prompt_config = agent_config.get("prompt", {})
        current_kb = prompt_config.get("knowledge_base", [])
        
        logger.debug(f"[ElevenLabs] Current knowledge base has {len(current_kb)} documents")
        
        # Check if document already exists in knowledge base
        existing_ids = {doc.get("id") for doc in current_kb}
        if document_id in existing_ids:
            logger.info(f"[ElevenLabs] Document {document_id} already in agent's knowledge base")
            return current_agent
        
        # Add the new document to the knowledge base
        new_doc = {
            "type": document_type,
            "name": document_name,
            "id": document_id
        }
        updated_kb = list(current_kb) + [new_doc]
        
        # Update the prompt config with the new knowledge base
        # IMPORTANT: We must send the FULL prompt config to avoid wiping other fields
        prompt_config["knowledge_base"] = updated_kb
        
        logger.debug(f"[ElevenLabs] Updated knowledge base will have {len(updated_kb)} documents")
        
        # Build the update payload with the complete prompt config
        update_payload = {
            "conversation_config": {
                "agent": {
                    "prompt": prompt_config
                }
            }
        }
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.patch(url, headers=headers, json=update_payload)
            
            if response.status_code != 200:
                logger.error(f"[ElevenLabs] Failed to update agent: {response.status_code} - {response.text}")
                raise Exception(f"Failed to add document to agent: {response.status_code} - {response.text}")
            
            data = response.json()
            
            # Verify the document was actually added
            updated_agent = await ElevenLabsService.get_agent(agent_id)
            if "conversation_config" in updated_agent:
                new_kb = updated_agent.get("conversation_config", {}).get("agent", {}).get("prompt", {}).get("knowledge_base", [])
                new_ids = {doc.get("id") for doc in new_kb}
                if document_id in new_ids:
                    logger.info(f"[ElevenLabs] Document {document_id} added to agent {agent_id}'s knowledge base (verified: {len(new_kb)} docs)")
                else:
                    logger.warning(f"[ElevenLabs] Document {document_id} NOT found in agent's knowledge base after update!")
                    logger.warning(f"[ElevenLabs] Current KB IDs: {new_ids}")
            
            return data
    
    @staticmethod
    async def get_agent_knowledge_base(agent_id: Optional[str] = None) -> list:
        """
        Get the current knowledge base documents attached to the agent.
        
        Args:
            agent_id: The agent ID (defaults to configured ELEVENLABS_AGENT_ID)
            
        Returns:
            list: List of knowledge base documents
        """
        agent = await ElevenLabsService.get_agent(agent_id)
        
        if "conversation_config" in agent:
            conv_config = agent.get("conversation_config", {})
            agent_config = conv_config.get("agent", {})
            prompt_config = agent_config.get("prompt", {})
            return prompt_config.get("knowledge_base", [])
        
        return []
    
    @staticmethod
    async def upload_and_index_document(
        file_content: bytes,
        filename: str,
        wait_for_completion: bool = False,
        max_wait_seconds: int = 300,
        attach_to_agent: bool = True,
        agent_id: Optional[str] = None
    ) -> dict:
        """
        Upload a document, trigger RAG indexing, and optionally attach to agent.
        
        This is a convenience method that combines upload, indexing, and agent attachment.
        
        Args:
            file_content: The file content as bytes
            filename: The name of the file
            wait_for_completion: Whether to wait for indexing to complete
            max_wait_seconds: Maximum time to wait for indexing
            attach_to_agent: Whether to attach the document to the agent's knowledge base
            agent_id: The agent ID (defaults to configured ELEVENLABS_AGENT_ID)
            
        Returns:
            dict: Response containing document info, indexing status, and agent attachment status
        """
        # Step 1: Upload the document
        upload_result = await ElevenLabsService.upload_knowledge_base_document(
            file_content, filename
        )
        document_id = upload_result.get("id")
        document_name = upload_result.get("name", filename)
        
        if not document_id:
            raise Exception("Document upload succeeded but no ID was returned")
        
        # Step 2: Trigger RAG indexing
        index_result = await ElevenLabsService.compute_rag_index(document_id)
        
        result = {
            "document_id": document_id,
            "document_name": document_name,
            "indexing_status": index_result.get("status"),
            "progress_percentage": index_result.get("progress_percentage", 0),
            "attached_to_agent": False
        }
        
        # Step 3: Optionally wait for completion
        if wait_for_completion:
            final_status = await ElevenLabsService.wait_for_rag_indexing(
                document_id, max_wait_seconds
            )
            result["indexing_status"] = final_status.get("status")
            result["progress_percentage"] = final_status.get("progress_percentage", 100)
        
        # Step 4: Attach document to agent's knowledge base
        if attach_to_agent:
            try:
                await ElevenLabsService.add_document_to_agent(
                    document_id=document_id,
                    document_name=document_name,
                    document_type="file",
                    agent_id=agent_id
                )
                result["attached_to_agent"] = True
                result["agent_id"] = agent_id or Config.ELEVENLABS_AGENT_ID
                logger.info(f"[ElevenLabs] Document {document_id} attached to agent")
            except Exception as e:
                logger.error(f"[ElevenLabs] Failed to attach document to agent: {e}")
                result["agent_attachment_error"] = str(e)
        
        return result
