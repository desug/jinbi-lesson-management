from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.encoders import jsonable_encoder
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.routers.admin import router as admin_router
from app.routers.admin_ai import router as admin_ai_router
from app.routers.auth import router as auth_router
from app.routers.health import router as health_router
from app.routers.student import router as student_router


# FastAPI 应用对象是后端入口；uvicorn 启动时会加载 app.main:app。
app = FastAPI(
    title=settings.project_name,
    version=settings.project_version,
    description="补课机构课时管理系统后端脚手架",
)

# CORS 允许前端跨域访问后端。开发阶段放开所有来源，生产环境可以收紧为指定域名。
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册各业务模块路由：请求进来后会按 URL 前缀分发到对应 router 文件。
app.include_router(health_router)
app.include_router(auth_router)
app.include_router(student_router)
app.include_router(admin_router)
app.include_router(admin_ai_router)


@app.exception_handler(HTTPException)
def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    # 统一 HTTPException 返回结构，前端 request.js 可以稳定读取 message/code。
    code = None
    if isinstance(exc.detail, dict):
        message = str(exc.detail.get("message") or "请求失败")
        code = exc.detail.get("code")
        detail = exc.detail.get("detail", exc.detail)
    else:
        message = exc.detail if isinstance(exc.detail, str) else "请求失败"
        detail = exc.detail
    content = {
        "success": False,
        "message": message,
        "detail": detail,
    }
    if code:
        content["code"] = code
    return JSONResponse(
        status_code=exc.status_code,
        content=content,
        headers=exc.headers,
    )


@app.exception_handler(RequestValidationError)
def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    # Pydantic 参数校验失败会走这里，例如缺字段、类型不对、数字小于 0。
    return JSONResponse(
        status_code=422,
        content={
            "success": False,
            "message": "参数校验失败",
            "detail": jsonable_encoder(exc.errors()),
        },
    )


@app.get("/", summary="服务信息")
def read_root() -> dict[str, str]:
    # 根路径只做服务状态展示，方便浏览器快速确认后端是否启动。
    return {
        "name": settings.project_name,
        "version": settings.project_version,
        "status": "running",
    }
