"""Research Questions cell — cell definition.

Registers the cell with the BrainCell framework via ``cell = ResearchQuestionsCell()``.

Auto-detection heuristic
------------------------
A message is treated as a research question when it:
- ends with ``?``, **or**
- starts with a known Dutch/English question word
  (wat, wie, wanneer, waar, waarom, hoe, welk(e), can, could, would, should,
   what, when, where, why, how, which, who, is, are, do, does, did, will,
   has, have, was, were, kan, kun, moet, mag)

This heuristic is used by ``question_detect`` and is also wired into
``interactions_save`` (role='user' messages only) for fully automatic capture.
"""
from fastapi import APIRouter

from itl_braincell_sdk.cells.base import MemoryCell

_QUESTION_STARTERS = (
    # Dutch
    "wat ", "wie ", "wanneer ", "waar ", "waarom ", "hoe ", "welk", "welke ",
    "kan ", "kun ", "moet ", "mag ", "zijn ", "is het ",
    # English
    "what ", "when ", "where ", "why ", "how ", "which ", "who ",
    "can ", "could ", "would ", "should ",
    "is ", "are ", "do ", "does ", "did ", "will ", "shall ",
    "has ", "have ", "was ", "were ",
)


def _is_question(text: str) -> bool:
    """Return True if *text* looks like an end-user question."""
    if not text:
        return False
    stripped = text.strip()
    if stripped.endswith("?"):
        return True
    lower = stripped.lower()
    return lower.startswith(_QUESTION_STARTERS)


