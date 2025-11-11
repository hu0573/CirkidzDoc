from http import HTTPStatus

from fastapi import APIRouter, BackgroundTasks, HTTPException, Query, status
from fastapi.responses import FileResponse

from app.models.templates import RenderRequest, RenderResponse, TaskStatus, TemplateDetail, TemplateSummary
from app.services.task_service import TaskNotFoundError, task_service
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
def render_template(request: RenderRequest, background_tasks: BackgroundTasks) -> RenderResponse:
    """
    创建渲染任务并交由后台执行。
    """

    try:
        template_repository.get_template(request.template_id)
    except TemplateNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"模板 {request.template_id} 不存在",
        ) from None

    response = task_service.create_task(request)
    background_tasks.add_task(task_service.process_task, response.task_id)
    return response


@router.get(
    "/tasks/{task_id}",
    response_model=TaskStatus,
    summary="查询任务状态",
)
def get_task_status(task_id: str) -> TaskStatus:
    """
    返回指定任务的当前状态、进度与结果列表。
    """

    try:
        return task_service.fetch_status(task_id)
    except TaskNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"任务 {task_id} 不存在") from None


@router.get(
    "/tasks/{task_id}/files/{target_format}",
    summary="下载任务结果文件",
)
def download_task_file(
    task_id: str,
    target_format: str,
    token: str = Query(..., description="下载授权 token"),
) -> FileResponse:
    """
    下载指定任务的结果文件。
    """

    try:
        path = task_service.resolve_download_path(task_id, token, target_format.lower())
    except TaskNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="任务或文件不存在") from None
    except FileNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="文件已过期或不存在") from None

    filename = path.name
    return FileResponse(path, filename=filename, media_type="application/octet-stream")

