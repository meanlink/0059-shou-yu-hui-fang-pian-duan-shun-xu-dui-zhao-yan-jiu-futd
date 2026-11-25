from typing import Annotated, Literal

from pydantic import BaseModel, Field, StringConstraints


class Correction(BaseModel):
    learner: str = Field(pattern=r"^[A-Z0-9-]{2,20}$")
    actual_arm: Literal['A', 'B']
    score: int = Field(ge=0, le=100)
    reason: Annotated[str, StringConstraints(strip_whitespace=True, min_length=6, max_length=200)]
