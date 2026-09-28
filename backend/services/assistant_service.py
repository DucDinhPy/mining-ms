import asyncio
import json
import os
import threading
from copy import deepcopy
from functools import lru_cache
from uuid import uuid4

from groq import Groq

from backend.services.mineops_tools import (
    get_latest_ppe_detections,
    list_camera_runtime_status,
)
from backend.workers.camera_manager import CameraManager


SYSTEM_INSTRUCTION = """
You are MineOps Assistant, an AI assistant for a mining
operations and PPE monitoring application.

Rules:
- Answer in the same language as the user.
- Use MineOps tools for questions about actual cameras
  or PPE detections.
- Never invent camera states or PPE detections.
- Clearly distinguish configured camera status from
  actual runtime status.
- Never reveal RTSP URLs, credentials, or secrets.
- Keep answers concise and practical.
- Do not replace qualified safety personnel.
"""


TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "list_camera_runtime_status",
            "description": (
                "Returns the runtime connection status of "
                "all MineOps camera workers."
            ),
            "parameters": {
                "type": "object",
                "properties": {},
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_latest_ppe_detections",
            "description": (
                "Returns the latest PPE detection metadata "
                "for one MineOps camera."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "camera_id": {
                        "type": "string",
                        "description": "The MineOps camera UUID.",
                    },
                },
                "required": ["camera_id"],
                "additionalProperties": False,
            },
        },
    },
]


MAX_HISTORY_MESSAGES = 12

_conversations: dict[str, list[dict]] = {}
_conversation_lock = threading.Lock()


@lru_cache(maxsize=1)
def _get_client() -> Groq:
    return Groq(
        api_key=os.environ["GROQ_API_KEY"],
    )


def _execute_tool(
    name: str,
    arguments: dict,
    camera_manager: CameraManager,
):
    if name == "list_camera_runtime_status":
        return list_camera_runtime_status(
            camera_manager,
        )

    if name == "get_latest_ppe_detections":
        camera_id = arguments.get("camera_id")

        if not camera_id:
            return {
                "error": "camera_id is required",
            }

        return get_latest_ppe_detections(
            camera_manager,
            camera_id,
        )

    return {
        "error": f"Unknown tool: {name}",
    }


def _load_conversation(
    previous_interaction_id: str | None,
) -> tuple[str, list[dict]]:
    with _conversation_lock:
        if (
            previous_interaction_id
            and previous_interaction_id in _conversations
        ):
            return (
                previous_interaction_id,
                deepcopy(
                    _conversations[
                        previous_interaction_id
                    ]
                ),
            )

    return str(uuid4()), []


def _save_conversation(
    conversation_id: str,
    history: list[dict],
) -> None:
    clean_history = [
        message
        for message in history
        if message.get("role") in {"user", "assistant"}
        and message.get("content")
    ]

    with _conversation_lock:
        _conversations[conversation_id] = (
            clean_history[-MAX_HISTORY_MESSAGES:]
        )


def _create_completion(
    message: str,
    previous_interaction_id: str | None,
    camera_manager: CameraManager,
):
    client = _get_client()

    conversation_id, history = _load_conversation(
        previous_interaction_id,
    )

    messages = [
        {
            "role": "system",
            "content": SYSTEM_INSTRUCTION,
        },
        *history,
        {
            "role": "user",
            "content": message,
        },
    ]

    for _ in range(3):
        completion = client.chat.completions.create(
            model=os.getenv(
                "GROQ_MODEL",
                "openai/gpt-oss-120b",
            ),
            messages=messages,
            tools=TOOLS,
            tool_choice="auto",
            reasoning_effort="low",
            reasoning_format="hidden",
            max_completion_tokens=600,
        )

        assistant_message = (
            completion.choices[0].message
        )

        messages.append(
            assistant_message.model_dump(
                exclude_none=True,
            )
        )

        tool_calls = assistant_message.tool_calls or []

        if not tool_calls:
            answer = assistant_message.content

            if not answer:
                raise RuntimeError(
                    "Groq returned an empty response."
                )

            _save_conversation(
                conversation_id,
                messages,
            )

            return {
                "interaction_id": conversation_id,
                "message": answer,
            }

        for tool_call in tool_calls:
            tool_name = tool_call.function.name

            try:
                arguments = json.loads(
                    tool_call.function.arguments or "{}"
                )

                result = _execute_tool(
                    name=tool_name,
                    arguments=arguments,
                    camera_manager=camera_manager,
                )

            except json.JSONDecodeError:
                result = {
                    "error": "Invalid tool arguments.",
                }

            except Exception:
                result = {
                    "error": "MineOps tool execution failed.",
                }

            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "name": tool_name,
                "content": json.dumps(
                    result,
                    ensure_ascii=False,
                ),
            })

    raise RuntimeError(
        "Assistant exceeded the maximum tool rounds."
    )


async def create_assistant_response(
    message: str,
    camera_manager: CameraManager,
    previous_interaction_id: str | None = None,
):
    return await asyncio.to_thread(
        _create_completion,
        message,
        previous_interaction_id,
        camera_manager,
    )