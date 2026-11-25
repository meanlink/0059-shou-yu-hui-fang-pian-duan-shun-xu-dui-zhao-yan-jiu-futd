from fastapi import APIRouter
from versions_api import router as router_0
from scores_api import router as router_1
from effect_api import router as router_2
from memo_api import router as router_3
from replay_seed import seed
from replay_worker import run as run_job

router = APIRouter(prefix="/api")
router.include_router(router_0)
router.include_router(router_1)
router.include_router(router_2)
router.include_router(router_3)
