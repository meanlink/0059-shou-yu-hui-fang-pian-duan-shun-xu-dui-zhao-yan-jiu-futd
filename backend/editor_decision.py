from decimal import Decimal
from fastapi import HTTPException
from trial_book import case

def sign(cx,code,body,reviewer):
    if case(cx,code,True)["state"]!="evaluated":
        raise HTTPException(409,"仅可为已评估且未签的试教出教材意见")
    row=cx.execute("SELECT * FROM sign_effect WHERE trial=%s",(code,)).fetchone()
    if body.decision=="adopt" and (row["p_value"]>Decimal(".05") or row["effect"]<=0):
        raise HTTPException(409,"试教学员证据未达到切换到版本 B 的阈值，请待复核或保留 A")
    memo=cx.execute("INSERT INTO sign_memos VALUES (%s,%s,%s,%s) RETURNING *",
                    (code,body.decision,body.rationale,reviewer)).fetchone()
    cx.execute("UPDATE sign_trials SET state='signed' WHERE code=%s",(code,))
    return memo
