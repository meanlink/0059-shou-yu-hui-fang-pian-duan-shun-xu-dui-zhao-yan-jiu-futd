from fastapi import APIRouter, Depends

from core import db, require
from correction_input import Correction
from corrections import accept, history, refreeze

router = APIRouter(prefix="/sign-trials/{code}")


@router.post("/corrections", status_code=201)
def correct(code: str, data: Correction, user=Depends(require("reviewer"))):
    with db() as cx:
        return accept(cx, code, data, user["email"])


@router.post("/refreeze", status_code=202)
def freeze_again(code: str, _=Depends(require("reviewer"))):
    with db() as cx:
        return refreeze(cx, code)


@router.get("/corrections")
def correction_history(code: str, _=Depends(require())):
    with db() as cx:
        return history(cx, code)
