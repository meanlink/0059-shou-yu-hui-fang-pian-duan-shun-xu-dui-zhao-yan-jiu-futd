from fastapi import APIRouter, Depends, HTTPException

from core import db, require
from editor_decision import sign
from memo_input import Memo

router = APIRouter(prefix="/sign-trials/{code}/memo")


@router.get("")
def decision(code: str, _=Depends(require())):
    """返回当前轮次意见及全部历史意见（含已被更正取代的旧意见，可回看当时依据）。"""
    with db() as cx:
        trial = cx.execute(
            "SELECT revision FROM sign_trials WHERE code=%s", (code,)
        ).fetchone()
        if trial is None:
            raise HTTPException(404, "该试教轮次不存在")
        history_rows = cx.execute("""
            SELECT m.memo_id, m.trial, m.revision, m.decision, m.rationale,
                   m.signed_by, m.signed_at, e.effect, e.p_value,
                   e.permutations, e.detail, e.valid
            FROM sign_memos m
            JOIN sign_effect e ON e.trial=m.trial AND e.revision=m.revision
            WHERE m.trial=%s ORDER BY m.signed_at, m.memo_id
        """, (code,)).fetchall()
        current = next(
            (row for row in history_rows if row["revision"] == trial["revision"]),
            None,
        )
        return {"revision": trial["revision"], "current": current, "history": history_rows}


@router.post("", status_code=201)
def review(code: str, data: Memo, user=Depends(require("reviewer"))):
    with db() as cx:
        return sign(cx, code, data, user["email"])
