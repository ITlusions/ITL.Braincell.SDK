"""Conversations memory cell."""
from fastapi import APIRouter

from itl_braincell_sdk.cells.base import MemoryCell


class ConversationsCell(MemoryCell):
    """Memory cell for conversations — tracks session topics and summaries."""

    @property
    def name(self) -> str:
        return "conversations"

    @property
    def prefix(self) -> str:
        return "/api/conversations"

    def get_router(self) -> APIRouter:
        from itl_braincell_sdk.cells.conversations.routes import router
        return router

    def get_models(self) -> list:
        from itl_braincell_sdk.cells.conversations.model import Conversation
        return [Conversation]

    def register_mcp_tools(self, mcp) -> None:
        from itl_braincell_sdk.core.database import SyncSessionLocal
        from itl_braincell_sdk.cells.conversations.model import Conversation

        @mcp.tool()
        async def conversations_search(query: str, limit: int = 10) -> dict:
            """Search conversation summaries by topic or overall summary text.

            Use when looking for a past discussion about a broad topic or subject area.
            Returns conversation-level summaries, not individual messages.
            For specific message content use interactions_search.
            """
            db = SyncSessionLocal()
            try:
                wv_hits = []
                try:
                    from itl_braincell_sdk.services.weaviate_service import get_weaviate_service as _gwvs
                    wv_hits = _gwvs().search_conversations(query, limit=limit * 2)
                except Exception:
                    pass
                if wv_hits:
                    from uuid import UUID as _UUID
                    live_ids = [h["embedding_id"] for h in wv_hits if not h.get("archived") and h.get("embedding_id")]
                    archived_list = [
                        {"id": h.get("embedding_id"), "archived": True,
                         "topic": h.get("topic"), "summary": h.get("summary")}
                        for h in wv_hits if h.get("archived")
                    ]
                    rows = db.query(Conversation).filter(
                        Conversation.id.in_([_UUID(i) for i in live_ids if i])
                    ).limit(limit).all()
                    return {"query": query, "count": len(rows) + len(archived_list),
                            "results": [{"id": str(r.id), "topic": r.topic, "summary": r.summary} for r in rows],
                            "archived": archived_list}
                q = query.lower()
                rows = db.query(Conversation).filter(
                    Conversation.topic.ilike(f"%{q}%") | Conversation.summary.ilike(f"%{q}%")
                ).limit(limit).all()
                return {"query": query, "count": len(rows), "results": [
                    {"id": str(r.id), "topic": r.topic, "summary": r.summary}
                    for r in rows
                ]}
            finally:
                db.close()

        @mcp.tool()
        async def conversations_save(
            topic: str,
            summary: str | None = None,
            session_id: str | None = None,
            retention_days: int | None = None,
            retain_reason: str | None = None,
        ) -> dict:
            """Save a conversation summary to memory.

            Use when a conversation has concluded or reached a milestone and you want
            to store its topic and key points. Captures the topic and a high-level summary.
            Not for raw messages — use interactions_save for individual turns.
            Not for session progress — use sessions_save.
            """
            if not topic:
                return {"error": "topic is required"}
            from uuid import UUID
            from itl_braincell_sdk.services.retention_policy import evaluate as _retention
            retention = _retention("conversations", {"topic": topic, "summary": summary or ""})
            if retention_days is not None:
                retention.retention_days = retention_days
            if retain_reason is not None:
                retention.reason = retain_reason
            if not retention.should_save:
                return {"saved": False, "reason": retention.reason}
            db = SyncSessionLocal()
            try:
                conv = Conversation(
                    topic=topic,
                    summary=summary,
                    session_id=UUID(session_id) if session_id else None,
                    retention_days=retention.retention_days,
                    retain_reason=retention.reason,
                    expires_at=retention.expires_at,
                )
                db.add(conv)
                db.commit()
                db.refresh(conv)
                try:
                    from itl_braincell_sdk.services.weaviate_service import get_weaviate_service as _gwvs
                    _gwvs().index_conversation(
                        str(conv.id), topic=topic,
                        summary=summary or "",
                        session_id=session_id,
                    )
                except Exception:
                    pass
                return {"success": True, "id": str(conv.id), "topic": topic, "retention_days": retention.retention_days, "retain_reason": retention.reason}
            finally:
                db.close()

        @mcp.tool()
        async def conversations_list(limit: int = 50) -> dict:
            """List recent conversation summaries.

            Use to see what topics have been discussed recently at a high level.
            For raw message history use interactions_list.
            """
            db = SyncSessionLocal()
            try:
                rows = db.query(Conversation).order_by(
                    Conversation.created_at.desc()
                ).limit(limit).all()
                return {"count": len(rows), "items": [
                    {"id": str(r.id), "topic": r.topic, "summary": r.summary}
                    for r in rows
                ]}
            finally:
                db.close()


cell = ConversationsCell()
