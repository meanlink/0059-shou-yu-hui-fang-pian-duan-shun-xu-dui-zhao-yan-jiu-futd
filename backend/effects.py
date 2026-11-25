from psycopg.types.json import Jsonb

from trial_book import assignment_sheet, case
from within_level import permute


def current_effect(cx, code):
    """当前修订轮次对应的结果；旧结果失效或尚未算出时为 None。"""
    data = case(cx, code)
    row = cx.execute(
        "SELECT * FROM sign_effect WHERE trial=%s AND revision=%s",
        (code, data["revision"]),
    ).fetchone()
    return data, row


def result(cx, code):
    data, row = current_effect(cx, code)
    return {"state": data["state"], "revision": data["revision"],
            "effect": row if row and row["valid"] else None}


def calculate(cx, code, revision=None):
    """写入指定修订轮次的置换结果。任务携带的轮次必须仍是当前轮次。"""
    data = case(cx, code, True)
    if revision is None:
        revision = data["revision"]
    if revision != data["revision"]:
        # 旧计算任务晚到：更正已开启新一轮，旧结果不能恢复签批资格
        raise StaleRevision(code, revision, data["revision"])
    evidence = permute(assignment_sheet(cx, code))
    cx.execute(
        """INSERT INTO sign_effect
               (trial, revision, effect, p_value, permutations, detail, valid)
           VALUES (%s,%s,%s,%s,%s,%s,true)
           ON CONFLICT (trial, revision) DO UPDATE
           SET effect=excluded.effect, p_value=excluded.p_value,
               permutations=excluded.permutations, detail=excluded.detail,
               valid=true""",
        (code, revision, evidence["effect"], evidence["p_value"],
         evidence["permutations"], Jsonb(evidence["detail"])),
    )
    cx.execute(
        "UPDATE sign_trials SET state='evaluated' WHERE code=%s AND revision=%s",
        (code, revision),
    )
    return evidence | {"revision": revision}


class StaleRevision(RuntimeError):
    def __init__(self, code, job_revision, current_revision):
        super().__init__(
            f"trial {code} job revision {job_revision} stale, current {current_revision}"
        )
        self.code = code
        self.job_revision = job_revision
        self.current_revision = current_revision
