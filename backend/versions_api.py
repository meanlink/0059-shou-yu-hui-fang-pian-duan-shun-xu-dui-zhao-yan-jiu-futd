from fastapi import APIRouter,Depends
from core import db,require
from trial_book import case,assignment_sheet

router=APIRouter(prefix="/sign-trials")

@router.get("")
def list_trials(_=Depends(require())):
    with db() as cx: return cx.execute("SELECT * FROM sign_trials ORDER BY code DESC").fetchall()

@router.get("/{code}/versions")
def versions(code:str,_=Depends(require())):
    with db() as cx:
        case(cx,code)
        return cx.execute("SELECT arm,clips FROM sign_versions WHERE trial=%s ORDER BY arm",(code,)).fetchall()

@router.get("/{code}/assignments")
def assignments(code:str,_=Depends(require())):
    with db() as cx: return assignment_sheet(cx,code)
