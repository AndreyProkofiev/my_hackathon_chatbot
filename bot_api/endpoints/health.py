from fastapi import APIRouter, Request


router = APIRouter(tags=["Тест"])


@router.get("/health")
async def health(request: Request):
    return {
        "status": "ok",
        "model_loaded": hasattr(request.app.state, "rag_chain"),
    }
