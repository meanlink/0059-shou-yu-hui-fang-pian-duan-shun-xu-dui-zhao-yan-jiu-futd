from fastapi import HTTPException

from core import enqueue
from trial_book import case, assignment_sheet

CORRECTABLE_STATES = ('frozen', 'evaluated', 'signed')


def _record_history(cx, trial, learner, score, actual_arm, revision, source, actor):
    cx.execute("""
        INSERT INTO sign_score_history
            (trial, learner, score, actual_arm, revision, source, changed_by)
        VALUES (%s,%s,%s,%s,%s,%s,%s)
    """, (trial, learner, score, actual_arm, revision, source, actor))


def accept(cx, code, body, reviewer):
    """受理一次成绩更正。受理即让旧结果失效，并把试教退回更正中。"""
    trial = case(cx, code, True)
    if trial["state"] not in CORRECTABLE_STATES:
        raise HTTPException(409, "仅已冻结（含已评估、已签批）的试教可受理成绩更正")
    row = cx.execute(
        "SELECT arm FROM sign_assignments WHERE trial=%s AND learner=%s",
        (code, body.learner),
    ).fetchone()
    if row is None:
        raise HTTPException(404, "试教学员码不在分配表")
    if row["arm"] != body.actual_arm:
        raise HTTPException(409, "实际回放版本与分配不符，先核对播放器记录")
    current = cx.execute(
        "SELECT score FROM sign_scores WHERE trial=%s AND learner=%s",
        (code, body.learner),
    ).fetchone()
    if current is None:
        raise HTTPException(409, "该匿名码尚无冻结时登记的成绩，无法在原登记上更正")
    if current["score"] == body.score:
        raise HTTPException(409, "更正成绩与原成绩相同，无需受理")

    revision = trial["revision"]
    new_revision = revision + 1
    # 受理单记录被取代的旧轮次
    cx.execute(
        "INSERT INTO sign_corrections(trial, revision, reason, accepted_by) "
        "VALUES (%s,%s,%s,%s)",
        (code, revision, body.reason, reviewer),
    )
    # 旧计算结果立即失效：任何签批不得再引用它
    cx.execute(
        "UPDATE sign_effect SET valid=false WHERE trial=%s AND revision=%s",
        (code, revision),
    )
    cx.execute(
        "UPDATE sign_scores SET score=%s WHERE trial=%s AND learner=%s",
        (body.score, code, body.learner),
    )
    # 轮次即刻递增：在途的旧轮次计算任务即使晚到也会因轮次不符被拒绝
    _record_history(cx, code, body.learner, body.score,
                    body.actual_arm, new_revision, "correction", reviewer)
    cx.execute(
        "UPDATE sign_trials SET revision=%s, state='revising' WHERE code=%s",
        (new_revision, code),
    )
    return {"trial": code, "revision": new_revision,
            "superseded_revision": revision, "state": "revising",
            "learner": body.learner, "score": body.score}


def refreeze(cx, code):
    """更正后的成绩重新冻结，并按当前修订轮次排队计算。"""
    trial = case(cx, code, True)
    if trial["state"] != "revising":
        raise HTTPException(409, "仅更正中的试教可重新冻结")
    rows = assignment_sheet(cx, code)
    for level in ("beginner", "returning"):
        eligible = [r for r in rows if r["level"] == level]
        if len(eligible) > 8:
            raise HTTPException(409, "每班置换上限为 8 人，请拆分试教轮次")
        if any(sum(r["arm"] == arm and r["score"] is not None for r in eligible) < 2
               for arm in ("A", "B")):
            raise HTTPException(409, "每水平、每回放版本至少需要两份有效答题")
        if any(r["score"] is None for r in eligible):
            raise HTTPException(409, "请完成已分配学员的成绩再冻结，避免对照失衡")
    revision = trial["revision"]
    cx.execute("UPDATE sign_trials SET state='frozen' WHERE code=%s", (code,))
    return {"job_id": enqueue(
        cx, "sign_order_permutation", {"code": code, "revision": revision},
    ), "revision": revision}


def history(cx, code):
    case(cx, code)
    corrections = cx.execute("""
        SELECT id, revision, reason, accepted_by, accepted_at
        FROM sign_corrections WHERE trial=%s ORDER BY id
    """, (code,)).fetchall()
    changes = cx.execute("""
        SELECT learner, score, actual_arm, revision, source, changed_by, changed_at
        FROM sign_score_history WHERE trial=%s ORDER BY changed_at, id
    """, (code,)).fetchall()
    return {"corrections": corrections, "score_history": changes}
