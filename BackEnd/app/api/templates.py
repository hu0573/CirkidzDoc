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
    summary="List available templates",
)
def list_templates() -> list[TemplateSummary]:
    """
    List all available templates (summary information only).
    """

    return [TemplateSummary.from_metadata(metadata) for metadata in template_repository.list_templates()]


@router.get(
    "/{template_id}",
    response_model=TemplateDetail,
    summary="Get template detail",
)
def get_template_detail(template_id: str) -> TemplateDetail:
    """
    Retrieve detailed metadata for the specified template.
    """

    try:
        metadata = template_repository.get_template(template_id)
    except TemplateNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Template {template_id} does not exist",
        ) from None

    return TemplateDetail(template=metadata)


@router.post(
    "/render",
    response_model=RenderResponse,
    status_code=HTTPStatus.ACCEPTED,
    summary="Submit a template render task",
)
def render_template(request: RenderRequest, background_tasks: BackgroundTasks) -> RenderResponse:
    """
    Create a render task and schedule it for background execution.
    """

    try:
        template_repository.get_template(request.template_id)
    except TemplateNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Template {request.template_id} does not exist",
        ) from None

    response = task_service.create_task(request)
    background_tasks.add_task(task_service.process_task, response.task_id)
    return response


@router.get(
    "/tasks/{task_id}",
    response_model=TaskStatus,
    summary="Get task status",
)
def get_task_status(task_id: str) -> TaskStatus:
    """
    Return the current status, progress, and results of the specified task.
    """

    try:
        return task_service.fetch_status(task_id)
    except TaskNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Task {task_id} does not exist") from None


@router.get(
    "/tasks/{task_id}/files/{target_format}",
    summary="Download a task result file",
)
def download_task_file(
    task_id: str,
    target_format: str,
    token: str = Query(..., description="Download authorization token"),
) -> FileResponse:
    """
    Download the result file for the specified task.
    """

    try:
        path = task_service.resolve_download_path(task_id, token, target_format.lower())
    except TaskNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task or file does not exist") from None
    except FileNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File has expired or is missing") from None

    filename = path.name
    return FileResponse(path, filename=filename, media_type="application/octet-stream")

