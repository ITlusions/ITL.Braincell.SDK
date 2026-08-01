"""Production-ready sync service for PostgreSQL → Weaviate synchronization

Handles initial population and ongoing synchronization of entities from
PostgreSQL to Weaviate vector database for semantic search capabilities.
"""
import logging
from typing import Optional
from sqlalchemy.orm import Session

from itl_braincell_sdk.core.database import SyncSessionLocal
from itl_braincell_sdk.cells.conversations.model import Conversation
from itl_braincell_sdk.cells.interactions.model import Interaction
from itl_braincell_sdk.cells.decisions.model import DesignDecision
from itl_braincell_sdk.cells.architecture_notes.model import ArchitectureNote
from itl_braincell_sdk.cells.files_discussed.model import FileDiscussed
from itl_braincell_sdk.cells.snippets.model import CodeSnippet
from itl_braincell_sdk.cells.sessions.model import MemorySession
from itl_braincell_sdk.services.weaviate_service import get_weaviate_service

logger = logging.getLogger(__name__)


class SyncService:
    """Manages synchronization from PostgreSQL to Weaviate"""
    
    def __init__(self):
        self.weaviate = get_weaviate_service()
        self.db: Optional[Session] = None
        self.stats = {
            "processed": 0,
            "success": 0,
            "failed": 0,
            "errors": []
        }
    
    def _get_db(self) -> Session:
        """Get database session"""
        if not self.db:
            self.db = SyncSessionLocal()
        return self.db
    
    def close(self):
        """Close database connection"""
        if self.db:
            self.db.close()
            self.db = None
    
    def sync_conversations(self) -> int:
        """Sync conversations from PostgreSQL to Weaviate"""
        logger.info("Syncing conversations...")
        db = self._get_db()
        count = 0
        
        try:
            conversations = db.query(Conversation).all()
            logger.info(f"Found {len(conversations)} conversations in PostgreSQL")
            
            for conv in conversations:
                try:
                    success = self.weaviate.index_conversation(
                        str(conv.id),
                        conv.topic,
                        conv.summary,
                        str(conv.session_id)
                    )
                    if success:
                        count += 1
                        self.stats["success"] += 1
                    else:
                        logger.warning(f"Failed to index conversation {conv.id}")
                        self.stats["failed"] += 1
                except Exception as e:
                    logger.error(f"Error indexing conversation {conv.id}: {e}")
                    self.stats["failed"] += 1
                    self.stats["errors"].append(f"Conversation {conv.id}: {str(e)}")
                finally:
                    self.stats["processed"] += 1
        
        except Exception as e:
            logger.error(f"Error syncing conversations: {e}")
            self.stats["errors"].append(f"Conversations: {str(e)}")
        
        logger.info(f"✓ Synced {count} conversations")
        return count
    
    def sync_interactions(self) -> int:
        """Sync interactions from PostgreSQL to Weaviate"""
        logger.info("Syncing interactions...")
        db = self._get_db()
        count = 0
        
        try:
            interactions = db.query(Interaction).all()
            logger.info(f"Found {len(interactions)} interactions in PostgreSQL")
            
            for interaction in interactions:
                try:
                    success = self.weaviate.index_interaction(
                        str(interaction.id),
                        interaction.content,
                        interaction.role,
                        interaction.message_type,
                        str(interaction.conversation_id),
                        str(interaction.session_id)
                    )
                    if success:
                        count += 1
                        self.stats["success"] += 1
                    else:
                        logger.warning(f"Failed to index interaction {interaction.id}")
                        self.stats["failed"] += 1
                except Exception as e:
                    logger.error(f"Error indexing interaction {interaction.id}: {e}")
                    self.stats["failed"] += 1
                    self.stats["errors"].append(f"Interaction {interaction.id}: {str(e)}")
                finally:
                    self.stats["processed"] += 1
        
        except Exception as e:
            logger.error(f"Error syncing interactions: {e}")
            self.stats["errors"].append(f"Interactions: {str(e)}")
        
        logger.info(f"✓ Synced {count} interactions")
        return count
    
    def sync_decisions(self) -> int:
        """Sync design decisions from PostgreSQL to Weaviate"""
        logger.info("Syncing design decisions...")
        db = self._get_db()
        count = 0
        
        try:
            decisions = db.query(DesignDecision).all()
            logger.info(f"Found {len(decisions)} decisions in PostgreSQL")
            
            for decision in decisions:
                try:
                    success = self.weaviate.index_decision(
                        str(decision.id),
                        decision.decision,
                        decision.rationale
                    )
                    if success:
                        count += 1
                        self.stats["success"] += 1
                    else:
                        logger.warning(f"Failed to index decision {decision.id}")
                        self.stats["failed"] += 1
                except Exception as e:
                    logger.error(f"Error indexing decision {decision.id}: {e}")
                    self.stats["failed"] += 1
                    self.stats["errors"].append(f"Decision {decision.id}: {str(e)}")
                finally:
                    self.stats["processed"] += 1
        
        except Exception as e:
            logger.error(f"Error syncing decisions: {e}")
            self.stats["errors"].append(f"Decisions: {str(e)}")
        
        logger.info(f"✓ Synced {count} decisions")
        return count
    
    def sync_architecture_notes(self) -> int:
        """Sync architecture notes from PostgreSQL to Weaviate"""
        logger.info("Syncing architecture notes...")
        db = self._get_db()
        count = 0
        
        try:
            notes = db.query(ArchitectureNote).all()
            logger.info(f"Found {len(notes)} architecture notes in PostgreSQL")
            
            for note in notes:
                try:
                    success = self.weaviate.index_architecture_note(
                        str(note.id),
                        note.component,
                        note.description,
                        note.type,
                        note.tags
                    )
                    if success:
                        count += 1
                        self.stats["success"] += 1
                    else:
                        logger.warning(f"Failed to index architecture note {note.id}")
                        self.stats["failed"] += 1
                except Exception as e:
                    logger.error(f"Error indexing architecture note {note.id}: {e}")
                    self.stats["failed"] += 1
                    self.stats["errors"].append(f"Architecture Note {note.id}: {str(e)}")
                finally:
                    self.stats["processed"] += 1
        
        except Exception as e:
            logger.error(f"Error syncing architecture notes: {e}")
            self.stats["errors"].append(f"Architecture Notes: {str(e)}")
        
        logger.info(f"✓ Synced {count} architecture notes")
        return count
    
    def sync_files(self) -> int:
        """Sync discussed files from PostgreSQL to Weaviate"""
        logger.info("Syncing discussed files...")
        db = self._get_db()
        count = 0
        
        try:
            files = db.query(FileDiscussed).all()
            logger.info(f"Found {len(files)} files in PostgreSQL")
            
            for file in files:
                try:
                    success = self.weaviate.index_file_discussed(
                        str(file.id),
                        file.file_path,
                        file.description,
                        file.language,
                        file.purpose
                    )
                    if success:
                        count += 1
                        self.stats["success"] += 1
                    else:
                        logger.warning(f"Failed to index file {file.id}")
                        self.stats["failed"] += 1
                except Exception as e:
                    logger.error(f"Error indexing file {file.id}: {e}")
                    self.stats["failed"] += 1
                    self.stats["errors"].append(f"File {file.id}: {str(e)}")
                finally:
                    self.stats["processed"] += 1
        
        except Exception as e:
            logger.error(f"Error syncing files: {e}")
            self.stats["errors"].append(f"Files: {str(e)}")
        
        logger.info(f"✓ Synced {count} files")
        return count
    
    def sync_code_snippets(self) -> int:
        """Sync code snippets from PostgreSQL to Weaviate"""
        logger.info("Syncing code snippets...")
        db = self._get_db()
        count = 0
        
        try:
            snippets = db.query(CodeSnippet).all()
            logger.info(f"Found {len(snippets)} snippets in PostgreSQL")
            
            for snippet in snippets:
                try:
                    success = self.weaviate.index_code_snippet(
                        str(snippet.id),
                        snippet.title,
                        snippet.code_content,
                        snippet.language
                    )
                    if success:
                        count += 1
                        self.stats["success"] += 1
                    else:
                        logger.warning(f"Failed to index code snippet {snippet.id}")
                        self.stats["failed"] += 1
                except Exception as e:
                    logger.error(f"Error indexing code snippet {snippet.id}: {e}")
                    self.stats["failed"] += 1
                    self.stats["errors"].append(f"CodeSnippet {snippet.id}: {str(e)}")
                finally:
                    self.stats["processed"] += 1
        
        except Exception as e:
            logger.error(f"Error syncing code snippets: {e}")
            self.stats["errors"].append(f"CodeSnippets: {str(e)}")
        
        logger.info(f"✓ Synced {count} code snippets")
        return count
    
    def sync_sessions(self) -> int:
        """Sync memory sessions from PostgreSQL to Weaviate"""
        logger.info("Syncing memory sessions...")
        db = self._get_db()
        count = 0
        
        try:
            sessions = db.query(MemorySession).all()
            logger.info(f"Found {len(sessions)} sessions in PostgreSQL")
            
            for session in sessions:
                try:
                    success = self.weaviate.index_memory_session(
                        str(session.id),
                        session.session_name,
                        session.summary,
                        session.status
                    )
                    if success:
                        count += 1
                        self.stats["success"] += 1
                    else:
                        logger.warning(f"Failed to index session {session.id}")
                        self.stats["failed"] += 1
                except Exception as e:
                    logger.error(f"Error indexing session {session.id}: {e}")
                    self.stats["failed"] += 1
                    self.stats["errors"].append(f"Session {session.id}: {str(e)}")
                finally:
                    self.stats["processed"] += 1
        
        except Exception as e:
            logger.error(f"Error syncing sessions: {e}")
            self.stats["errors"].append(f"Sessions: {str(e)}")
        
        logger.info(f"✓ Synced {count} sessions")
        return count
    
    def sync_all(self) -> dict:
        """Perform complete synchronization of all entities
        
        Returns:
            dict: Statistics about the sync operation including counts and errors
        """
        logger.info("=" * 80)
        logger.info("STARTING COMPLETE SYNC: PostgreSQL → Weaviate")
        logger.info("=" * 80)
        
        self.stats = {
            "processed": 0,
            "success": 0,
            "failed": 0,
            "errors": []
        }
        
        try:
            # Sync all entity types
            self.sync_conversations()
            self.sync_interactions()
            self.sync_decisions()
            self.sync_architecture_notes()
            self.sync_files()
            self.sync_code_snippets()
            self.sync_sessions()
            
            log_message = (
                f"\n{'=' * 80}\n"
                f"SYNC COMPLETE\n"
                f"{'=' * 80}\n"
                f"Total Processed: {self.stats['processed']}\n"
                f"Successful: {self.stats['success']}\n"
                f"Failed: {self.stats['failed']}\n"
            )
            
            if self.stats['errors']:
                log_message += f"\nErrors ({len(self.stats['errors'])}):\n"
                for error in self.stats['errors']:
                    log_message += f"  • {error}\n"
            
            logger.info(log_message)
            
        except Exception as e:
            logger.error(f"Critical error during sync: {e}")
            self.stats["errors"].append(f"Critical error: {str(e)}")
        
        finally:
            self.close()
        
        return self.stats


def perform_sync() -> dict:
    """Convenience function to perform full sync
    
    Returns:
        dict: Statistics about the sync operation
    """
    sync_service = SyncService()
    return sync_service.sync_all()
