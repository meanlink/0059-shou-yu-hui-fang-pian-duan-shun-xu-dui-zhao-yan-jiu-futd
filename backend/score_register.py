from fastapi import HTTPException

from corrections import _record_history
from trial_book import case


def log(cx, trial, body, actor):
    if case(cx, trial, True)["state"] != "open":
        raise HTTPException(409, "试教已冻结，成绩更正请由复核员在原试教登记上受理")
    row = cx.execute(
        "SELECT arm FROM sign_assignments WHERE trial=%s AND learner=%s",
        (trial, body.learner),
    ).fetchone()
    if row is None:
        raise HTTPException(404, "试教学员码不在分配表")
    if row["arm"] != body.actual_arm:
        raise HTTPException(409, "实际回放版本与分配不符，先核对播放器记录")
    saved = cx.execute("""
        INSERT INTO sign_scores VALUES (%s,%s,%s,%s)
        ON CONFLICT(trial,learner) DO UPDATE SET score=excluded.score RETURNING *
    """, (trial, body.learner, body.score, body.actual_arm)).fetchone()
    _record_history(cx, trial, body.learner, body.score,
                    body.actual_arm, 1, "register", actor)
    return saved
