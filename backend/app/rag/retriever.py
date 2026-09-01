import os
from typing import List, Dict, Any, Optional
from app.ai.factory import AIProviderFactory
from app.core.security import wrap_untrusted_code
from app.rag.vector_store import vector_store
from app.core.logging import logger


class CodebaseRetriever:
    """
    RAG engine for 'Ask Your Codebase' chat.
    Retrieves semantic code chunks, formats citations, and generates answers with LLM.
    """

    PROMPT_PATH = os.path.join(os.path.dirname(__file__), "..", "ai", "prompts", "chat.txt")

    @classmethod
    def _read_prompt(cls) -> str:
        try:
            with open(cls.PROMPT_PATH, "r", encoding="utf-8") as f:
                return f.read()
        except Exception:
            return (
                "You are an expert software engineer answering questions about the codebase.\n"
                "Context:\n{{context}}\n\nQuestion:\n{{question}}"
            )

    @classmethod
    async def answer_question(
        cls,
        analysis_id: str,
        question: str,
        provider_type: Optional[str] = None,
        top_k: int = 5
    ) -> Dict[str, Any]:
        provider = AIProviderFactory.get_provider(provider_type)

        # 1. Generate query embedding
        query_embeddings = await provider.generate_embeddings([question])
        query_vec = query_embeddings[0] if query_embeddings else []

        # 2. Vector search in store
        results = vector_store.search(analysis_id, query_vec, top_k=top_k)

        # Format context chunks and citations
        context_parts = []
        citations = []

        for chunk_data, sim in results:
            file_p = chunk_data.get("file_path", "unknown")
            sym = chunk_data.get("symbol_name")
            start_l = chunk_data.get("start_line", 1)
            end_l = chunk_data.get("end_line", 1)
            snippet = chunk_data.get("content", "")

            heading = f"File: {file_p} (Lines {start_l}-{end_l})" + (f" | Symbol: {sym}" if sym else "")
            context_parts.append(f"### {heading}\n```{snippet}```\n")

            citations.append({
                "file_path": file_p,
                "line_number": start_l,
                "symbol_name": sym,
                "snippet": snippet[:150] + "..." if len(snippet) > 150 else snippet,
            })

        context_str = "\n".join(context_parts) or "No specific code chunks matched the query."

        # 3. Fill prompt template and invoke LLM
        prompt_tpl = cls._read_prompt()
        prompt = prompt_tpl.replace("{{context}}", wrap_untrusted_code(context_str, "CONTEXT")).replace("{{question}}", question)

        answer_text = await provider.generate_text(prompt, temperature=0.2)

        return {
            "answer": answer_text,
            "citations": citations,
        }
