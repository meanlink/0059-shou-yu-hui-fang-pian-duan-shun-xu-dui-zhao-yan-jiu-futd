"""自包含业务规则验证：用内存存储复刻行锁/事务/约束语义。

在无 Postgres/Docker 的环境中验证更正、失效、重算、并发签批等规则。
运行：python3 tests/test_corrections_logic.py
"""
import os
import sys
import threading
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from types import ModuleType
from pathlib import Path


class HTTPException(RuntimeError):
    def __init__(self, status_code, detail):
        super().__init__(detail)
        self.status_code = status_code
        self.detail = detail


# 为缺少第三方依赖的环境注入最小桩模块
_fastapi = ModuleType("fastapi")
_fastapi.__path__ = []
_fastapi.HTTPException = HTTPException
_fastapi.APIRouter = lambda *a, **k: None
_fastapi.Depends = lambda *a, **k: None
_fastapi.HTTPBearer = lambda *a, **k: None
sys.modules.setdefault("fastapi", _fastapi)
_security = ModuleType("fastapi.security")
_security.HTTPBearer = lambda *a, **k: None
_security.HTTPAuthorizationCredentials = object
sys.modules.setdefault("fastapi.security", _security)
for name in ("jwt", "redis"):
    sys.modules.setdefault(name, ModuleType(name))
sys.modules.setdefault("psycopg", ModuleType("psycopg"))
_pkgs = {
    "psycopg.types": ModuleType("psycopg.types"),
    "psycopg.rows": ModuleType("psycopg.rows"),
}
_pkgs["psycopg.rows"].dict_row = lambda *a, **k: None
_jsonb = ModuleType("psycopg.types.json")
_jsonb.Jsonb = lambda obj, dumps=None: obj
_pkgs["psycopg.types.json"] = _jsonb
for name, mod in _pkgs.items():
    sys.modules.setdefault(name, mod)
os.environ.setdefault("JWT_SECRET", "test-secret")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("DATABASE_URL", "postgresql://localhost/business")
sys.modules["redis"].Redis = type("Redis", (), {"from_url": staticmethod(lambda *a, **k: object())})

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from within_level import permute  # noqa: E402

PASS, FAIL = 0, 0


def check(name, condition, detail=""):
    global PASS, FAIL
    if condition:
        PASS += 1
        print(f"  ✓ {name}")
    else:
        FAIL += 1
        print(f"  ✗ {name} {detail}")


