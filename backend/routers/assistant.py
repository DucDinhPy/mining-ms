import logging

from fastapi import APIRouter, HTTPException, Request

from backend.schemas.assistant import (
    AssistantRequest,
    AssistantResponse,
)
from backend.services.assistant_service import (
    create_assistant_response,
)


logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/assistant",
    tags=["assistant"],
)


@router.post(
    "/messages",
    response_model=AssistantResponse,
)
async def send_message(
    payload: AssistantRequest,
    http_request: Request,
):
    camera_manager = getattr(
        http_request.app.state,
        "camera_manager",
        None,
    )

    if camera_manager is None:
        raise HTTPException(
            status_code=503,
            detail="Camera manager is unavailable.",
        )

    try:
        return await create_assistant_response(
            message=payload.message,
            previous_interaction_id=(
                payload.previous_interaction_id
            ),
            camera_manager=camera_manager,
        )

    except Exception as error:
        logger.exception(
            "Gemini assistant request failed"
        )

        raise HTTPException(
            status_code=502,
            detail="AI assistant is unavailable.",
        ) from error