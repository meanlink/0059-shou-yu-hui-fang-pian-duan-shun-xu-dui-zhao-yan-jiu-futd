from typing import Literal
from pydantic import BaseModel,Field

class Score(BaseModel):
    learner:str=Field(pattern=r"^[A-Z0-9-]{2,20}$")
    actual_arm:Literal['A','B']
    score:int=Field(ge=0,le=100)