class FakeDB:
    """模拟 sign_trials/sign_effect/sign_memos/sign_scores 及 FOR UPDATE 行锁。"""

    def __init__(self):
        self.state_lock = threading.RLock()         # 保护内部字典
        self._row_locks = {}                        # 锁实例持久，避免被回收
        self.held = threading.local()              # 当前线程已持有的行
        self.trials = {}
        self.effect = {}
        self.memos = {}
        self.effect_keys = set()
        self.memo_keys = set()
        self.scores = {}
        self.assignments = {}
        self.corrections = []
        self.history = []
        self.jobs = []

    def _held(self):
        codes = getattr(self.held, "codes", None)
        if codes is None:
            codes = set()
            self.held.codes = codes
        return codes

    def acquire_row(self, code):
        held = self._held()
        if code not in held:                       # 同线程可重入
            with self.state_lock:
                lock = self._row_locks.get(code)
                if lock is None:
                    lock = threading.RLock()
                    self._row_locks[code] = lock
            lock.acquire()
            held.add(code)

    def release_row(self, code):
        held = self._held()
        if code in held:
            held.discard(code)
            self._row_locks[code].release()

    def execute(self, sql, params=()):
        s = " ".join(sql.split())
        if "FROM sign_trials WHERE code=%s FOR UPDATE" in s:
            (code,) = params
            self.acquire_row(code)
            if code not in self.trials:
                raise HTTPException(404, "该试教轮次不存在")
            return _R(self.trials[code])
        if "FROM sign_trials WHERE code=%s" in s:
            (code,) = params
            if code not in self.trials:
                raise HTTPException(404, "该试教轮次不存在")
            return _R(self.trials[code])
        if s.startswith("UPDATE sign_trials SET state='frozen' WHERE code"):
            (code,) = params
            self.trials[code]["state"] = "frozen"
            return _R(None)
        if s.startswith("UPDATE sign_trials SET revision=%s, state='frozen'"):
            rev, code = params
            self.trials[code]["revision"] = rev
            self.trials[code]["state"] = "frozen"
            return _R(None)
        if s.startswith("UPDATE sign_trials SET state='evaluated'"):
            code, rev = params
            if self.trials[code]["revision"] == rev:
                self.trials[code]["state"] = "evaluated"
            return _R(None)
        if s.startswith("UPDATE sign_trials SET state='signed'"):
            (code,) = params
            self.trials[code]["state"] = "signed"
            return _R(None)
        if "state='revising'" in s and s.startswith("UPDATE sign_trials"):
            rev, code = params
            self.trials[code]["revision"] = rev
            self.trials[code]["state"] = "revising"
            return _R(None)
        if s.startswith("SELECT arm FROM sign_assignments"):
            code, learner = params
            arm = self.assignments.get((code, learner))
            return _R({"arm": arm} if arm is not None else None)
        if s.startswith("SELECT score FROM sign_scores"):
            code, learner = params
            return _R({"score": self.scores[(code, learner)]}
                      if (code, learner) in self.scores else None)
        if s.startswith("UPDATE sign_scores SET score=%s"):
            score, code, learner = params
            self.scores[(code, learner)] = score
            return _R(None)
        if s.startswith("UPDATE sign_effect SET valid=false"):
            code, rev = params
            self.effect[(code, rev)]["valid"] = False
            return _R(None)
        if s.startswith("SELECT * FROM sign_effect"):
            code, rev = params
            return _R(self.effect.get((code, rev)))
        if s.startswith("INSERT INTO sign_effect"):
            code, rev, effect, p, perms, detail = params
            if rev != self.trials[code]["revision"]:
                from effects import StaleRevision
                raise StaleRevision(code, rev, self.trials[code]["revision"])
            key = (code, rev)
            if key in self.effect_keys:
                raise RuntimeError("unique effect violated")
            self.effect_keys.add(key)
            self.effect[key] = {"trial": code, "revision": rev, "effect": effect,
                                "p_value": p, "permutations": perms,
                                "detail": detail, "valid": True}
            return _R(None)
        if s.startswith("INSERT INTO sign_memos"):
            code, rev, decision, rationale, reviewer = params
            if (code, rev) in self.memo_keys:
                raise RuntimeError("one memo per revision violated")
            self.memo_keys.add((code, rev))
            mid = len(self.memos) + 1
            self.memos[mid] = {"memo_id": mid, "trial": code, "revision": rev,
                               "decision": decision, "rationale": rationale,
                               "signed_by": reviewer}
            return _R(self.memos[mid])
        if s.startswith("INSERT INTO sign_corrections"):
            code, rev, reason, reviewer = params
            self.corrections.append({"trial": code, "revision": rev,
                                     "reason": reason, "accepted_by": reviewer})
            return _R(None)
        if s.startswith("INSERT INTO sign_score_history"):
            self.history.append(dict(zip(
                ["trial", "learner", "score", "actual_arm",
                 "revision", "source", "changed_by"], params)))
            return _R(None)
        if "INTO app_jobs" in s:
            payload = params[1]
            self.jobs.append((payload["code"], payload.get("revision")))
            return _R({"id": len(self.jobs)})
        raise AssertionError("unmapped SQL: " + s)


class _R:
    def __init__(self, row):
        self.row = row

    def fetchone(self):
        return self.row


class Tx:
    """模拟一个数据库事务：整个块持有该行锁，结束释放。"""

    def __init__(self, db, code):
        self.db, self.code = db, code

    def __enter__(self):
        self.db.acquire_row(self.code)
        return self.db

    def __exit__(self, *exc):
        self.db.release_row(self.code)
        return False


import corrections as corr_mod  # noqa: E402
import effects as eff_mod  # noqa: E402
import editor_decision as memo_mod  # noqa: E402
import lock_trial  # noqa: E402

ROSTER = []
for level, stem in [("beginner", "N"), ("returning", "R")]:
    for idx, arm in enumerate(["A", "A", "B", "B"], 1):
        ROSTER.append({"level": level, "arm": arm,
                       "learner": f"{stem}-{idx}", "score": None})


def fake_case(cx, code, lock=False):
    if lock:
        cx.execute("SELECT * FROM sign_trials WHERE code=%s FOR UPDATE", (code,))
        return cx.trials[code]
    return cx.execute("SELECT * FROM sign_trials WHERE code=%s", (code,)).fetchone()


def fake_sheet(cx, code):
    fake_case(cx, code)
    return [dict(r, score=cx.scores.get((code, r["learner"]))) for r in ROSTER]


def install(db):
    corr_mod.case = fake_case
    corr_mod.assignment_sheet = fake_sheet
    eff_mod.case = fake_case
    eff_mod.assignment_sheet = fake_sheet
    eff_mod.permute = permute
    memo_mod.case = fake_case
    lock_trial.case = fake_case
    lock_trial.assignment_sheet = fake_sheet
    enq = lambda cx, kind, payload, available_at=None: cx.execute(
        "INSERT INTO app_jobs(kind,payload) VALUES (%s,%s)", (kind, payload)).fetchone()["id"]
    corr_mod.enqueue = enq
    lock_trial.enqueue = enq


