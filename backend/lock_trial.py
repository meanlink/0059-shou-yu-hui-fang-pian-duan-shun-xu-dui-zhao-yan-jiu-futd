from fastapi import HTTPException
from core import enqueue
from trial_book import case, assignment_sheet

def lock(cx,code):
    if case(cx,code,True)["state"]!="open":
        raise HTTPException(409,"此轮已冻结")
    rows=assignment_sheet(cx,code)
    for level in ("beginner","returning"):
        eligible=[r for r in rows if r["level"]==level]
        if len(eligible)>8:
            raise HTTPException(409,"每班置换上限为 8 人，请拆分试教轮次")
        if any(sum(r["arm"]==arm and r["score"] is not None for r in eligible)<2 for arm in ("A","B")):
            raise HTTPException(409,"每水平、每回放版本至少需要两份有效答题")
        if any(r["score"] is None for r in eligible):
            raise HTTPException(409,"请完成已分配学员的成绩再冻结，避免对照失衡")
    cx.execute("UPDATE sign_trials SET state='frozen' WHERE code=%s", (code,))
    revision = case(cx, code)["revision"]
    return {"job_id": enqueue(
        cx, "sign_order_permutation", {"code": code, "revision": revision},
    ), "revision": revision}
