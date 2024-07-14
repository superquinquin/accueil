
from sanic import Sanic

from accueil.scheduler import Scheduler

async def start_scheduler(app: Sanic):
    app.ctx.scheduler = Scheduler.initialize(app)
    