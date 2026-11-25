from fastapi import APIRouter,Depends
from core import db,require
from editor_decision import sign
from memo_input import Memo

router=APIRouter(prefix="/sign-trials/{code}/memo")

@router.get("")
def decision(code:str,_=Depends(require())):
    with db() as cx:
        return cx.execute("SELECT * FROM sign_memos WHERE trial=%s",(code,)).fetchone()

@router.post("",status_code=201)
def review(code:str,data:Memo,user=Depends(require("reviewer"))):
    with db() as cx: return sign(cx,code,data,user["email"])
