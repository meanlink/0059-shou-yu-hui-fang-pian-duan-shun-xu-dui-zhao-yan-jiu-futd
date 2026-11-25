from fastapi import HTTPException

def case(cx,code,lock=False):
    row=cx.execute("SELECT * FROM sign_trials WHERE code=%s"+(" FOR UPDATE" if lock else ""),(code,)).fetchone()
    if row is None:
        raise HTTPException(404,"该试教轮次不存在")
    return row

def assignment_sheet(cx,code):
    case(cx,code)
    return cx.execute("""SELECT a.*,s.score FROM sign_assignments a
     LEFT JOIN sign_scores s ON s.trial=a.trial AND s.learner=a.learner
     WHERE a.trial=%s ORDER BY a.level,a.arm,a.learner""",(code,)).fetchall()
