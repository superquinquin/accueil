
from sanic import Sanic

from accueil.scheduler import Scheduler

async def start_scheduler(app: Sanic):
    await app.add_task(Scheduler.initialize(app), name="scheduler")
    