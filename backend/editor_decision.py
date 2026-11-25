from decimal import Decimal

from fastapi import HTTPException

from trial_book import case


def sign(cx, code, body, reviewer):
    # 锁住试教行，与更正受理串行化，防止拿旧结果并发签成新版
    trial = case(cx, code, True)
    if trial["state"] != "evaluated":
        raise HTTPException(409, "仅可为已评估且未签的试教出教材意见")
    row = cx.execute(
        "SELECT * FROM sign_effect WHERE trial=%s AND revision=%s",
        (code, trial["revision"]),
    ).fetchone()
    # 必须是当前轮次且仍有效的结果；更正受理后旧结果 valid=false，签批立即被拒
    if row is None or not row["valid"]:
        raise HTTPException(409, "签批依据的结果已因成绩更正失效，请等待新一轮结果")
    if body.decision == "adopt" and (
        row["p_value"] > Decimal(".05") or row["effect"] <= 0
    ):
        raise HTTPException(409, "试教学员证据未达到切换到版本 B 的阈值，请待复核或保留 A")
    memo = cx.execute("""
        INSERT INTO sign_memos(trial, revision, decision, rationale, signed_by)
        VALUES (%s,%s,%s,%s,%s)
        RETURNING memo_id, trial, revision, decision, rationale, signed_by, signed_at
    """, (code, trial["revision"], body.decision, body.rationale, reviewer)).fetchone()
    cx.execute("UPDATE sign_trials SET state='signed' WHERE code=%s", (code,))
    return memo
