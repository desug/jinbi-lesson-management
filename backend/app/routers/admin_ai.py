from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.schemas.ai import AiQueryRequest, AiQueryResponse
from app.schemas.auth import TokenPayload
from app.services.ai_query_service import answer_ai_query
from app.utils.deps import get_current_admin, get_db


router = APIRouter(prefix="/admin", tags=["admin"])


@router.post("/ai-query", response_model=AiQueryResponse, summary="管理员 AI 查询课时助手")
def admin_ai_query_endpoint(
    payload: AiQueryRequest,
    current_admin: TokenPayload = Depends(get_current_admin),
    db: Session = Depends(get_db),
) -> AiQueryResponse:
    return answer_ai_query(
        db=db,
        current_admin=current_admin,
        query=payload.query,
    )
