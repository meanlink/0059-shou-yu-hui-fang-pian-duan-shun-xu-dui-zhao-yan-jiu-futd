from psycopg.types.json import Jsonb
from trial_book import assignment_sheet, case
from within_level import permute

def result(cx,code):
    data=case(cx,code)
    row=cx.execute("SELECT * FROM sign_effect WHERE trial=%s",(code,)).fetchone()
    return {"state":data["state"],"effect":row}

def calculate(cx,code):
    evidence=permute(assignment_sheet(cx,code))
    cx.execute("""INSERT INTO sign_effect VALUES (%s,%s,%s,%s,%s)""",
              (code,evidence["effect"],evidence["p_value"],evidence["permutations"],Jsonb(evidence["detail"])))
    cx.execute("UPDATE sign_trials SET state='evaluated' WHERE code=%s",(code,))
    return evidence
