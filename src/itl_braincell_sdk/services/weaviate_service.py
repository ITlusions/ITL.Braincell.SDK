import weaviate
from typing import List, Optional, Dict, Any
import logging
from weaviate.classes.config import Configure

from itl_braincell_sdk.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class WeaviateService:
    """Service for vector database operations with Weaviate (SDK v4)"""
    
    def __init__(self):
        """Initialize Weaviate client"""
        self.client = None
        # Parse Weaviate URL properly
        url = settings.weaviate_url.strip("/")
        if url.startswith("http://"):
            url = url[7:]  # Remove http://
        elif url.startswith("https://"):
            url = url[8:]  # Remove https://
        
        # Split host and port
        if ":" in url:
            host, port = url.split(":", 1)
            port = int(port)
        else:
            host = url
            port = 8080
        
        logger.info(f"Connecting to Weaviate at {host}:{port}")
        
        # Try v4 API - simplified connection without additional_config
        # Using grpc_port 50051 for Kubernetes gRPC service
        try:
            self.client = weaviate.connect_to_local(
                host=host,
                port=port,
                grpc_port=50051
            )
            logger.info("✓ Connected to Weaviate v4")
        except Exception as e:
            logger.error(f"Weaviate v4 connection failed: {e}")
            logger.info("Attempting connection with gRPC checks disabled...")
            try:
                # Fallback: Connect without gRPC health checks
                self.client = weaviate.connect_to_local(
                    host=host,
                    port=port,
                    grpc_port=50051,
                    skip_init_checks=True
                )
                logger.info("✓ Connected to Weaviate v4 (gRPC checks skipped)")
            except Exception as e2:
                logger.error(f"Weaviate connection failed with fallback: {e2}")
                self.client = None
        
        self._ensure_schema()
        self._ensure_archive_properties()
    
    def _ensure_archive_properties(self):
        """Add archived/archived_at properties to all memory collections if missing."""
        if not self.client:
            return
        archive_collections = [
            "Conversation", "Interaction", "Decision", "CodeSnippet",
            "ArchitectureNote", "FileDiscussed", "MemorySession", "Note",
        ]
        try:
            from weaviate.classes.config import Property, DataType
            for name in archive_collections:
                try:
                    col = self.client.collections.get(name)
                    existing = {p.name for p in col.config.get().properties}
                    if "archived" not in existing:
                        col.config.add_property(Property(name="archived", data_type=DataType.BOOL))
                        logger.info(f"✓ Added 'archived' property to {name}")
                    if "archived_at" not in existing:
                        col.config.add_property(Property(name="archived_at", data_type=DataType.TEXT))
                        logger.info(f"✓ Added 'archived_at' property to {name}")
                except Exception as e:
                    logger.warning(f"Could not ensure archive properties for {name}: {e}")
        except Exception as e:
            logger.error(f"_ensure_archive_properties failed: {e}")

    def _ensure_schema(self):
        """Ensure required schema classes exist in Weaviate using v4 SDK"""
        if not self.client:
            logger.error("Weaviate client not available - cannot create schema")
            return
        
        # Define collection properties
        collections_config = {
            "Conversation": {
                "description": "Copilot conversations and discussions",
                "properties": [
                    {"name": "topic", "description": "Conversation topic", "dataType": ["text"]},
                    {"name": "summary", "description": "Conversation summary", "dataType": ["text"]},
                    {"name": "session_id", "description": "Session ID", "dataType": ["string"]},
                    {"name": "embedding_id", "description": "ID from PostgreSQL", "dataType": ["string"]},
                ],
            },
            "Interaction": {
                "description": "Individual messages and interactions",
                "properties": [
                    {"name": "content", "description": "Message content", "dataType": ["text"]},
                    {"name": "role", "description": "Message role (user/assistant/system)", "dataType": ["string"]},
                    {"name": "message_type", "description": "Type of message", "dataType": ["string"]},
                    {"name": "conversation_id", "description": "Parent conversation ID", "dataType": ["string"]},
                    {"name": "session_id", "description": "Session ID", "dataType": ["string"]},
                    {"name": "embedding_id", "description": "ID from PostgreSQL", "dataType": ["string"]},
                ],
            },
            "Decision": {
                "description": "Design decisions",
                "properties": [
                    {"name": "decision", "description": "Decision text", "dataType": ["text"]},
                    {"name": "rationale", "description": "Decision rationale", "dataType": ["text"]},
                    {"name": "embedding_id", "description": "ID from PostgreSQL", "dataType": ["string"]},
                ],
            },
            "CodeSnippet": {
                "description": "Code snippets and examples",
                "properties": [
                    {"name": "title", "description": "Snippet title", "dataType": ["text"]},
                    {"name": "code_content", "description": "Code content", "dataType": ["text"]},
                    {"name": "language", "description": "Programming language", "dataType": ["string"]},
                    {"name": "embedding_id", "description": "ID from PostgreSQL", "dataType": ["string"]},
                ],
            },
            "ArchitectureNote": {
                "description": "Architecture and design notes",
                "properties": [
                    {"name": "component", "description": "Component name", "dataType": ["text"]},
                    {"name": "description", "description": "Description", "dataType": ["text"]},
                    {"name": "type", "description": "Note type", "dataType": ["string"]},
                    {"name": "tags", "description": "Tags", "dataType": ["string[]"]},
                    {"name": "embedding_id", "description": "ID from PostgreSQL", "dataType": ["string"]},
                ],
            },
            "FileDiscussed": {
                "description": "Files mentioned in discussions",
                "properties": [
                    {"name": "file_path", "description": "File path", "dataType": ["text"]},
                    {"name": "description", "description": "Description", "dataType": ["text"]},
                    {"name": "language", "description": "Programming language", "dataType": ["string"]},
                    {"name": "purpose", "description": "Purpose", "dataType": ["text"]},
                    {"name": "embedding_id", "description": "ID from PostgreSQL", "dataType": ["string"]},
                ],
            },
            "MemorySession": {
                "description": "Memory sessions and context",
                "properties": [
                    {"name": "session_name", "description": "Session name", "dataType": ["text"]},
                    {"name": "summary", "description": "Session summary", "dataType": ["text"]},
                    {"name": "status", "description": "Session status", "dataType": ["string"]},
                    {"name": "embedding_id", "description": "ID from PostgreSQL", "dataType": ["string"]},
                ],
            },
            "Note": {
                "description": "Free-form notes and observations",
                "properties": [
                    {"name": "title", "description": "Note title", "dataType": ["text"]},
                    {"name": "content", "description": "Note body text", "dataType": ["text"]},
                    {"name": "tags", "description": "Tags", "dataType": ["string[]"]},
                    {"name": "source", "description": "Source (agent/user)", "dataType": ["string"]},
                    {"name": "embedding_id", "description": "ID from PostgreSQL", "dataType": ["string"]},
                ],
            },
            "ResearchQuestion": {
                "description": "End-user questions flagged for research follow-up",
                "properties": [
                    {"name": "question", "description": "The question text", "dataType": ["text"]},
                    {"name": "status", "description": "Lifecycle status", "dataType": ["string"]},
                    {"name": "priority", "description": "Priority level", "dataType": ["string"]},
                    {"name": "context", "description": "Surrounding context", "dataType": ["text"]},
                    {"name": "source", "description": "How it was captured", "dataType": ["string"]},
                    {"name": "embedding_id", "description": "ID from PostgreSQL", "dataType": ["string"]},
                ],
            },
            "Job": {
                "description": "Job postings and freelance opportunities",
                "properties": [
                    {"name": "job_id", "description": "Unique job identifier", "dataType": ["string"]},
                    {"name": "title", "description": "Job title", "dataType": ["text"]},
                    {"name": "company", "description": "Company or client name", "dataType": ["text"]},
                    {"name": "location", "description": "Job location", "dataType": ["string"]},
                    {"name": "description", "description": "Full job description", "dataType": ["text"]},
                    {"name": "url", "description": "Job posting URL", "dataType": ["string"]},
                    {"name": "source", "description": "Job source (github, linkedin, freep, etc.)", "dataType": ["string"]},
                    {"name": "salary_min", "description": "Minimum salary/hourly rate", "dataType": ["number"]},
                    {"name": "salary_max", "description": "Maximum salary/hourly rate", "dataType": ["number"]},
                    {"name": "job_type", "description": "Job type (fulltime, freelance, zzp, contract, etc.)", "dataType": ["string"]},
                    {"name": "seniority_level", "description": "Required seniority level", "dataType": ["string"]},
                    {"name": "posted_date", "description": "Date job was posted", "dataType": ["string"]},
                    {"name": "tags", "description": "Job tags and keywords", "dataType": ["string[]"]},
                ],
            },
            # --- National Security Intelligence Collections ---
            "ThreatActor": {
                "description": "Threat actors — APTs, criminal groups, state-sponsored actors",
                "properties": [
                    {"name": "name", "description": "Threat actor name", "dataType": ["text"]},
                    {"name": "aliases", "description": "Known aliases", "dataType": ["text"]},
                    {"name": "classification", "description": "Actor type (apt/criminal/hacktivist/state-sponsored)", "dataType": ["string"]},
                    {"name": "origin_country", "description": "Country of origin", "dataType": ["string"]},
                    {"name": "motivation", "description": "Motivation (espionage/financial/disruption/ideological)", "dataType": ["string"]},
                    {"name": "sophistication", "description": "Sophistication level", "dataType": ["string"]},
                    {"name": "ttps", "description": "MITRE ATT&CK technique IDs", "dataType": ["text"]},
                    {"name": "status", "description": "Active/inactive/unknown", "dataType": ["string"]},
                    {"name": "stix_id", "description": "STIX 2.1 identity reference", "dataType": ["string"]},
                    {"name": "embedding_id", "description": "ID from PostgreSQL", "dataType": ["string"]},
                    {"name": "archived", "description": "Whether record is archived", "dataType": ["boolean"]},
                    {"name": "archived_at", "description": "When archived", "dataType": ["text"]},
                ],
            },
            "SecurityIncident": {
                "description": "Security incidents — breaches, attacks, events under investigation",
                "properties": [
                    {"name": "title", "description": "Incident title", "dataType": ["text"]},
                    {"name": "description", "description": "Incident description", "dataType": ["text"]},
                    {"name": "severity", "description": "Severity level", "dataType": ["string"]},
                    {"name": "status", "description": "Incident status", "dataType": ["string"]},
                    {"name": "attack_vector", "description": "Initial attack vector", "dataType": ["string"]},
                    {"name": "threat_actor_name", "description": "Attributed threat actor", "dataType": ["string"]},
                    {"name": "mitre_tactics", "description": "MITRE ATT&CK tactic IDs", "dataType": ["text"]},
                    {"name": "classification_level", "description": "Classification marking", "dataType": ["string"]},
                    {"name": "embedding_id", "description": "ID from PostgreSQL", "dataType": ["string"]},
                    {"name": "archived", "description": "Whether record is archived", "dataType": ["boolean"]},
                    {"name": "archived_at", "description": "When archived", "dataType": ["text"]},
                ],
            },
            "IOC": {
                "description": "Indicators of Compromise — IPs, domains, hashes, CVEs",
                "properties": [
                    {"name": "ioc_type", "description": "IOC type (ip/domain/hash_md5/cve/...)", "dataType": ["string"]},
                    {"name": "value", "description": "IOC value", "dataType": ["text"]},
                    {"name": "severity", "description": "Severity level", "dataType": ["string"]},
                    {"name": "status", "description": "Status (active/expired/false_positive)", "dataType": ["string"]},
                    {"name": "source", "description": "IOC source", "dataType": ["string"]},
                    {"name": "context", "description": "Context description", "dataType": ["text"]},
                    {"name": "tags", "description": "Tags", "dataType": ["string[]"]},
                    {"name": "embedding_id", "description": "ID from PostgreSQL", "dataType": ["string"]},
                    {"name": "archived", "description": "Whether record is archived", "dataType": ["boolean"]},
                    {"name": "archived_at", "description": "When archived", "dataType": ["text"]},
                ],
            },
            "IntelReport": {
                "description": "Threat intelligence reports — TLP-marked analysis and briefings",
                "properties": [
                    {"name": "title", "description": "Report title", "dataType": ["text"]},
                    {"name": "summary", "description": "Executive summary", "dataType": ["text"]},
                    {"name": "content", "description": "Full report body", "dataType": ["text"]},
                    {"name": "classification_level", "description": "Classification marking", "dataType": ["string"]},
                    {"name": "tlp_level", "description": "TLP level (WHITE/GREEN/AMBER/RED)", "dataType": ["string"]},
                    {"name": "source", "description": "Intelligence source", "dataType": ["string"]},
                    {"name": "analyst", "description": "Author/analyst", "dataType": ["string"]},
                    {"name": "embedding_id", "description": "ID from PostgreSQL", "dataType": ["string"]},
                    {"name": "archived", "description": "Whether record is archived", "dataType": ["boolean"]},
                    {"name": "archived_at", "description": "When archived", "dataType": ["text"]},
                ],
            },
            "VulnPatch": {
                "description": "Known-vulnerable code snippets paired with their patched equivalents",
                "properties": [
                    {"name": "title", "description": "Short title", "dataType": ["text"]},
                    {"name": "description", "description": "What the vulnerability is about", "dataType": ["text"]},
                    {"name": "vulnerable_code", "description": "The vulnerable code snippet", "dataType": ["text"]},
                    {"name": "patched_code", "description": "The fixed/patched version", "dataType": ["text"]},
                    {"name": "patch_explanation", "description": "Explanation of what changed and why", "dataType": ["text"]},
                    {"name": "language", "description": "Programming language", "dataType": ["string"]},
                    {"name": "category", "description": "Vulnerability category (sql_injection, xss, ...)", "dataType": ["string"]},
                    {"name": "severity", "description": "critical / high / medium / low", "dataType": ["string"]},
                    {"name": "embedding_id", "description": "ID from PostgreSQL", "dataType": ["string"]},
                    {"name": "archived", "description": "Whether record is archived", "dataType": ["boolean"]},
                    {"name": "archived_at", "description": "When archived", "dataType": ["text"]},
                ],
            },
            "Task": {
                "description": "Tasks and backlog items — work items tracked by agents or teams",
                "properties": [
                    {"name": "title", "description": "Task title", "dataType": ["text"]},
                    {"name": "description", "description": "Task description", "dataType": ["text"]},
                    {"name": "status", "description": "open / in_progress / done / cancelled / blocked", "dataType": ["string"]},
                    {"name": "priority", "description": "critical / high / medium / low", "dataType": ["string"]},
                    {"name": "project", "description": "Project or workstream", "dataType": ["string"]},
                    {"name": "assignee", "description": "Person or agent responsible", "dataType": ["string"]},
                    {"name": "embedding_id", "description": "ID from PostgreSQL", "dataType": ["string"]},
                    {"name": "archived", "description": "Whether record is archived", "dataType": ["boolean"]},
                    {"name": "archived_at", "description": "When archived", "dataType": ["text"]},
                ],
            },
            "Runbook": {
                "description": "Operational runbooks — step-by-step procedures for incidents, deployments, maintenance",
                "properties": [
                    {"name": "title", "description": "Runbook title", "dataType": ["text"]},
                    {"name": "description", "description": "Runbook description", "dataType": ["text"]},
                    {"name": "category", "description": "incident_response / deployment / maintenance / ...", "dataType": ["string"]},
                    {"name": "trigger", "description": "When to use this runbook", "dataType": ["text"]},
                    {"name": "prerequisites", "description": "Prerequisites before starting", "dataType": ["text"]},
                    {"name": "severity", "description": "P1 / P2 / P3 for incident runbooks", "dataType": ["string"]},
                    {"name": "embedding_id", "description": "ID from PostgreSQL", "dataType": ["string"]},
                    {"name": "archived", "description": "Whether record is archived", "dataType": ["boolean"]},
                    {"name": "archived_at", "description": "When archived", "dataType": ["text"]},
                ],
            },
            "ApiContract": {
                "description": "API contracts — specifications, versioning, endpoints, and changelogs",
                "properties": [
                    {"name": "title", "description": "Contract title", "dataType": ["text"]},
                    {"name": "service_name", "description": "Service name", "dataType": ["string"]},
                    {"name": "version", "description": "API version", "dataType": ["string"]},
                    {"name": "spec_format", "description": "openapi / graphql / grpc / rest / soap", "dataType": ["string"]},
                    {"name": "base_url", "description": "Base URL", "dataType": ["string"]},
                    {"name": "spec_content", "description": "Full spec or summary", "dataType": ["text"]},
                    {"name": "status", "description": "active / deprecated / draft / sunset", "dataType": ["string"]},
                    {"name": "breaking_changes", "description": "Breaking changes description", "dataType": ["text"]},
                    {"name": "embedding_id", "description": "ID from PostgreSQL", "dataType": ["string"]},
                    {"name": "archived", "description": "Whether record is archived", "dataType": ["boolean"]},
                    {"name": "archived_at", "description": "When archived", "dataType": ["text"]},
                ],
            },
            "Dependency": {
                "description": "Software dependencies — packages, versions, license, and CVE exposure",
                "properties": [
                    {"name": "name", "description": "Package name", "dataType": ["text"]},
                    {"name": "version", "description": "Package version", "dataType": ["string"]},
                    {"name": "ecosystem", "description": "pypi / npm / nuget / maven / cargo / go / gem", "dataType": ["string"]},
                    {"name": "project", "description": "Internal project using this dep", "dataType": ["string"]},
                    {"name": "status", "description": "ok / vulnerable / deprecated / outdated / unknown", "dataType": ["string"]},
                    {"name": "license", "description": "License identifier", "dataType": ["string"]},
                    {"name": "notes", "description": "Additional notes", "dataType": ["text"]},
                    {"name": "embedding_id", "description": "ID from PostgreSQL", "dataType": ["string"]},
                    {"name": "archived", "description": "Whether record is archived", "dataType": ["boolean"]},
                    {"name": "archived_at", "description": "When archived", "dataType": ["text"]},
                ],
            },
        }

        try:
            for class_name, config in collections_config.items():
                try:
                    # Check if collection exists (v4 SDK: list_all() returns dict)
                    existing_collections = self.client.collections.list_all()
                    collection_exists = class_name in existing_collections
                    
                    if not collection_exists:
                        # Create the collection using v4 API (no vectorizer - standalone Weaviate)
                        self.client.collections.create(
                            name=class_name,
                            description=config["description"],
                            vectorizer_config=Configure.Vectorizer.none(),
                        )
                        logger.info(f"✓ Created Weaviate collection: {class_name}")
                    else:
                        logger.info(f"✓ Weaviate collection already exists: {class_name}")
                except Exception as e:
                    logger.warning(f"Could not verify/create collection {class_name}: {e}")
        except Exception as e:
            logger.error(f"Schema creation error: {e}")
    
    def index_conversation(
        self, 
        embedding_id: str, 
        topic: str, 
        summary: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> bool:
        """Index a conversation in Weaviate using v4 SDK"""
        if not self.client:
            logger.warning("Weaviate client not available, skipping conversation index")
            return False
        
        try:
            properties = {
                "topic": topic,
                "summary": summary or "",
                "session_id": session_id or "",
                "embedding_id": embedding_id,
            }
            
            try:
                self.client.collections.get("Conversation").data.insert(
                    properties=properties,
                    uuid=embedding_id,
                )
            except Exception as insert_err:
                if "already exists" in str(insert_err):
                    self.client.collections.get("Conversation").data.update(
                        uuid=embedding_id,
                        properties=properties,
                    )
                else:
                    raise
            
            logger.info(f"✓ Indexed conversation: {embedding_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to index conversation {embedding_id}: {e}")
            return False
    
    
    def index_decision(
        self,
        embedding_id: str,
        decision: str,
        rationale: Optional[str] = None
    ) -> bool:
        """Index a design decision in Weaviate using v4 SDK"""
        if not self.client:
            logger.warning("Weaviate client not available, skipping decision index")
            return False
        
        try:
            properties = {
                "decision": decision,
                "rationale": rationale or "",
                "embedding_id": embedding_id,
            }
            
            try:
                # Try to insert first
                self.client.collections.get("Decision").data.insert(
                    properties=properties,
                    uuid=embedding_id,
                )
            except Exception as insert_err:
                # If insert fails, try to update
                if "already exists" in str(insert_err):
                    self.client.collections.get("Decision").data.update(
                        uuid=embedding_id,
                        properties=properties,
                    )
                else:
                    raise
            
            logger.info(f"✓ Indexed decision: {embedding_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to index decision {embedding_id}: {e}")
            return False
    
    def delete_decision(self, embedding_id: str) -> bool:
        """Delete a design decision from Weaviate"""
        if not self.client:
            logger.warning("Weaviate client not available, skipping delete")
            return False
        
        try:
            self.client.collections.get("Decision").data.delete_by_id(embedding_id)
            logger.info(f"✓ Deleted decision: {embedding_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete decision {embedding_id}: {e}")
            return False
    
    def index_code_snippet(
        self,
        embedding_id: str,
        title: str,
        code_content: str,
        language: Optional[str] = None
    ) -> bool:
        """Index a code snippet in Weaviate using v4 SDK"""
        if not self.client:
            logger.warning("Weaviate client not available, skipping snippet index")
            return False
        
        try:
            properties = {
                "title": title,
                "code_content": code_content,
                "language": language or "",
                "embedding_id": embedding_id,
            }
            
            try:
                self.client.collections.get("CodeSnippet").data.insert(
                    properties=properties,
                    uuid=embedding_id,
                )
            except Exception as insert_err:
                if "already exists" in str(insert_err):
                    self.client.collections.get("CodeSnippet").data.update(
                        uuid=embedding_id,
                        properties=properties,
                    )
                else:
                    raise
            
            logger.info(f"✓ Indexed code snippet: {embedding_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to index snippet {embedding_id}: {e}")
            return False
    
    def delete_code_snippet(self, embedding_id: str) -> bool:
        """Delete a code snippet from Weaviate"""
        if not self.client:
            logger.warning("Weaviate client not available, skipping delete")
            return False
        
        try:
            self.client.collections.get("CodeSnippet").data.delete_by_id(embedding_id)
            logger.info(f"✓ Deleted code snippet: {embedding_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete snippet {embedding_id}: {e}")
            return False
    
    def update_conversation(
        self,
        embedding_id: str,
        topic: Optional[str] = None,
        summary: Optional[str] = None
    ) -> bool:
        """Update a conversation in Weaviate using v4 SDK"""
        if not self.client:
            logger.warning("Weaviate client not available, skipping update")
            return False
        
        try:
            update_data = {}
            if topic is not None:
                update_data["topic"] = topic
            if summary is not None:
                update_data["summary"] = summary
            
            if update_data:
                self.client.collections.get("Conversation").data.update(
                    uuid=embedding_id,
                    properties=update_data,
                )
                logger.info(f"✓ Updated conversation: {embedding_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to update conversation {embedding_id}: {e}")
            return False
    
    def delete_conversation(self, embedding_id: str) -> bool:
        """Delete a conversation from Weaviate"""
        if not self.client:
            logger.warning("Weaviate client not available, skipping delete")
            return False
        
        try:
            self.client.collections.get("Conversation").data.delete_by_id(embedding_id)
            logger.info(f"✓ Deleted conversation: {embedding_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete conversation {embedding_id}: {e}")
            return False
    
    def index_interaction(
        self,
        embedding_id: str,
        content: str,
        role: str,
        message_type: str,
        conversation_id: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> bool:
        """Index an interaction/message in Weaviate using v4 SDK"""
        if not self.client:
            logger.warning("Weaviate client not available, skipping interaction index")
            return False
        
        try:
            properties = {
                "content": content,
                "role": role,
                "message_type": message_type,
                "conversation_id": conversation_id or "",
                "session_id": session_id or "",
                "embedding_id": embedding_id,
            }
            
            try:
                self.client.collections.get("Interaction").data.insert(
                    properties=properties,
                    uuid=embedding_id,
                )
            except Exception as insert_err:
                if "already exists" in str(insert_err):
                    self.client.collections.get("Interaction").data.update(
                        uuid=embedding_id,
                        properties=properties,
                    )
                else:
                    raise
            
            logger.info(f"✓ Indexed interaction: {embedding_id} ({role}/{message_type})")
            return True
        except Exception as e:
            logger.error(f"Failed to index interaction {embedding_id}: {e}")
            return False
    
    def update_interaction(
        self,
        embedding_id: str,
        content: Optional[str] = None,
        role: Optional[str] = None,
        message_type: Optional[str] = None
    ) -> bool:
        """Update an interaction in Weaviate using v4 SDK"""
        if not self.client:
            logger.warning("Weaviate client not available, skipping update")
            return False
        
        try:
            update_data = {}
            if content is not None:
                update_data["content"] = content
            if role is not None:
                update_data["role"] = role
            if message_type is not None:
                update_data["message_type"] = message_type
            
            if update_data:
                self.client.collections.get("Interaction").data.update(
                    uuid=embedding_id,
                    properties=update_data,
                )
                logger.info(f"✓ Updated interaction: {embedding_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to update interaction {embedding_id}: {e}")
            return False
    
    def delete_interaction(self, embedding_id: str) -> bool:
        """Delete an interaction from Weaviate"""
        if not self.client:
            logger.warning("Weaviate client not available, skipping delete")
            return False
        
        try:
            self.client.collections.get("Interaction").data.delete_by_id(embedding_id)
            logger.info(f"✓ Deleted interaction: {embedding_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete interaction {embedding_id}: {e}")
            return False
    
    def index_architecture_note(
        self,
        embedding_id: str,
        component: str,
        description: str,
        note_type: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> bool:
        """Index an architecture note in Weaviate using v4 SDK"""
        if not self.client:
            logger.warning("Weaviate client not available, skipping note index")
            return False
        
        try:
            properties = {
                "component": component,
                "description": description,
                "type": note_type or "general",
                "tags": tags if tags else [],
                "embedding_id": embedding_id,
            }
            
            try:
                self.client.collections.get("ArchitectureNote").data.insert(
                    properties=properties,
                    uuid=embedding_id,
                )
            except Exception as insert_err:
                if "already exists" in str(insert_err):
                    self.client.collections.get("ArchitectureNote").data.update(
                        uuid=embedding_id,
                        properties=properties,
                    )
                else:
                    raise
            
            logger.info(f"✓ Indexed architecture note: {embedding_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to index architecture note {embedding_id}: {e}")
            return False
    
    def update_architecture_note(
        self,
        embedding_id: str,
        component: Optional[str] = None,
        description: Optional[str] = None,
        note_type: Optional[str] = None
    ) -> bool:
        """Update an architecture note in Weaviate using v4 SDK"""
        if not self.client:
            logger.warning("Weaviate client not available, skipping update")
            return False
        
        try:
            update_data = {}
            if component is not None:
                update_data["component"] = component
            if description is not None:
                update_data["description"] = description
            if note_type is not None:
                update_data["type"] = note_type
            
            if update_data:
                self.client.collections.get("ArchitectureNote").data.update(
                    uuid=embedding_id,
                    properties=update_data,
                )
                logger.info(f"✓ Updated architecture note: {embedding_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to update architecture note {embedding_id}: {e}")
            return False
    
    def delete_architecture_note(self, embedding_id: str) -> bool:
        """Delete an architecture note from Weaviate"""
        if not self.client:
            logger.warning("Weaviate client not available, skipping delete")
            return False
        
        try:
            self.client.collections.get("ArchitectureNote").data.delete_by_id(embedding_id)
            logger.info(f"✓ Deleted architecture note: {embedding_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete architecture note {embedding_id}: {e}")
            return False
    
    def index_file_discussed(
        self,
        embedding_id: str,
        file_path: str,
        description: Optional[str] = None,
        language: Optional[str] = None,
        purpose: Optional[str] = None
    ) -> bool:
        """Index a file discussed in Weaviate using v4 SDK"""
        if not self.client:
            logger.warning("Weaviate client not available, skipping file index")
            return False
        
        try:
            properties = {
                "file_path": file_path,
                "description": description or "",
                "language": language or "",
                "purpose": purpose or "",
                "embedding_id": embedding_id,
            }
            
            try:
                self.client.collections.get("FileDiscussed").data.insert(
                    properties=properties,
                    uuid=embedding_id,
                )
            except Exception as insert_err:
                if "already exists" in str(insert_err):
                    self.client.collections.get("FileDiscussed").data.update(
                        uuid=embedding_id,
                        properties=properties,
                    )
                else:
                    raise
            
            logger.info(f"✓ Indexed file: {embedding_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to index file {embedding_id}: {e}")
            return False
    
    def update_file_discussed(
        self,
        embedding_id: str,
        description: Optional[str] = None,
        purpose: Optional[str] = None
    ) -> bool:
        """Update a file discussed in Weaviate using v4 SDK"""
        if not self.client:
            logger.warning("Weaviate client not available, skipping update")
            return False
        
        try:
            update_data = {}
            if description is not None:
                update_data["description"] = description
            if purpose is not None:
                update_data["purpose"] = purpose
            
            if update_data:
                self.client.collections.get("FileDiscussed").data.update(
                    uuid=embedding_id,
                    properties=update_data,
                )
                logger.info(f"✓ Updated file: {embedding_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to update file {embedding_id}: {e}")
            return False
    
    def delete_file_discussed(self, embedding_id: str) -> bool:
        """Delete a file discussed from Weaviate"""
        if not self.client:
            logger.warning("Weaviate client not available, skipping delete")
            return False
        
        try:
            self.client.collections.get("FileDiscussed").data.delete_by_id(embedding_id)
            logger.info(f"✓ Deleted file: {embedding_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete file {embedding_id}: {e}")
            return False
    
    def index_memory_session(
        self,
        embedding_id: str,
        session_name: str,
        summary: Optional[str] = None,
        status: Optional[str] = None
    ) -> bool:
        """Index a memory session in Weaviate using v4 SDK"""
        if not self.client:
            logger.warning("Weaviate client not available, skipping session index")
            return False
        
        try:
            properties = {
                "session_name": session_name,
                "summary": summary or "",
                "status": status or "active",
                "embedding_id": embedding_id,
            }
            
            try:
                self.client.collections.get("MemorySession").data.insert(
                    properties=properties,
                    uuid=embedding_id,
                )
            except Exception as insert_err:
                if "already exists" in str(insert_err):
                    self.client.collections.get("MemorySession").data.update(
                        uuid=embedding_id,
                        properties=properties,
                    )
                else:
                    raise
            
            logger.info(f"✓ Indexed memory session: {embedding_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to index memory session {embedding_id}: {e}")
            return False
    
    def update_memory_session(
        self,
        embedding_id: str,
        session_name: Optional[str] = None,
        summary: Optional[str] = None,
        status: Optional[str] = None
    ) -> bool:
        """Update a memory session in Weaviate using v4 SDK"""
        if not self.client:
            logger.warning("Weaviate client not available, skipping update")
            return False
        
        try:
            update_data = {}
            if session_name is not None:
                update_data["session_name"] = session_name
            if summary is not None:
                update_data["summary"] = summary
            if status is not None:
                update_data["status"] = status
            
            if update_data:
                self.client.collections.get("MemorySession").data.update(
                    uuid=embedding_id,
                    properties=update_data,
                )
                logger.info(f"✓ Updated memory session: {embedding_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to update memory session {embedding_id}: {e}")
            return False
    
    def delete_memory_session(self, embedding_id: str) -> bool:
        """Delete a memory session from Weaviate"""
        if not self.client:
            logger.warning("Weaviate client not available, skipping delete")
            return False
        
        try:
            self.client.collections.get("MemorySession").data.delete_by_id(embedding_id)
            logger.info(f"✓ Deleted memory session: {embedding_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete memory session {embedding_id}: {e}")
            return False
    
    def search_conversations(
        self,
        query: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Search conversations using semantic similarity with v4 SDK"""
        if not self.client:
            logger.warning("Weaviate client not available, cannot search")
            return []
        
        try:
            results = self.client.collections.get("Conversation").query.near_text(
                query=query,
                limit=limit,
                return_metadata=True
            )
            
            conversations = []
            for result in results.objects:
                obj = {
                    "uuid": result.uuid,
                    **result.properties
                }
                if result.metadata:
                    obj["distance"] = result.metadata.distance
                conversations.append(obj)
            
            logger.info(f"✓ Found {len(conversations)} conversations matching query")
            return conversations
        except Exception as e:
            logger.error(f"Conversation search failed: {e}")
            return []
    
    def search_decisions(
        self,
        query: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Search design decisions using semantic similarity with v4 SDK"""
        if not self.client:
            logger.warning("Weaviate client not available, cannot search")
            return []
        
        try:
            results = self.client.collections.get("Decision").query.near_text(
                query=query,
                limit=limit,
                return_metadata=True
            )
            
            decisions = []
            for result in results.objects:
                obj = {
                    "uuid": result.uuid,
                    **result.properties
                }
                if result.metadata:
                    obj["distance"] = result.metadata.distance
                decisions.append(obj)
            
            logger.info(f"✓ Found {len(decisions)} decisions matching query")
            return decisions
        except Exception as e:
            logger.error(f"Decision search failed: {e}")
            return []
    
    def search_code(
        self,
        query: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Search code snippets using semantic similarity with v4 SDK"""
        if not self.client:
            logger.warning("Weaviate client not available, cannot search")
            return []
        
        try:
            results = self.client.collections.get("CodeSnippet").query.near_text(
                query=query,
                limit=limit,
                return_metadata=True
            )
            
            snippets = []
            for result in results.objects:
                obj = {
                    "uuid": result.uuid,
                    **result.properties
                }
                if result.metadata:
                    obj["distance"] = result.metadata.distance
                snippets.append(obj)
            
            logger.info(f"✓ Found {len(snippets)} code snippets matching query")
            return snippets
        except Exception as e:
            logger.error(f"Code search failed: {e}")
            return []
    
    def search_interactions(
        self,
        query: str,
        limit: int = 10,
        conversation_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Search interactions/messages using semantic similarity with v4 SDK"""
        if not self.client:
            logger.warning("Weaviate client not available, cannot search")
            return []
        
        try:
            collection = self.client.collections.get("Interaction")
            
            # If filtering by conversation_id, use where clause
            if conversation_id:
                from weaviate.classes.query import Filter
                results = collection.query.near_text(
                    query=query,
                    where=Filter.by_property("conversation_id").equal(conversation_id),
                    limit=limit,
                    return_metadata=True
                )
            else:
                results = collection.query.near_text(
                    query=query,
                    limit=limit,
                    return_metadata=True
                )
            
            interactions = []
            for result in results.objects:
                obj = {
                    "uuid": result.uuid,
                    **result.properties
                }
                if result.metadata:
                    obj["distance"] = result.metadata.distance
                interactions.append(obj)
            
            logger.info(f"✓ Found {len(interactions)} interactions matching query")
            return interactions
        except Exception as e:
            logger.error(f"Interaction search failed: {e}")
            return []
    
    def search_architecture_notes(
        self,
        query: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Search architecture notes using semantic similarity with v4 SDK"""
        if not self.client:
            logger.warning("Weaviate client not available, cannot search")
            return []
        
        try:
            results = self.client.collections.get("ArchitectureNote").query.near_text(
                query=query,
                limit=limit,
                return_metadata=True
            )
            
            notes = []
            for result in results.objects:
                obj = {
                    "uuid": result.uuid,
                    **result.properties
                }
                if result.metadata:
                    obj["distance"] = result.metadata.distance
                notes.append(obj)
            
            logger.info(f"✓ Found {len(notes)} architecture notes matching query")
            return notes
        except Exception as e:
            logger.error(f"Architecture note search failed: {e}")
            return []
    
    def search_files(
        self,
        query: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Search files discussed using semantic similarity with v4 SDK"""
        if not self.client:
            logger.warning("Weaviate client not available, cannot search")
            return []
        
        try:
            results = self.client.collections.get("FileDiscussed").query.near_text(
                query=query,
                limit=limit,
                return_metadata=True
            )
            
            files = []
            for result in results.objects:
                obj = {
                    "uuid": result.uuid,
                    **result.properties
                }
                if result.metadata:
                    obj["distance"] = result.metadata.distance
                files.append(obj)
            
            logger.info(f"✓ Found {len(files)} files matching query")
            return files
        except Exception as e:
            logger.error(f"File search failed: {e}")
            return []
    
    def search_sessions(
        self,
        query: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Search memory sessions using semantic similarity with v4 SDK"""
        if not self.client:
            logger.warning("Weaviate client not available, cannot search")
            return []
        
        try:
            results = self.client.collections.get("MemorySession").query.near_text(
                query=query,
                limit=limit,
                return_metadata=True
            )
            
            sessions = []
            for result in results.objects:
                obj = {
                    "uuid": result.uuid,
                    **result.properties
                }
                if result.metadata:
                    obj["distance"] = result.metadata.distance
                sessions.append(obj)
            
            logger.info(f"✓ Found {len(sessions)} sessions matching query")
            return sessions
        except Exception as e:
            logger.error(f"Session search failed: {e}")
            return []
    
    def index_job(
        self,
        job_id: str,
        title: str,
        company: str,
        location: str,
        description: str,
        url: str,
        source: str,
        salary_min: Optional[float] = None,
        salary_max: Optional[float] = None,
        job_type: Optional[str] = None,
        seniority_level: Optional[str] = None,
        posted_date: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> bool:
        """Index a job in Weaviate using v4 SDK"""
        if not self.client:
            logger.warning("Weaviate client not available, skipping job index")
            return False
        
        try:
            properties = {
                "job_id": job_id,
                "title": title,
                "company": company,
                "location": location,
                "description": description,
                "url": url,
                "source": source,
                "salary_min": salary_min,
                "salary_max": salary_max,
                "job_type": job_type or "unknown",
                "seniority_level": seniority_level or "unknown",
                "posted_date": posted_date or "",
                "tags": tags or [],
            }
            
            try:
                # Try to insert first
                self.client.collections.get("Job").data.insert(
                    properties=properties,
                    uuid=job_id,
                )
            except Exception as insert_err:
                # If insert fails, try to update
                if "already exists" in str(insert_err):
                    self.client.collections.get("Job").data.update(
                        uuid=job_id,
                        properties=properties,
                    )
                else:
                    raise
            
            logger.info(f"✓ Indexed job: {job_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to index job {job_id}: {e}")
            return False
    
    def search_jobs(
        self,
        query: str,
        limit: int = 50,
        source: Optional[str] = None,
        job_type: Optional[str] = None,
        location: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Search jobs using semantic similarity with filtering"""
        if not self.client:
            logger.warning("Weaviate client not available, cannot search")
            return []
        
        try:
            collection = self.client.collections.get("Job")
            
            # Build where clause for filters
            where_clause = None
            if source or job_type or location:
                from weaviate.classes.query import Filter
                filters = []
                
                if source:
                    filters.append(Filter.by_property("source").equal(source))
                if job_type:
                    filters.append(Filter.by_property("job_type").equal(job_type))
                if location:
                    filters.append(Filter.by_property("location").contains_substring(location))
                
                if len(filters) == 1:
                    where_clause = filters[0]
                elif len(filters) > 1:
                    where_clause = Filter.multi_field(filters)
            
            # Perform search
            if where_clause:
                results = collection.query.near_text(
                    query=query,
                    where=where_clause,
                    limit=limit,
                    return_metadata=True
                )
            else:
                results = collection.query.near_text(
                    query=query,
                    limit=limit,
                    return_metadata=True
                )
            
            jobs = []
            for result in results.objects:
                obj = {
                    "uuid": result.uuid,
                    **result.properties
                }
                if result.metadata:
                    obj["_additional"] = {"distance": result.metadata.distance}
                jobs.append(obj)
            
            logger.info(f"✓ Found {len(jobs)} jobs matching query")
            return jobs
        except Exception as e:
            logger.error(f"Job search failed: {e}")
            return []
    
    def delete_job(self, job_id: str) -> bool:
        """Delete a job from Weaviate"""
        if not self.client:
            logger.warning("Weaviate client not available, skipping delete")
            return False
        
        try:
            self.client.collections.get("Job").data.delete_by_id(job_id)
            logger.info(f"✓ Deleted job: {job_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete job {job_id}: {e}")
            return False
    
    def archive_object(self, collection_name: str, embedding_id: str) -> bool:
        """Mark a Weaviate object as archived (called when PostgreSQL record is deleted)."""
        if not self.client:
            return False
        from datetime import datetime, timezone
        try:
            self.client.collections.get(collection_name).data.update(
                uuid=embedding_id,
                properties={"archived": True, "archived_at": datetime.now(timezone.utc).isoformat()},
            )
            logger.info(f"✓ Archived {collection_name}: {embedding_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to archive {collection_name}/{embedding_id}: {e}")
            return False

    def index_note(
        self,
        embedding_id: str,
        title: str,
        content: str,
        tags: Optional[List[str]] = None,
        source: Optional[str] = None,
    ) -> bool:
        """Index a free-form note in Weaviate."""
        if not self.client:
            logger.warning("Weaviate client not available, skipping note index")
            return False
        try:
            properties = {
                "title": title,
                "content": content,
                "tags": tags or [],
                "source": source or "",
                "embedding_id": embedding_id,
            }
            try:
                self.client.collections.get("Note").data.insert(properties=properties, uuid=embedding_id)
            except Exception as ins_err:
                if "already exists" in str(ins_err):
                    self.client.collections.get("Note").data.update(uuid=embedding_id, properties=properties)
                else:
                    raise
            logger.info(f"✓ Indexed note: {embedding_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to index note {embedding_id}: {e}")
            return False

    def search_notes(
        self,
        query: str,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """Search free-form notes using semantic similarity."""
        if not self.client:
            return []
        try:
            results = self.client.collections.get("Note").query.near_text(
                query=query, limit=limit, return_metadata=True
            )
            notes = []
            for result in results.objects:
                obj = {"uuid": result.uuid, **result.properties}
                if result.metadata:
                    obj["distance"] = result.metadata.distance
                notes.append(obj)
            logger.info(f"✓ Found {len(notes)} notes matching query")
            return notes
        except Exception as e:
            logger.error(f"Note search failed: {e}")
            return []

    def index_research_question(
        self,
        embedding_id: str,
        question: str,
        status: str = "pending",
        priority: str = "medium",
        context: Optional[str] = None,
        source: Optional[str] = None,
    ) -> bool:
        """Index a research question in Weaviate."""
        if not self.client:
            logger.warning("Weaviate client not available, skipping research_question index")
            return False
        try:
            properties = {
                "question": question,
                "status": status,
                "priority": priority,
                "context": context or "",
                "source": source or "",
                "embedding_id": embedding_id,
            }
            try:
                self.client.collections.get("ResearchQuestion").data.insert(
                    properties=properties, uuid=embedding_id
                )
            except Exception as ins_err:
                if "already exists" in str(ins_err):
                    self.client.collections.get("ResearchQuestion").data.update(
                        uuid=embedding_id, properties=properties
                    )
                else:
                    raise
            logger.info(f"✓ Indexed research question: {embedding_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to index research question {embedding_id}: {e}")
            return False

    def search_research_questions(
        self,
        query: str,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """Search research questions using semantic similarity."""
        if not self.client:
            return []
        try:
            results = self.client.collections.get("ResearchQuestion").query.near_text(
                query=query, limit=limit, return_metadata=True
            )
            hits = []
            for result in results.objects:
                obj = {"uuid": result.uuid, **result.properties}
                if result.metadata:
                    obj["distance"] = result.metadata.distance
                hits.append(obj)
            logger.info(f"✓ Found {len(hits)} research questions matching query")
            return hits
        except Exception as e:
            logger.error(f"Research question search failed: {e}")
            return []

    # ------------------------------------------------------------------ #
    #  National Security Intelligence — ThreatActor                       #
    # ------------------------------------------------------------------ #

    def index_threat_actor(
        self,
        embedding_id: str,
        name: str,
        classification: Optional[str] = None,
        motivation: Optional[str] = None,
        ttps: Optional[List[str]] = None,
    ) -> bool:
        if not self.client:
            return False
        try:
            props = {
                "name": name,
                "classification": classification or "",
                "motivation": motivation or "",
                "ttps": " ".join(ttps or []),
                "embedding_id": embedding_id,
            }
            try:
                self.client.collections.get("ThreatActor").data.insert(properties=props, uuid=embedding_id)
            except Exception as e:
                if "already exists" in str(e):
                    self.client.collections.get("ThreatActor").data.update(uuid=embedding_id, properties=props)
                else:
                    raise
            logger.info(f"✓ Indexed threat actor: {embedding_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to index threat actor {embedding_id}: {e}")
            return False

    def search_threat_actors(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        if not self.client:
            return []
        try:
            results = self.client.collections.get("ThreatActor").query.near_text(
                query=query, limit=limit, return_metadata=True
            )
            return [{"uuid": r.uuid, **r.properties} for r in results.objects]
        except Exception as e:
            logger.error(f"Threat actor search failed: {e}")
            return []

    # ------------------------------------------------------------------ #
    #  National Security Intelligence — SecurityIncident                   #
    # ------------------------------------------------------------------ #

    def index_incident(
        self,
        embedding_id: str,
        title: str,
        description: Optional[str] = None,
        severity: Optional[str] = None,
    ) -> bool:
        if not self.client:
            return False
        try:
            props = {
                "title": title,
                "description": description or "",
                "severity": severity or "medium",
                "embedding_id": embedding_id,
            }
            try:
                self.client.collections.get("SecurityIncident").data.insert(properties=props, uuid=embedding_id)
            except Exception as e:
                if "already exists" in str(e):
                    self.client.collections.get("SecurityIncident").data.update(uuid=embedding_id, properties=props)
                else:
                    raise
            logger.info(f"✓ Indexed security incident: {embedding_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to index security incident {embedding_id}: {e}")
            return False

    def search_incidents(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        if not self.client:
            return []
        try:
            results = self.client.collections.get("SecurityIncident").query.near_text(
                query=query, limit=limit, return_metadata=True
            )
            return [{"uuid": r.uuid, **r.properties} for r in results.objects]
        except Exception as e:
            logger.error(f"Incident search failed: {e}")
            return []

    # ------------------------------------------------------------------ #
    #  National Security Intelligence — IOC                                #
    # ------------------------------------------------------------------ #

    def index_ioc(
        self,
        embedding_id: str,
        ioc_type: str,
        value: str,
        context: Optional[str] = None,
    ) -> bool:
        if not self.client:
            return False
        try:
            props = {
                "ioc_type": ioc_type,
                "value": value,
                "context": context or "",
                "embedding_id": embedding_id,
            }
            try:
                self.client.collections.get("IOC").data.insert(properties=props, uuid=embedding_id)
            except Exception as e:
                if "already exists" in str(e):
                    self.client.collections.get("IOC").data.update(uuid=embedding_id, properties=props)
                else:
                    raise
            logger.info(f"✓ Indexed IOC: {embedding_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to index IOC {embedding_id}: {e}")
            return False

    def search_iocs(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        if not self.client:
            return []
        try:
            results = self.client.collections.get("IOC").query.near_text(
                query=query, limit=limit, return_metadata=True
            )
            return [{"uuid": r.uuid, **r.properties} for r in results.objects]
        except Exception as e:
            logger.error(f"IOC search failed: {e}")
            return []

    # ------------------------------------------------------------------ #
    #  National Security Intelligence — IntelReport                        #
    # ------------------------------------------------------------------ #

    def index_intel_report(
        self,
        embedding_id: str,
        title: str,
        summary: Optional[str] = None,
        content: Optional[str] = None,
    ) -> bool:
        if not self.client:
            return False
        try:
            props = {
                "title": title,
                "summary": summary or "",
                "content": (content or "")[:4000],  # Weaviate text limit guard
                "embedding_id": embedding_id,
            }
            try:
                self.client.collections.get("IntelReport").data.insert(properties=props, uuid=embedding_id)
            except Exception as e:
                if "already exists" in str(e):
                    self.client.collections.get("IntelReport").data.update(uuid=embedding_id, properties=props)
                else:
                    raise
            logger.info(f"✓ Indexed intel report: {embedding_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to index intel report {embedding_id}: {e}")
            return False

    def search_intel_reports(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        if not self.client:
            return []
        try:
            results = self.client.collections.get("IntelReport").query.near_text(
                query=query, limit=limit, return_metadata=True
            )
            return [{"uuid": r.uuid, **r.properties} for r in results.objects]
        except Exception as e:
            logger.error(f"Intel report search failed: {e}")
            return []

    # -----------------------------------------------------------------------
    #  Vulnerable Code / Patches — VulnPatch                               #
    # -----------------------------------------------------------------------

    def index_vuln_patch(
        self,
        embedding_id: str,
        title: str,
        description: str = "",
        vulnerable_code: str = "",
        patched_code: str = "",
        patch_explanation: str = "",
    ) -> bool:
        """Index a vulnerable/patched code pair in Weaviate."""
        if not self.client:
            return False
        try:
            props = {
                "title": title,
                "description": description[:2000],
                "vulnerable_code": vulnerable_code[:4000],
                "patched_code": patched_code[:4000],
                "patch_explanation": patch_explanation[:2000],
                "embedding_id": embedding_id,
                "archived": False,
                "archived_at": "",
            }
            try:
                self.client.collections.get("VulnPatch").data.insert(properties=props, uuid=embedding_id)
            except Exception as e:
                if "already exists" in str(e):
                    self.client.collections.get("VulnPatch").data.update(uuid=embedding_id, properties=props)
                else:
                    raise
            return True
        except Exception as e:
            logger.error(f"Failed to index vuln_patch {embedding_id}: {e}")
            return False

    def search_vuln_patches(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Semantic search over vulnerable/patched code pairs."""
        if not self.client:
            return []
        try:
            results = self.client.collections.get("VulnPatch").query.near_text(
                query=query, limit=limit, return_metadata=True
            )
            return [{"uuid": r.uuid, **r.properties} for r in results.objects]
        except Exception as e:
            logger.error(f"VulnPatch search failed: {e}")
            return []

    # -----------------------------------------------------------------------
    #  Tasks                                                               #
    # -----------------------------------------------------------------------

    def index_task(
        self,
        embedding_id: str,
        title: str,
        description: str = "",
        status: str = "open",
        priority: str = "medium",
        project: str = "",
        assignee: str = "",
    ) -> bool:
        if not self.client:
            return False
        try:
            props = {
                "title": title,
                "description": description[:2000],
                "status": status,
                "priority": priority,
                "project": project,
                "assignee": assignee,
                "embedding_id": embedding_id,
                "archived": False,
                "archived_at": "",
            }
            try:
                self.client.collections.get("Task").data.insert(properties=props, uuid=embedding_id)
            except Exception as e:
                if "already exists" in str(e):
                    self.client.collections.get("Task").data.update(uuid=embedding_id, properties=props)
                else:
                    raise
            return True
        except Exception as e:
            logger.error(f"Failed to index task {embedding_id}: {e}")
            return False

    def search_tasks(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        if not self.client:
            return []
        try:
            results = self.client.collections.get("Task").query.near_text(
                query=query, limit=limit, return_metadata=True
            )
            return [{"uuid": r.uuid, **r.properties} for r in results.objects]
        except Exception as e:
            logger.error(f"Task search failed: {e}")
            return []

    # -----------------------------------------------------------------------
    #  Runbooks                                                             #
    # -----------------------------------------------------------------------

    def index_runbook(
        self,
        embedding_id: str,
        title: str,
        description: str = "",
        category: str = "",
        trigger: str = "",
        prerequisites: str = "",
        severity: str = "",
    ) -> bool:
        if not self.client:
            return False
        try:
            props = {
                "title": title,
                "description": description[:2000],
                "category": category,
                "trigger": trigger[:2000],
                "prerequisites": prerequisites[:2000],
                "severity": severity,
                "embedding_id": embedding_id,
                "archived": False,
                "archived_at": "",
            }
            try:
                self.client.collections.get("Runbook").data.insert(properties=props, uuid=embedding_id)
            except Exception as e:
                if "already exists" in str(e):
                    self.client.collections.get("Runbook").data.update(uuid=embedding_id, properties=props)
                else:
                    raise
            return True
        except Exception as e:
            logger.error(f"Failed to index runbook {embedding_id}: {e}")
            return False

    def search_runbooks(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        if not self.client:
            return []
        try:
            results = self.client.collections.get("Runbook").query.near_text(
                query=query, limit=limit, return_metadata=True
            )
            return [{"uuid": r.uuid, **r.properties} for r in results.objects]
        except Exception as e:
            logger.error(f"Runbook search failed: {e}")
            return []

    # -----------------------------------------------------------------------
    #  API Contracts                                                        #
    # -----------------------------------------------------------------------

    def index_api_contract(
        self,
        embedding_id: str,
        title: str,
        service_name: str = "",
        version: str = "",
        spec_format: str = "",
        base_url: str = "",
        spec_content: str = "",
        status: str = "active",
        breaking_changes: str = "",
    ) -> bool:
        if not self.client:
            return False
        try:
            props = {
                "title": title,
                "service_name": service_name,
                "version": version,
                "spec_format": spec_format,
                "base_url": base_url,
                "spec_content": spec_content[:4000],
                "status": status,
                "breaking_changes": breaking_changes[:2000],
                "embedding_id": embedding_id,
                "archived": False,
                "archived_at": "",
            }
            try:
                self.client.collections.get("ApiContract").data.insert(properties=props, uuid=embedding_id)
            except Exception as e:
                if "already exists" in str(e):
                    self.client.collections.get("ApiContract").data.update(uuid=embedding_id, properties=props)
                else:
                    raise
            return True
        except Exception as e:
            logger.error(f"Failed to index api_contract {embedding_id}: {e}")
            return False

    def search_api_contracts(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        if not self.client:
            return []
        try:
            results = self.client.collections.get("ApiContract").query.near_text(
                query=query, limit=limit, return_metadata=True
            )
            return [{"uuid": r.uuid, **r.properties} for r in results.objects]
        except Exception as e:
            logger.error(f"ApiContract search failed: {e}")
            return []

    # -----------------------------------------------------------------------
    #  Dependencies                                                         #
    # -----------------------------------------------------------------------

    def index_dependency(
        self,
        embedding_id: str,
        name: str,
        version: str = "",
        ecosystem: str = "",
        project: str = "",
        status: str = "ok",
        license: str = "",
        notes: str = "",
    ) -> bool:
        if not self.client:
            return False
        try:
            props = {
                "name": name,
                "version": version,
                "ecosystem": ecosystem,
                "project": project,
                "status": status,
                "license": license,
                "notes": notes[:2000],
                "embedding_id": embedding_id,
                "archived": False,
                "archived_at": "",
            }
            try:
                self.client.collections.get("Dependency").data.insert(properties=props, uuid=embedding_id)
            except Exception as e:
                if "already exists" in str(e):
                    self.client.collections.get("Dependency").data.update(uuid=embedding_id, properties=props)
                else:
                    raise
            return True
        except Exception as e:
            logger.error(f"Failed to index dependency {embedding_id}: {e}")
            return False

    def search_dependencies(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        if not self.client:
            return []
        try:
            results = self.client.collections.get("Dependency").query.near_text(
                query=query, limit=limit, return_metadata=True
            )
            return [{"uuid": r.uuid, **r.properties} for r in results.objects]
        except Exception as e:
            logger.error(f"Dependency search failed: {e}")
            return []

    def health_check(self) -> bool:
        """Check if Weaviate is healthy"""
        if not self.client:
            logger.warning("Weaviate client is not initialized")
            return False
        
        try:
            if hasattr(self.client, 'is_ready'):
                is_ready = self.client.is_ready()
                logger.info(f"✓ Weaviate is ready: {is_ready}")
                return is_ready
            else:
                logger.warning("Weaviate client does not have is_ready method")
                return True
        except Exception as e:
            logger.error(f"Weaviate health check failed: {e}")
            return False


# Global instance
weaviate_service: Optional[WeaviateService] = None


def get_weaviate_service() -> WeaviateService:
    """Get or create Weaviate service instance"""
    global weaviate_service
    if weaviate_service is None:
        weaviate_service = WeaviateService()
    return weaviate_service
