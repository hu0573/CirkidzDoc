from datetime import datetime, timedelta
from http import HTTPStatus
from uuid import uuid4

from fastapi import APIRouter, HTTPException, status

from app.models.templates import RenderRequest, RenderResponse, TemplateDetail, TemplateSummary
from app.services.templates import TemplateNotFoundError, template_repository

router = APIRouter()


@router.get(
    "",
    response_model=list[TemplateSummary],
    summary="获取模板列表",
)
def list_templates() -> list[TemplateSummary]:
    """
    列出所有可用模板（仅概要信息）。
    """

    return [TemplateSummary.from_metadata(metadata) for metadata in template_repository.list_templates()]


@router.get(
    "/{template_id}",
    response_model=TemplateDetail,
    summary="获取模板详情",
)
def get_template_detail(template_id: str) -> TemplateDetail:
    """
    查询指定模板的详细元数据。
    """

    try:
        metadata = template_repository.get_template(template_id)
    except TemplateNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"模板 {template_id} 不存在",
        ) from None

    return TemplateDetail(template=metadata)


@router.post(
    "/render",
    response_model=RenderResponse,
    status_code=HTTPStatus.ACCEPTED,
    summary="提交模板渲染任务",
)
def render_template(request: RenderRequest) -> RenderResponse:
    """
    目前仅返回占位响应，后续接入真实任务编排与渲染逻辑。
    """

    try:
        template_repository.get_template(request.template_id)
    except TemplateNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"模板 {request.template_id} 不存在",
        ) from None

    fake_task_id = uuid4().hex
    expires_at = datetime.utcnow() + timedelta(minutes=30)

    return RenderResponse(task_id=fake_task_id, status="queued", expires_at=expires_at)

