import pytest
from app.ai.mock_provider import MockProvider
from app.rag.chunker import CodeChunker
from app.rag.vector_store import VectorStore, cosine_similarity
from app.rag.retriever import CodebaseRetriever
from app.analyzers.file_scanner import ScannedFile
from app.analyzers.parser.ast_extractor import TreeSitterParserEngine


@pytest.mark.asyncio
async def test_mock_provider_embeddings_and_reviews():
    provider = MockProvider()
    texts = ["def login_user(username, password): pass", "class DatabaseConnection: pass"]
    vectors = await provider.generate_embeddings(texts)
    
    assert len(vectors) == 2
    assert len(vectors[0]) == 384
    
    sim = cosine_similarity(vectors[0], vectors[0])
    assert pytest.approx(sim, 0.01) == 1.0

    review = await provider.generate_text("architectural code review prompt")
    assert "Architectural Assessment" in review


@pytest.mark.asyncio
async def test_vector_store_and_rag(tmp_path):
    store = VectorStore()
    chunk1 = {
        "id": "1",
        "file_path": "auth/service.py",
        "symbol_name": "authenticate_user",
        "start_line": 10,
        "end_line": 25,
        "content": "def authenticate_user(token): return verify_jwt(token)",
        "embedding": [0.5] * 384,
    }
    chunk2 = {
        "id": "2",
        "file_path": "billing/stripe.py",
        "symbol_name": "charge_card",
        "start_line": 1,
        "end_line": 15,
        "content": "def charge_card(amount): pass",
        "embedding": [-0.5] * 384,
    }
    store.index_chunks("test_analysis", [chunk1, chunk2])

    query_vec = [0.5] * 384
    results = store.search("test_analysis", query_vec, top_k=1)
    assert len(results) == 1
    assert results[0][0]["symbol_name"] == "authenticate_user"
