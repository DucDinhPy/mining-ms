import asyncio
import os

from google import genai

import json

from backend.services.mineops_tools import (
    get_latest_ppe_detections,
    list_camera_runtime_status,
)
from backend.workers.camera_manager import CameraManager

TOOLS = [
    {
        "type": "function",
        "name": "list_camera_runtime_status",
        "description": (
            "Returns the current runtime connection status of "
            "all camera workers managed by MineOps."
        ),
        "parameters": {
            "type": "object",
            "properties": {},
        },
    },
    {
        "type": "function",
        "name": "get_latest_ppe_detections",
        "description": (
            "Returns the latest PPE detection metadata for "
            "one MineOps camera."
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
        },
    },
]

MODEL = os.getenv(
    "GEMINI_MODEL",
    "gemini-3.8-flash",
)

SYSTEM_INSTRUCTION = """
You are MineOps Assistant, an AI assistant for a mining
operations and PPE monitoring application.

Rules:
- Answer in the same language as the user.
- Help users understand cameras and PPE detection data.
- Do not invent camera states or PPE detections.
- Clearly distinguish configured status from actual
  camera connection status.
- If operational data is unavailable, say so clearly.
- Never expose RTSP credentials or internal secrets.
- Keep answers concise and practical.
- Do not claim to replace qualified safety personnel.
- Use the available MineOps tools whenever the user asks
  about actual cameras or PPE detections.
- Never pretend that tool data exists when a tool returns
  no data.
"""


def _create_interaction(
    message: str,
    previous_interaction_id: str | None,
    camera_manager: CameraManager,
):
    api_key = os.environ["GEMINI_API_KEY"]

    client = genai.Client(
        api_key=api_key,
    )

    parameters = {
        "model": MODEL,
        "system_instruction": SYSTEM_INSTRUCTION,
        "input": message,
        "tools": TOOLS,
        "generation_config": {
            "thinking_level": "low",
        },   
    }

    if previous_interaction_id:
        parameters["previous_interaction_id"] = (
            previous_interaction_id
        )

    interaction = client.interactions.create(
        **parameters,
    )


    for _ in range(3):
        function_calls = [
            step
            for step in interaction.steps
            if step.type == "function_call"
        ]

        if not function_calls:
            return {
                "interaction_id": interaction.id,
                "message": interaction.output_text,
            }

        function_results = []

        for function_call in function_calls:
            result = _execute_tool(
                name=function_call.name,
                arguments=function_call.arguments or {},
                camera_manager=camera_manager,
            )

            function_results.append({
                "type": "function_result",
                "name": function_call.name,
                "call_id": function_call.id,
                "result": [
                    {
                        "type": "text",
                        "text": json.dumps(
                            result,
                            ensure_ascii=False,
                        ),
                    }
                ],
            })

        interaction = client.interactions.create(
            model=MODEL,
            previous_interaction_id=interaction.id,
            input=function_results,
            tools=TOOLS,
            generation_config={
                "thinking_level": "low",
            },
        )

    raise RuntimeError(
        "Assistant exceeded the maximum number of tool rounds."
    )


async def create_assistant_response(
    message: str,
    camera_manager: CameraManager,
    previous_interaction_id: str | None = None,
):
    return await asyncio.to_thread(
        _create_interaction,
        message,
        previous_interaction_id,
        camera_manager,
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