from sentence_transformers import SentenceTransformer
from pinecone import Pinecone
from config import PINECONE_API_KEY, PINECONE_INDEX_NAME, EMBED_MODEL_NAME

_embed_model = None
_pinecone_index = None


def _get_embed_model():
    global _embed_model
    if _embed_model is None:
        _embed_model = SentenceTransformer(EMBED_MODEL_NAME)
    return _embed_model


def _get_index():
    global _pinecone_index
    if _pinecone_index is None:
        pc = Pinecone(api_key=PINECONE_API_KEY)
        _pinecone_index = pc.Index(PINECONE_INDEX_NAME)
    return _pinecone_index


def retrieve_state_context(state: str, top_k: int = 3) -> str:
    if not state or not state.strip():
        return "No state provided. General insurance guidance applies."

    state_clean = state.strip().title()
    query_text = f"auto insurance claim rules laws {state_clean}"

    embed_model = _get_embed_model()
    index = _get_index()

    query_vector = embed_model.encode(query_text).tolist()
    results = index.query(
        vector=query_vector,
        top_k=top_k,
        filter={"state": {"$eq": state_clean}},
        include_metadata=True,
    )

    if not results.matches:
        return f"No specific data found for {state_clean}. General guidance applies."

    chunks = [m.metadata["text"] for m in results.matches]
    return f"--- {state_clean} Insurance Laws ---\n\n" + "\n\n".join(chunks)
