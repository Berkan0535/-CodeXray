from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.config import settings
from app.models.entities import AIMessage, Analysis
from app.schemas.schemas import ChatRequest, ChatResponse, CitationSchema
from app.rag.retriever import CodebaseRetriever

router = APIRouter()


@router.post("/{analysis_id}/chat", response_model=ChatResponse)
async def ask_codebase(
    analysis_id: str,
    payload: ChatRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    RAG 'Ask Your Codebase' endpoint.
    Performs semantic vector search across indexed codebase chunks and returns
    an accurate LLM answer with precise file, symbol, and line number citations.
    """
    stmt = select(Analysis).where(Analysis.id == analysis_id)
    res = await db.execute(stmt)
    analysis = res.scalar_one_or_none()
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")

    # Record User Message
    user_msg = AIMessage(
        analysis_id=analysis_id,
        role="user",
        content=payload.message,
        citations=[]
    )
    db.add(user_msg)

    # Perform RAG Retrieval & LLM Generation
    rag_result = await CodebaseRetriever.answer_question(
        analysis_id=analysis_id,
        question=payload.message,
        provider_type=settings.AI_PROVIDER,
        top_k=settings.VECTOR_TOP_K
    )

    # Record Assistant Message
    assistant_msg = AIMessage(
        analysis_id=analysis_id,
        role="assistant",
        content=rag_result["answer"],
        citations=rag_result.get("citations", [])
    )
    db.add(assistant_msg)
    await db.commit()
    await db.refresh(assistant_msg)

    return ChatResponse(
        id=assistant_msg.id,
        role=assistant_msg.role,
        content=assistant_msg.content,
        citations=[CitationSchema.model_validate(c) for c in (assistant_msg.citations or [])],
        created_at=assistant_msg.created_at
    )


@router.get("/{analysis_id}/chat/history", response_model=List[ChatResponse])
async def get_chat_history(
    analysis_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Returns conversation history for an analysis session."""
    stmt = select(AIMessage).where(AIMessage.analysis_id == analysis_id).order_by(AIMessage.created_at.asc())
    res = await db.execute(stmt)
    messages = res.scalars().all()
    return [
        ChatResponse(
            id=m.id,
            role=m.role,
            content=m.content,
            citations=[CitationSchema.model_validate(c) for c in (m.citations or [])],
            created_at=m.created_at
        )
        for m in messages
    ]
