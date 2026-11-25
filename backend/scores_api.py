from fastapi import APIRouter,Depends
from core import db,require
from score_register import log
from scores_input import Score

router=APIRouter(prefix="/sign-trials/{code}")

@router.put("/scores")
def score(code:str,data:Score,_=Depends(require("operator"))):
    with db() as cx: return log(cx,code,data)
