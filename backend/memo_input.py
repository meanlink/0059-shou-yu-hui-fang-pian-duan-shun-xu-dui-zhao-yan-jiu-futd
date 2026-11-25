from typing import Annotated,Literal
from pydantic import BaseModel,StringConstraints

class Memo(BaseModel):
    decision:Literal['adopt','keep','defer']
    rationale:Annotated[str,StringConstraints(strip_whitespace=True,min_length=6,max_length=200)]
