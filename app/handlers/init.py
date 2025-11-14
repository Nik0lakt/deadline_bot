from .common import router as common_router
from .tasks import router as tasks_router

def setup_routers(dp):
    dp.include_router(common_router)
    dp.include_router(tasks_router)
