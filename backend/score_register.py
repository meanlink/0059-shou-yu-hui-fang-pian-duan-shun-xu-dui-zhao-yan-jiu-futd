from fastapi import HTTPException
from trial_book import case

def log(cx, trial, body):
    if case(cx,trial,True)["state"]!="open":
        raise HTTPException(409,"试教已冻结")
    row=cx.execute("SELECT arm FROM sign_assignments WHERE trial=%s AND learner=%s",(trial,body.learner)).fetchone()
    if row is None:
        raise HTTPException(404,"试教学员码不在分配表")
    if row["arm"]!=body.actual_arm:
        raise HTTPException(409,"实际回放版本与分配不符，先核对播放器记录")
    return cx.execute("""
        INSERT INTO sign_scores VALUES (%s,%s,%s,%s)
        ON CONFLICT(trial,learner) DO UPDATE SET score=excluded.score RETURNING *
    """,(trial,body.learner,body.score,body.actual_arm)).fetchone()