CODE = "SR-12"


def fresh_db():
    db = FakeDB()
    db.trials[CODE] = {"code": CODE, "state": "open", "revision": 1}
    for r in ROSTER:
        db.scores[(CODE, r["learner"])] = 60
        db.assignments[(CODE, r["learner"])] = r["arm"]
    install(db)
    return db


class Body:
    def __init__(self, learner, actual_arm, score, reason=None):
        self.learner, self.actual_arm, self.score, self.reason = \
            learner, actual_arm, score, reason


class MemoBody:
    def __init__(self, decision, rationale):
        self.decision, self.rationale = decision, rationale


def run_worker(db):
    code, rev = db.jobs.pop()
    try:
        with Tx(db, code):
            eff_mod.calculate(db, code, rev)
        return ("done", rev)
    except eff_mod.StaleRevision:
        return ("stale-failed", rev)


print("== 1. 正常冻结→计算→签批 ==")
db = fresh_db()
with Tx(db, CODE):
    lock_trial.lock(db, CODE)
check("首冻入队任务带 revision=1", db.jobs[-1] == (CODE, 1), str(db.jobs))
run_worker(db)
check("计算后状态 evaluated", db.trials[CODE]["state"] == "evaluated")
check("第1轮结果有效", db.effect[(CODE, 1)]["valid"] is True)
with Tx(db, CODE):
    memo_mod.sign(db, CODE, MemoBody("keep", "保留首版，等待下轮验证。"), "reviewer@demo.local")
check("签批后状态 signed", db.trials[CODE]["state"] == "signed")

print("== 2. 更正受理：旧结果立即失效，状态转 revising ==")
with Tx(db, CODE):
    corr_mod.accept(db, CODE, Body("N-1", "A", 90, "匿名答题抄错分，按答题卡更正。"), "reviewer@demo.local")
check("状态变为更正中", db.trials[CODE]["state"] == "revising")
check("旧结果 valid=false", db.effect[(CODE, 1)]["valid"] is False)
check("成绩已更新为 90", db.scores[(CODE, "N-1")] == 90)
check("留了更正受理单", len(db.corrections) == 1 and db.corrections[0]["revision"] == 1)
check("成绩流水含 correction 记录",
      any(h["source"] == "correction" and h["score"] == 90 for h in db.history))

print("== 3. 更正后拒绝用旧结果签批 ==")
try:
    with Tx(db, CODE):
        memo_mod.sign(db, CODE, MemoBody("keep", "试图用旧结果签批。"), "r@x")
    check("旧结果签批被拒绝", False)
except HTTPException as e:
    check("旧结果签批被拒绝（状态或依据失效，均为 409）", e.status_code == 409, str(e.detail))

print("== 4. 更正中不能重复更正；open/相同分/版本不符均拦截 ==")
for desc, make_db, body in [
    ("更正中拒绝再次受理", db, Body("N-2", "A", 80, "再次更正同一轮。")),
    ("open 状态拒绝更正", fresh_db(), Body("N-1", "A", 90, "未冻结就想更正。")),
]:
    try:
        with Tx(make_db, CODE):
            corr_mod.accept(make_db, CODE, body, "r@x")
        check(desc, False)
    except HTTPException as e:
        check(desc, e.status_code == 409)
for desc, body in [
    ("相同成绩拒绝受理", Body("N-1", "A", 90, "成绩相同的更正。")),
    ("版本不符拒绝受理", Body("N-1", "B", 90, "版本不符。")),
]:
    try:
        with Tx(db, CODE):
            corr_mod.accept(db, CODE, body, "r@x")
        check(desc, False)
    except HTTPException as e:
        check(desc, e.status_code == 409)

print("== 5. 重新冻结→新轮次结果→才能签新意见 ==")
with Tx(db, CODE):
    receipt = corr_mod.refreeze(db, CODE)
check("重新冻结后 revision=2", db.trials[CODE]["revision"] == 2 and receipt["revision"] == 2)
check("状态回到 frozen", db.trials[CODE]["state"] == "frozen")
check("新任务带 revision=2", db.jobs[-1] == (CODE, 2))
run_worker(db)
check("新结果有效且旧结果仍失效",
      db.effect[(CODE, 2)]["valid"] is True and db.effect[(CODE, 1)]["valid"] is False)
check("状态 evaluated", db.trials[CODE]["state"] == "evaluated")
with Tx(db, CODE):
    memo_mod.sign(db, CODE, MemoBody("defer", "依据第二轮结果延后决定。"), "reviewer@demo.local")
