from pydantic import BaseModel, Field


class AssistantRequest(BaseModel):
    message: str = Field(
        min_length=1,
        max_length=4000,
    )

    previous_interaction_id: str | None = None


class AssistantResponse(BaseModel):
    interaction_id: str
    message: str