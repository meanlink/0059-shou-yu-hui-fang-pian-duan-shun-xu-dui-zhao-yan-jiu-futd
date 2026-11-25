from fastapi import APIRouter,Depends
from core import db,require
from lock_trial import lock
from effects import result

router=APIRouter(prefix="/sign-trials/{code}/effect")

@router.get("")
def report(code:str,_=Depends(require())):
    with db() as cx: return result(cx,code)

@router.post("",status_code=202)
def compare(code:str,_=Depends(require("reviewer"))):
    with db() as cx: return lock(cx,code)
