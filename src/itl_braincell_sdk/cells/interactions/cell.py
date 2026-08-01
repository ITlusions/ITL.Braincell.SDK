"""Interactions memory cell."""
from fastapi import APIRouter

from itl_braincell_sdk.cells.base import MemoryCell


class InteractionsCell(MemoryCell):
    """Memory cell for interactions — individual messages within conversations."""

    @property
    def name(self) -> str:
        return "interactions"

    @property
    def prefix(self) -> str:
        return "/api/interactions"

    def get_router(self) -> APIRouter:
        from itl_braincell_sdk.cells.interactions.routes import router
        return router

    def get_models(self) -> list:
        from itl_braincell_sdk.cells.interactions.model import Interaction
        return [Interaction]

    def register_mcp_tools(self, mcp) -> None:
        from itl_braincell_sdk.core.database import SyncSessionLocal
        from itl_braincell_sdk.cells.interactions.model import Interaction

        @mcp.tool()
        async def interactions_search(query: str, limit: int = 10) -> dict:
            """Search individual messages or chat turns by content or speaker role.

            Use when looking for what was specifically said in a message, a particular
            user request, or an assistant response. Matches on the raw message text
            and role (user/assistant/system).
            Not for conversation-level topics — use conversations_search instead.
            """
            db = SyncSessionLocal()
            try:
                # Try Weaviate vector search first
                wv_hits = []
                try:
                    from itl_braincell_sdk.services.weaviate_service import get_weaviate_service as _gwvs
                    wv_hits = _gwvs().search_interactions(query, limit=limit * 2)
                except Exception:
                    pass
                if wv_hits:
                    from uuid import UUID as _UUID
                    live_ids = [h["embedding_id"] for h in wv_hits if not h.get("archived") and h.get("embedding_id")]
                    archived_list = [
                        {"id": h.get("embedding_id"), "archived": True,
                         "role": h.get("role"), "content": (h.get("content") or "")[:200],
                         "message_type": h.get("message_type")}
                        for h in wv_hits if h.get("archived")
                    ]
                    rows = db.query(Interaction).filter(
                        Interaction.id.in_([_UUID(i) for i in live_ids if i])
                    ).limit(limit).all()
                    return {"query": query, "count": len(rows) + len(archived_list),
                            "results": [{"id": str(r.id), "role": r.role, "content": (r.content or "")[:200], "message_type": r.message_type} for r in rows],
                            "archived": archived_list}
                # Fallback: ILIKE
                q = query.lower()
                rows = db.query(Interaction).filter(
                    Interaction.content.ilike(f"%{q}%") | Interaction.role.ilike(f"%{q}%")
                ).limit(limit).all()
                return {"query": query, "count": len(rows), "results": [
                    {"id": str(r.id), "role": r.role,
                     "content": (r.content or "")[:200], "message_type": r.message_type}
                    for r in rows
                ]}
            finally:
                db.close()

        @mcp.tool()
        async def interactions_save(
            role: str,
            content: str,
            message_type: str | None = None,
            conversation_id: str | None = None,
            session_id: str | None = None,
            retention_days: int | None = None,
            retain_reason: str | None = None,
        ) -> dict:
            """Save a single message or chat turn to memory.

            Use when recording an individual user/assistant exchange, a tool output,
            or any raw message-level content. role must be 'user', 'assistant', or 'system'.
            For a whole conversation summary use conversations_save.
            For a session-level summary use sessions_save.
            """
            if not role or not content:
                return {"error": "role and content are required"}
            from uuid import UUID
            from itl_braincell_sdk.services.retention_policy import evaluate as _retention
            retention = _retention("interactions", {"role": role, "content": content})
            if retention_days is not None:
                retention.retention_days = retention_days
            if retain_reason is not None:
                retention.reason = retain_reason
            if not retention.should_save:
                return {"saved": False, "reason": retention.reason}
            db = SyncSessionLocal()
            try:
                interaction = Interaction(
                    role=role, content=content, message_type=message_type,
                    conversation_id=UUID(conversation_id) if conversation_id else None,
                    session_id=UUID(session_id) if session_id else None,
                    retention_days=retention.retention_days,
                    retain_reason=retention.reason,
                    expires_at=retention.expires_at,
                )
                db.add(interaction)
                db.commit()
                db.refresh(interaction)
                try:
                    from itl_braincell_sdk.services.weaviate_service import get_weaviate_service as _gwvs
                    _gwvs().index_interaction(
                        str(interaction.id), content=content, role=role,
                        message_type=message_type or "",
                        conversation_id=conversation_id,
                        session_id=session_id,
                    )
                except Exception:
                    pass
                # ── Auto-detect: research questions (user messages) ──────────────
                if role == "user":
                    try:
                        from itl_braincell_sdk.cells.research_questions.cell import _is_question
                        if _is_question(content):
                            from itl_braincell_sdk.cells.research_questions.model import ResearchQuestion as _RQ
                            from itl_braincell_sdk.services.weaviate_service import get_weaviate_service as _gwvs2
                            _rq = _RQ(
                                question=content.strip(),
                                status="pending",
                                priority="medium",
                                source="auto_detected",
                                source_interaction_id=interaction.id,
                            )
                            db2 = SessionLocal()
                            try:
                                db2.add(_rq)
                                db2.commit()
                                db2.refresh(_rq)
                                try:
                                    _gwvs2().index_research_question(
                                        str(_rq.id),
                                        question=_rq.question,
                                        status=_rq.status,
                                        priority=_rq.priority,
                                        source=_rq.source,
                                    )
                                except Exception:
                                    pass
                            finally:
                                db2.close()
                    except Exception:
                        pass

                # ── Auto-detect: code snippets (assistant messages with code fences) ──
                if role == "assistant":
                    try:
                        import re as _re
                        _code_blocks = _re.findall(
                            r"```(\w*)\n(.*?)```", content, _re.DOTALL
                        )
                        if _code_blocks:
                            from itl_braincell_sdk.cells.snippets.model import CodeSnippet as _CS
                            from itl_braincell_sdk.services.weaviate_service import get_weaviate_service as _gwvs3
                            db3 = SessionLocal()
                            try:
                                for _lang, _code in _code_blocks:
                                    _code = _code.strip()
                                    if len(_code) < 10:
                                        continue
                                    _title = f"Auto-detected {_lang or 'code'} snippet"
                                    _cs = _CS(
                                        title=_title,
                                        code_content=_code,
                                        language=_lang or None,
                                        meta_data={"source_interaction_id": str(interaction.id)},
                                    )
                                    db3.add(_cs)
                                    db3.commit()
                                    db3.refresh(_cs)
                                    try:
                                        _gwvs3().index_code_snippet(
                                            str(_cs.id),
                                            title=_title,
                                            code_content=_code,
                                            language=_lang or None,
                                        )
                                    except Exception:
                                        pass
                            finally:
                                db3.close()
                    except Exception:
                        pass

                # ── Auto-detect: files discussed (any role, file path patterns) ──────
                try:
                    import re as _re
                    _FILE_PATTERN = _re.compile(
                        r"(?:[a-zA-Z]:[\\/]|\.{1,2}[\\/]|src[\\/]|/[\w])"
                        r"[\w/\\.\\-]+"
                        r"\.(?:py|ts|js|yaml|yml|json|toml|md|sh|tf|bicep|cs|go|rs|java|html|css)"
                    )
                    _found_paths = list(dict.fromkeys(_FILE_PATTERN.findall(content)))
                    if _found_paths:
                        from itl_braincell_sdk.cells.files_discussed.model import FileDiscussed as _FD
                        from itl_braincell_sdk.services.weaviate_service import get_weaviate_service as _gwvs4
                        db4 = SessionLocal()
                        try:
                            for _fp in _found_paths[:10]:
                                _existing = db4.query(_FD).filter(_FD.file_path == _fp).first()
                                if _existing:
                                    _existing.discussion_count = (_existing.discussion_count or 1) + 1
                                    db4.commit()
                                else:
                                    _fd = _FD(
                                        file_path=_fp,
                                        meta_data={"source_interaction_id": str(interaction.id)},
                                    )
                                    db4.add(_fd)
                                    db4.commit()
                                    db4.refresh(_fd)
                                    try:
                                        _gwvs4().index_file_discussed(
                                            str(_fd.id),
                                            file_path=_fp,
                                        )
                                    except Exception:
                                        pass
                        finally:
                            db4.close()
                except Exception:
                    pass

                # ── Auto-detect: design decisions (assistant messages) ───────────────
                if role == "assistant":
                    try:
                        import re as _re
                        _DECISION_PATTERN = _re.compile(
                            r"\b(we\s+(?:gaan|kiezen|gebruiken|besluiten)|besloten\s+om|"
                            r"aanbeveling[:\s]|ik\s+(?:raad|adviseer)|"
                            r"we\s+(?:should|will|are\s+going\s+to)\s+use|"
                            r"i\s+recommend|decided\s+to|going\s+with|"
                            r"best\s+(?:practice|approach)\s+is)\b",
                            _re.IGNORECASE,
                        )
                        if _DECISION_PATTERN.search(content):
                            from itl_braincell_sdk.cells.decisions.model import DesignDecision as _DD
                            from itl_braincell_sdk.services.weaviate_service import get_weaviate_service as _gwvs5
                            _sentence = next(
                                (s.strip() for s in content.split("\n") if _DECISION_PATTERN.search(s)),
                                content[:200],
                            )
                            db5 = SessionLocal()
                            try:
                                _dd = _DD(
                                    decision=_sentence,
                                    rationale="Auto-detected from assistant message",
                                    status="proposed",
                                    meta_data={"source_interaction_id": str(interaction.id)},
                                )
                                db5.add(_dd)
                                db5.commit()
                                db5.refresh(_dd)
                                try:
                                    _gwvs5().index_decision(
                                        str(_dd.id),
                                        decision=_dd.decision,
                                        rationale=_dd.rationale,
                                    )
                                except Exception:
                                    pass
                            finally:
                                db5.close()
                    except Exception:
                        pass

                # ── Auto-answer: link assistant reply to pending research question ───
                if role == "assistant":
                    try:
                        from itl_braincell_sdk.services.weaviate_service import get_weaviate_service as _gwvs6
                        from itl_braincell_sdk.cells.research_questions.model import ResearchQuestion as _RQ2
                        _hits = _gwvs6().search_research_questions(query=content[:500], limit=1)
                        if _hits:
                            _hit = _hits[0]
                            _dist = _hit.get("distance", 1.0)
                            _hit_status = _hit.get("status", "")
                            if _dist is not None and _dist < 0.25 and _hit_status == "pending":
                                _rq_id = _hit.get("embedding_id") or str(_hit.get("uuid", ""))
                                if _rq_id:
                                    db6 = SessionLocal()
                                    try:
                                        from uuid import UUID as _UUID
                                        _rq_obj = db6.query(_RQ2).filter(
                                            _RQ2.id == _UUID(_rq_id)
                                        ).first()
                                        if _rq_obj and _rq_obj.status == "pending":
                                            _rq_obj.status = "answered"
                                            _rq_obj.answer = content[:1000]
                                            db6.commit()
                                            try:
                                                _gwvs6().index_research_question(
                                                    str(_rq_obj.id),
                                                    question=_rq_obj.question,
                                                    status="answered",
                                                    priority=_rq_obj.priority,
                                                    source=_rq_obj.source,
                                                )
                                            except Exception:
                                                pass
                                    finally:
                                        db6.close()
                    except Exception:
                        pass

                # ── Auto-detect: IOCs in any message ────────────────────────────────
                try:
                    from itl_braincell_sdk.cells.iocs.cell import detect_iocs_in_text as _detect_iocs
                    from itl_braincell_sdk.cells.iocs.model import IOC as _IOC
                    from datetime import datetime as _dt, timezone as _tz
                    _now_ioc = _dt.now(_tz.utc)
                    _found_iocs = _detect_iocs(content)
                    if _found_iocs:
                        from itl_braincell_sdk.services.weaviate_service import get_weaviate_service as _gwvs7
                        db7 = SessionLocal()
                        try:
                            for _ioc_type, _ioc_val in _found_iocs[:20]:
                                _existing_ioc = db7.query(_IOC).filter(
                                    _IOC.type == _ioc_type, _IOC.value == _ioc_val
                                ).first()
                                if _existing_ioc:
                                    _existing_ioc.last_seen = _now_ioc
                                    db7.commit()
                                else:
                                    _new_ioc = _IOC(
                                        type=_ioc_type,
                                        value=_ioc_val,
                                        source="auto-detect",
                                        confidence=0.3,
                                        first_seen=_now_ioc,
                                        last_seen=_now_ioc,
                                        meta_data={"source_interaction_id": str(interaction.id)},
                                    )
                                    db7.add(_new_ioc)
                                    db7.commit()
                                    db7.refresh(_new_ioc)
                                    try:
                                        _gwvs7().index_ioc(
                                            str(_new_ioc.id), _ioc_type, _ioc_val
                                        )
                                    except Exception:
                                        pass
                        finally:
                            db7.close()
                except Exception:
                    pass

                return {"success": True, "id": str(interaction.id), "retention_days": retention.retention_days, "retain_reason": retention.reason}
            finally:
                db.close()

        @mcp.tool()
        async def interactions_list(limit: int = 50) -> dict:
            """List recent individual messages across all conversations, newest first.

            Use to review raw chat history at the message level.
            For conversation summaries use conversations_list.
            """
            db = SyncSessionLocal()
            try:
                rows = db.query(Interaction).order_by(
                    Interaction.created_at.desc()
                ).limit(limit).all()
                return {"count": len(rows), "items": [
                    {"id": str(r.id), "role": r.role,
                     "content": (r.content or "")[:100], "message_type": r.message_type}
                    for r in rows
                ]}
            finally:
                db.close()


cell = InteractionsCell()
