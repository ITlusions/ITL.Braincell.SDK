"""Jobs memory cell — Weaviate-only, no PostgreSQL entities."""
from fastapi import APIRouter

from itl_braincell_sdk.cells.base import MemoryCell


class JobsCell(MemoryCell):
    """Memory cell for job postings — stores and searches jobs via Weaviate vector DB."""

    @property
    def name(self) -> str:
        return "jobs"

    @property
    def prefix(self) -> str:
        return "/api/jobs"

    def get_router(self) -> APIRouter:
        from itl_braincell_sdk.cells.jobs.routes import router
        return router

    def get_models(self) -> list:
        return []  # Weaviate-only, no SQL tables

    def register_mcp_tools(self, mcp) -> None:
        from datetime import datetime, timezone
        from itl_braincell_sdk.core.database import SyncSessionLocal
        from itl_braincell_sdk.services.weaviate_service import get_weaviate_service as _gwvs
        from itl_braincell_sdk.cells.interactions.model import Interaction
        from itl_braincell_sdk.cells.conversations.model import Conversation
        from itl_braincell_sdk.cells.decisions.model import DesignDecision
        from itl_braincell_sdk.cells.architecture_notes.model import ArchitectureNote
        from itl_braincell_sdk.cells.notes.model import Note
        from itl_braincell_sdk.cells.snippets.model import CodeSnippet
        from itl_braincell_sdk.cells.files_discussed.model import FileDiscussed
        from itl_braincell_sdk.cells.sessions.model import MemorySession
        from itl_braincell_sdk.cells.threats.model import ThreatActor
        from itl_braincell_sdk.cells.incidents.model import SecurityIncident
        from itl_braincell_sdk.cells.iocs.model import IOC
        from itl_braincell_sdk.cells.intel_reports.model import IntelReport
        from itl_braincell_sdk.cells.vuln_patches.model import VulnPatch
        from itl_braincell_sdk.cells.tasks.model import Task
        from itl_braincell_sdk.cells.runbooks.model import Runbook
        from itl_braincell_sdk.cells.api_contracts.model import ApiContract
        from itl_braincell_sdk.cells.dependencies.model import Dependency

        CELL_MAP = [
            ("Interaction", Interaction),
            ("Conversation", Conversation),
            ("Decision", DesignDecision),
            ("ArchitectureNote", ArchitectureNote),
            ("Note", Note),
            ("CodeSnippet", CodeSnippet),
            ("FileDiscussed", FileDiscussed),
            ("MemorySession", MemorySession),
            ("ThreatActor", ThreatActor),
            ("SecurityIncident", SecurityIncident),
            ("IOC", IOC),
            ("IntelReport", IntelReport),
            ("VulnPatch", VulnPatch),
            ("Task", Task),
            ("Runbook", Runbook),
            ("ApiContract", ApiContract),
            ("Dependency", Dependency),
        ]

        @mcp.tool()
        async def memory_cleanup() -> dict:
            """Archive expired PostgreSQL records to Weaviate and delete them from PostgreSQL.

            Run this daily (or on demand) to maintain the layered memory model:
            - Active records live in PostgreSQL + Weaviate (archived=false)
            - After expiry: PostgreSQL record is deleted, Weaviate vector is marked archived=true
            - Archived vectors remain searchable forever as semantic long-term memory

            Returns a summary of archived and deleted counts per collection.
            """
            wv = _gwvs()
            now = datetime.now(timezone.utc)
            stats = {}
            db = SyncSessionLocal()
            try:
                for collection_name, Model in CELL_MAP:
                    expired = db.query(Model).filter(
                        Model.expires_at.isnot(None),
                        Model.expires_at < now,
                    ).all()
                    archived = 0
                    deleted = 0
                    for row in expired:
                        try:
                            wv.archive_object(collection_name, str(row.id))
                            archived += 1
                        except Exception:
                            pass
                        db.delete(row)
                        deleted += 1
                    db.commit()
                    stats[collection_name] = {"archived": archived, "deleted": deleted}
            finally:
                db.close()
            return {"success": True, "stats": stats, "ran_at": now.isoformat()}


cell = JobsCell()
