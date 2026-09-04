from fastapi import APIRouter

from app.core.config import settings


router = APIRouter(tags=["health"])


@router.get("/health", summary="健康检查")
def health_check() -> dict[str, object]:
    return {
        "ok": True,
        "message": "服务运行正常",
        "service": settings.project_name,
        "version": settings.project_version,
    }