class ResearchQuestionsCell(MemoryCell):
    """Cell that tracks end-user questions requiring follow-up research."""

    @property
    def name(self) -> str:
        return "research_questions"

    @property
    def prefix(self) -> str:
        return "/api/research-questions"

    def get_router(self) -> APIRouter:
        from itl_braincell_sdk.cells.research_questions.routes import router
        return router

    def get_models(self) -> list:
        from itl_braincell_sdk.cells.research_questions.model import ResearchQuestion
        return [ResearchQuestion]

    def register_mcp_tools(self, mcp) -> None:  # noqa: C901
        from itl_braincell_sdk.core.database import SyncSessionLocal
        from itl_braincell_sdk.cells.research_questions.model import ResearchQuestion

        # ------------------------------------------------------------------ #
        #  question_detect                                                     #
        # ------------------------------------------------------------------ #
        @mcp.tool()
        async def question_detect(
            text: str,
            source_interaction_id: str | None = None,
            context: str | None = None,
            priority: str = "medium",
            tags: list[str] | None = None,
        ) -> dict:
            """Detect whether *text* is a research question and, if so, save it.

            Returns ``{"detected": True, "id": "<uuid>"}`` when saved,
            or ``{"detected": False}`` when the text is not a question.

            Use this whenever you receive a user message and want to check
            whether it should be tracked for research follow-up.

            Args:
                text: The raw user message to analyse.
                source_interaction_id: UUID of the interaction this came from.
                context: Optional surrounding context (e.g. conversation snippet).
                priority: low / medium / high — default is medium.
                tags: Optional list of topic tags.
            """
            if not _is_question(text):
                return {"detected": False}

            db = SyncSessionLocal()
            try:
                row = ResearchQuestion(
                    question=text.strip(),
                    status="pending",
                    priority=priority,
                    context=context,
                    source="auto_detected",
                    source_interaction_id=source_interaction_id or None,
                    tags=tags or [],
                )
                db.add(row)
                db.commit()
                db.refresh(row)

                # Index in Weaviate
                try:
                    from itl_braincell_sdk.services.weaviate_service import get_weaviate_service as _gwvs
                    _gwvs().index_research_question(
                        str(row.id),
                        question=row.question,
                        status=row.status,
                        priority=row.priority,
                        context=row.context or "",
                        source=row.source,
                    )
                except Exception:
                    pass

                return {"detected": True, "id": str(row.id), "question": row.question}
            finally:
                db.close()

        # ------------------------------------------------------------------ #
        #  question_save                                                       #
        # ------------------------------------------------------------------ #
        @mcp.tool()
        async def question_save(
            question: str,
            priority: str = "medium",
            context: str | None = None,
            tags: list[str] | None = None,
            source: str = "manual",
            retention_days: int | None = None,
            retain_reason: str | None = None,
        ) -> dict:
            """Manually save a research question for follow-up.

            Use when you identify a question that warrants investigation but
            was not auto-detected (e.g. implicit/rhetorical questions, or
            questions surfaced during summarisation).

            Args:
                question: The question text.
                priority: low / medium / high.
                context: Optional context or background.
                tags: Topic tags.
                source: Origin — defaults to 'manual'.
                retention_days: Override default retention window.
                retain_reason: Human-readable reason for custom retention.
            """
            db = SyncSessionLocal()
            try:
                row = ResearchQuestion(
                    question=question.strip(),
                    status="pending",
                    priority=priority,
                    context=context,
                    source=source,
                    tags=tags or [],
                )
                if retention_days is not None:
                    row.retention_days = retention_days
                if retain_reason is not None:
                    row.retain_reason = retain_reason
                db.add(row)
                db.commit()
                db.refresh(row)

                try:
                    from itl_braincell_sdk.services.weaviate_service import get_weaviate_service as _gwvs
                    _gwvs().index_research_question(
                        str(row.id),
                        question=row.question,
                        status=row.status,
                        priority=row.priority,
                        context=row.context or "",
                        source=row.source,
                    )
                except Exception:
                    pass

                return {
                    "success": True,
                    "id": str(row.id),
                    "question": row.question,
                    "status": row.status,
                    "priority": row.priority,
                }
            finally:
                db.close()

        # ------------------------------------------------------------------ #
        #  question_search                                                     #
        # ------------------------------------------------------------------ #
        @mcp.tool()
        async def question_search(
            query: str,
            limit: int = 10,
            status_filter: str | None = None,
        ) -> dict:
            """Search research questions by semantic similarity.

            Returns both *live* (still in PostgreSQL) and *archived*
            (Weaviate-only) questions so that nothing is forgotten.

            Args:
                query: Natural-language search string.
                limit: Maximum results to return.
                status_filter: Optionally restrict to pending / investigating /
                               answered / closed.
            """
            db = SyncSessionLocal()
            try:
                wv_hits = []
                try:
                    from itl_braincell_sdk.services.weaviate_service import get_weaviate_service as _gwvs
                    wv_hits = _gwvs().search_research_questions(query, limit=limit)
                except Exception:
                    pass

                live_ids: set[str] = set()
                archived: list[dict] = []
                for h in wv_hits:
                    eid = h.get("embedding_id", "")
                    if h.get("archived"):
                        archived.append(h)
                    else:
                        live_ids.add(eid)

                if live_ids:
                    from uuid import UUID as _UUID
                    rows = db.query(ResearchQuestion).filter(
                        ResearchQuestion.id.in_([_UUID(i) for i in live_ids if _is_valid_uuid(i)])
                    ).all()
                else:
                    rows = []

                if not rows and not archived:
                    # ILIKE fallback
                    q = db.query(ResearchQuestion).filter(
                        ResearchQuestion.question.ilike(f"%{query}%")
                    )
                    if status_filter:
                        q = q.filter(ResearchQuestion.status == status_filter)
                    rows = q.limit(limit).all()

                results = [
                    {
                        "id": str(r.id),
                        "question": r.question,
                        "status": r.status,
                        "priority": r.priority,
                        "context": r.context,
                        "answer": r.answer,
                        "source": r.source,
                        "tags": r.tags,
                        "created_at": r.created_at.isoformat() if r.created_at else None,
                    }
                    for r in rows
                    if not status_filter or r.status == status_filter
                ]

                return {"results": results, "archived": archived}
            finally:
                db.close()

        # ------------------------------------------------------------------ #
        #  question_list                                                       #
        # ------------------------------------------------------------------ #
        @mcp.tool()
        async def question_list(
            status_filter: str = "pending",
            limit: int = 20,
        ) -> dict:
            """List research questions by status.

            Defaults to *pending* so agents can quickly see what needs
            follow-up without a search query.

            Args:
                status_filter: pending / investigating / answered / closed.
                limit: Maximum number of rows to return.
            """
            db = SyncSessionLocal()
            try:
                q = (
                    db.query(ResearchQuestion)
                    .filter(ResearchQuestion.status == status_filter)
                    .order_by(ResearchQuestion.created_at.desc())
                    .limit(limit)
                )
                rows = q.all()
                return {
                    "status_filter": status_filter,
                    "count": len(rows),
                    "questions": [
                        {
                            "id": str(r.id),
                            "question": r.question,
                            "priority": r.priority,
                            "context": r.context,
                            "source": r.source,
                            "tags": r.tags,
                            "created_at": r.created_at.isoformat() if r.created_at else None,
                        }
                        for r in rows
                    ],
                }
            finally:
                db.close()

        # ------------------------------------------------------------------ #
        #  question_update                                                     #
        # ------------------------------------------------------------------ #
        @mcp.tool()
        async def question_update(
            question_id: str,
            status: str | None = None,
            answer: str | None = None,
            priority: str | None = None,
            context: str | None = None,
            tags: list[str] | None = None,
        ) -> dict:
            """Update the status, answer, or priority of a research question.

            Typical lifecycle:
            pending → investigating → answered → closed.

            Args:
                question_id: UUID of the question to update.
                status: New status value.
                answer: Answer text (when the question has been resolved).
                priority: Revised priority.
                context: Additional context to append / replace.
                tags: Revised tag list.
            """
            from uuid import UUID as _UUID
            db = SyncSessionLocal()
            try:
                row = db.query(ResearchQuestion).filter(
                    ResearchQuestion.id == _UUID(question_id)
                ).first()
                if not row:
                    return {"success": False, "error": "Question not found"}

                if status is not None:
                    row.status = status
                if answer is not None:
                    row.answer = answer
                if priority is not None:
                    row.priority = priority
                if context is not None:
                    row.context = context
                if tags is not None:
                    row.tags = tags

                db.commit()
                db.refresh(row)

                # Re-index updated state in Weaviate
                try:
                    from itl_braincell_sdk.services.weaviate_service import get_weaviate_service as _gwvs
                    _gwvs().index_research_question(
                        str(row.id),
                        question=row.question,
                        status=row.status,
                        priority=row.priority,
                        context=row.context or "",
                        source=row.source,
                    )
                except Exception:
                    pass

                return {
                    "success": True,
                    "id": str(row.id),
                    "status": row.status,
                    "priority": row.priority,
                    "answer": row.answer,
                }
            finally:
                db.close()


def _is_valid_uuid(val: str) -> bool:
    try:
        from uuid import UUID as _UUID
        _UUID(val)
        return True
    except ValueError:
        return False


cell = ResearchQuestionsCell()
