from __future__ import annotations

import json
import asyncio
import logging
from sanic import Sanic
from threading import Timer
from collections import deque, OrderedDict
from attrs import define, field
from datetime import datetime, timedelta

from typing import Callable

from accueil.models.odoo import Odoo
from accueil.models.shift import Shift
from accueil.channel import Channel
from accueil.mail import MailManager
from accueil.exceptions import UnknownShift

logger = logging.getLogger("scheduler")

@define(repr=False)
class Task(object):
    action: Callable = field()
    shift_id: int = field()
    time: datetime = field()
    
    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}: {self.action.__name__} shift {self.shift_id} at {self.time.strftime('%H:%M:%S')}>"
    
    async def add(self, app: Sanic) -> None:
        channel: Channel = app.ctx.channels.get("registration")
        shift = app.ctx.shifts.get(self.shift_id, None)
        if shift is None:
            raise UnknownShift()
        app.ctx.current_shifts.update({self.shift_id:shift})
        await channel.broadcast(json.dumps({"message": "reload", "data": {}}))
        
    async def rm(self, app: Sanic) -> None:
        channel: Channel = app.ctx.channels.get("registration")
        app.ctx.current_shifts.pop(self.shift_id)
        await channel.broadcast(json.dumps({"message": "reload", "data": {}}))
    
    async def refresh(self, app: Sanic) -> None:
        cycles = app.ctx.cycles
        odoo: Odoo = app.ctx.odoo
        members = odoo.get_shift_members(self.shift_id, cycles)
        shift: Shift = app.ctx.shifts.get(self.shift_id, None)
        if shift is None:
            raise UnknownShift()
        shift.refresh_shift_members(*members)

    async def execute(self, app: Sanic) -> None:
        callback = self.action
        await callback(self, app)
    
    
@define
class Scheduler(object):
    __queue: deque[Task] = field(default=deque([]))

    @property
    def queue(self):
        return self.__queue

    @classmethod
    async def initialize(cls, app: Sanic) -> Scheduler:
        scheduler = cls()
        await scheduler.initialize_queue(app)
        await scheduler.runner(app)
        return scheduler
               
    async def initialize_queue(self, app: Sanic) -> None:
        """first tasks of the day"""
        odoo: Odoo = app.ctx.odoo
        
        cycles = odoo.get_cycle()
        shifts = odoo.build_shifts(cycles)
        ftop_shifts = odoo.build_shifts(cycles, ftop=True)
        app.ctx.cycles = cycles
        app.ctx.ftop_shifts = {shift.shift_id:shift for shift in ftop_shifts}
        app.ctx.shifts = {shift.shift_id:shift for shift in shifts}
        app.ctx.current_shifts = OrderedDict() # dict[shift_id, Shift]
        self._build_queue(app)
        await self._fast_forward(app)

    def close(self, app: Sanic) -> None:
        set_absences = app.config.AUTO_ABSENCE_NOTATION or False
        close_shifts = app.config.AUTO_CLOSE_SHIFTS or False
        close_ftop = app.config.AUTO_CLOSE_FTOP_SHIFT or False
        send_absence_mails = app.config.AUTO_ABSENCE_MAILS or False
         
        odoo: Odoo = app.ctx.odoo
        shifts: dict[int, Shift] = app.ctx.shifts
        ftop_shifts: dict[int, Shift] = app.ctx.ftop_shifts
        mail_manager: MailManager = app.ctx.mail_manager
        
        if set_absences:
            odoo.set_regular_shifts_absences(shifts)
            if close_shifts:
                [odoo.close_shift(shift) for shift in shifts.values()]
            if send_absence_mails:
                [mail_manager.send_absence_mails(shift) for shift in shifts.values()]
                
            
        if close_ftop:
            [odoo.close_shift(shift) for shift in ftop_shifts.values()]
            
    def _build_queue(self, app: Sanic) -> None:
        early = app.config.ACCEPT_EARLY_ENTRANCE or {"minutes": 15}
        late = app.config.ACCEPT_LATE_ENTRANCE or {"minutes": 0}
        
        tasks = []
        for shift in app.ctx.shifts.values():
            tasks.append(Task(Task.refresh, shift.shift_id, shift.begin - timedelta(**early) - timedelta(minutes=5)))
            tasks.append(Task(Task.add, shift.shift_id, shift.begin - timedelta(**early)))
            tasks.append(Task(Task.rm, shift.shift_id, shift.end - timedelta(**late)))
        tasks.sort(key=lambda x: x.time)
        self.__queue = deque(tasks)        

    async def _fast_forward(self, app: Sanic) -> None:
        while len(self.queue) > 0 and self.queue[0].time < datetime.now():
            task = self.__queue.popleft()
            if task.action.__name__ != "refresh":
                await task.execute(app)

    async def _close_and_rebuild_queue(self, app: Sanic) -> None:
        """last tasks of the day"""
        
        # self.close(app)
        await self.initialize_queue(app)
        
    async def runner(self, app: Sanic):
        while True:
            while len(self.queue) > 0:
                task = self.__queue.popleft()
                interval = (task.time - datetime.now()).total_seconds()
                logger.info(f"NEXT TASk {task} in {round(interval, 2)}secs")
                await asyncio.sleep(interval)
                await task.execute(app)
                
            scheduled_rebuild = datetime.now().replace(hour=0, minute=10, second=0) + timedelta(days=1)
            interval = (scheduled_rebuild - datetime.now()).total_seconds()
            logger.info(f"CLOSING DAY TASK in {round(interval, 2)}secs")
            await asyncio.sleep(interval)
            await self._close_and_rebuild_queue(app)