check("第二轮可签新意见", db.trials[CODE]["state"] == "signed")
check("两轮意见都留存", len(db.memos) == 2 and
      {m["revision"] for m in db.memos.values()} == {1, 2})

print("== 6. 旧计算任务晚到：不能恢复签批资格 ==")
db3 = fresh_db()
with Tx(db3, CODE):
    lock_trial.lock(db3, CODE)
run_worker(db3)
with Tx(db3, CODE):
    corr_mod.accept(db3, CODE, Body("N-1", "A", 90, "触发更正作废旧结果。"), "r@x")
try:
    with Tx(db3, CODE):
        eff_mod.calculate(db3, CODE, 1)   # 晚到的旧 revision=1 任务
    check("旧轮次任务被判 stale 失败", False)
except eff_mod.StaleRevision:
    check("旧轮次任务被判 stale 失败", True)
check("旧结果保持失效", db3.effect[(CODE, 1)]["valid"] is False)
check("状态仍是 revising", db3.trials[CODE]["state"] == "revising")
try:
    with Tx(db3, CODE):
        memo_mod.sign(db3, CODE, MemoBody("keep", "晚到任务后尝试签批。"), "r@x")
    check("晚到任务未恢复签批资格", False)
except HTTPException:
    check("晚到任务未恢复签批资格", True)

print("== 7. 并发：更正与签批同时发起，旧结果签批不得签成新版 ==")
db4 = fresh_db()
with Tx(db4, CODE):
    lock_trial.lock(db4, CODE)
run_worker(db4)
barrier = threading.Barrier(2)
errors = []


def do_correct():
    barrier.wait()
    try:
        with Tx(db4, CODE):
            corr_mod.accept(db4, CODE, Body("N-1", "A", 90, "并发场景下受理更正。"), "r@x")
    except HTTPException as e:
        errors.append(("correct", e.status_code))


def do_sign():
    barrier.wait()
    try:
        with Tx(db4, CODE):
            memo_mod.sign(db4, CODE, MemoBody("keep", "并发场景下尝试签批。"), "r@x")
    except HTTPException as e:
        errors.append(("sign", e.status_code))


with ThreadPoolExecutor(2) as pool:
    f1 = pool.submit(do_correct)
    f2 = pool.submit(do_sign)
    f1.result(); f2.result()
# 行锁使两事务串行。合法终态只有两种：
#  A) 更正先得锁：签批被拒，无意见，旧结果失效；
#  B) 签批先得锁：意见在更正前签署，随后更正把旧结果作废但意见留档。
memos = list(db4.memos.values())
check("至多产生一条意见（旧结果绝不能在更正后再签出新版）", len(memos) <= 1, str(len(memos)))
check("不存在引用当前轮次却已失效结果的意见",
      all(not (m["revision"] == db4.trials[CODE]["revision"]
               and not db4.effect[(CODE, m["revision"])]["valid"]) for m in memos))
if any(k == "sign" for k, _ in errors):
    check("A) 更正先得锁：签批被拒、状态更正中、无意见、旧结果失效",
          db4.trials[CODE]["state"] == "revising" and len(memos) == 0
          and db4.effect[(CODE, 1)]["valid"] is False, str(errors))
else:
    check("B) 签批先得锁：意见签署于第1轮（当时有效），更正后留档，轮次已推进",
          len(memos) == 1 and memos[0]["revision"] == 1
          and db4.trials[CODE]["revision"] == 2
          and db4.effect[(CODE, 1)]["valid"] is False
          and db4.trials[CODE]["state"] == "revising", str(errors))

print("== 8. 多轮更正链：revision 单调，历史完整 ==")
db5 = fresh_db()
with Tx(db5, CODE):
    lock_trial.lock(db5, CODE)
run_worker(db5)
for new_score in (70, 80):
    with Tx(db5, CODE):
        corr_mod.accept(db5, CODE, Body("N-1", "A", new_score, f"第{new_score}次更正。"), "r@x")
    with Tx(db5, CODE):
        corr_mod.refreeze(db5, CODE)
    run_worker(db5)
check("revision 推进到 3", db5.trials[CODE]["revision"] == 3)
check("仅最新轮结果有效",
      db5.effect[(CODE, 3)]["valid"] and not db5.effect[(CODE, 2)]["valid"]
      and not db5.effect[(CODE, 1)]["valid"])
check("两次更正受理单均留存", len(db5.corrections) == 2)
check("成绩流水保留全部变更",
      [h["score"] for h in db5.history if h["source"] == "correction"] == [70, 80])

print(f"\n结果：通过 {PASS}，失败 {FAIL}")
sys.exit(1 if FAIL else 0)
