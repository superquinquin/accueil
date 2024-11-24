import logging
import traceback
import json as js
from xmlrpc.client import Fault
from socket import gaierror
from sanic import Blueprint, Request, Websocket
from sanic.response import json, HTTPResponse, empty
from sanic_ext import render

from accueil.channel import Channel
from accueil.models.odoo import Odoo
from accueil.models.shift import Shift
from accueil.exceptions import UnknownXmlrcpError, UnknownSocketError
from accueil.utils import handle_odoo_exceptions

logger = logging.getLogger("endpointAccess")

basebp = Blueprint("Basebp", "/")
registrationbp = Blueprint("shiftsbp", "/registration")

@basebp.get("/favicon.ico")
async def favicon(_: Request):
    return empty()

@basebp.get("/")
async def shifts(request: Request) -> HTTPResponse:
    shifts = request.app.ctx.current_shifts.values()
    return await render("shifts.html", context= {"shifts": [shift.payload for shift in shifts]})

@basebp.get("/all")
async def all_shifts(request: Request) -> HTTPResponse:
    shifts = request.app.ctx.shifts.values()
    return await render("shifts.html", context= {"shifts": [shift.payload for shift in shifts]})

@basebp.get("/admin")
async def shifts_admin_view(request: Request) -> HTTPResponse:
    shifts = request.app.ctx.current_shifts.values()
    return await render("admin.html", context= {"shifts": [shift.admin_payload for shift in shifts]})

@basebp.get("/admin/all")
async def all_shifts_admin_view(request: Request) -> HTTPResponse:
    shifts = request.app.ctx.shifts.values()
    return await render("admin.html", context= {"shifts": [shift.admin_payload for shift in shifts]})


@registrationbp.post("/search_member")
async def search_member(request: Request) -> HTTPResponse:

    data = request.json
    odoo: Odoo = request.app.ctx.odoo
    inp: str = data["input"]

    if inp.isnumeric():
        payload = odoo.get_members_from_barcodebase(int(inp))
    else:
        payload = odoo.get_members_from_name(inp)

    return json({"status": 200, "reasons": "Ok", "data": payload}, status=200)



@registrationbp.websocket("/")
async def registration(request: Request, ws: Websocket):
    channel: Channel = request.app.ctx.channels.get("registration")
    channel.subscribe(ws)
    while True:
        payload = await ws.recv()
        try:
            if payload is None:
                logger.error("WS received no payload")
                raise ValueError("WS received no payload")
            payload = js.loads(payload)

            message = payload["message"]
            data = payload["data"]
            if message == "attend":
                odoo: Odoo = request.app.ctx.odoo
                shifts = request.app.ctx.shifts

                shift = shifts.get(data["shift_id"])
                member = shift.members.get(data["partner_id"])
                if member is None:
                    logger.error("ATTENDING operation on an Unknow member")
                    raise ValueError("Operation on an Unknow member")

                odoo.set_attendancy(member)
                logger.info(f"ATTENDING {member}")
                await ws.send(js.dumps({"message":"closeCmodal", "data": data}))
            elif message == "reset":
                odoo: Odoo = request.app.ctx.odoo
                shifts = request.app.ctx.shifts

                shift = shifts.get(data["shift_id"])
                member = shift.members.get(data["partner_id"])
                if member is None:
                    logger.error("RESET operation on an Unknow member")
                    raise ValueError("Operation on an Unknow member")
                odoo.reset_attendancy(member)
                logger.info(f"RESET {member}")
                await ws.send(js.dumps({"message":"closeCmodal", "data": data}))

            elif message == "registrate":
                odoo: Odoo = request.app.ctx.odoo
                cycles = request.app.ctx.cycles
                shifts = request.app.ctx.shifts
                shift: Shift = shifts.get(data["shift_id"])

                registration_record = odoo.registrate_attendancy(data["partner_id"], shift)
                member = odoo.build_member(registration_record, cycles)
                shift.add_shift_members(member)
                payload["data"].update({"partner_id": member.partner_id, "html": member.into_html()})
                logger.info(f"REGISTRATING {member}")
                await ws.send(js.dumps({"message":"closeRegistrationModal", "data": payload["data"]}))

            else:
                # unintented messages shouldn't be send from the application frame.
                logger.info(f"UNEXPECTED CALL from {str(request.socket)}. closing websocket...")
                await ws.close()

            await channel.broadcast(js.dumps(payload))

        except Exception as e:
            if isinstance(e, Fault):
                error = handle_odoo_exceptions(e)
            elif isinstance(e, gaierror):
                error = UnknownSocketError()
            else:
                error = UnknownXmlrcpError()

            if isinstance(error, UnknownXmlrcpError) or isinstance(error, UnknownSocketError):
                logger.error(traceback.format_exc())
            else:
                logger.error(f"{request.host} > {request.method} {request.url} : {str(error)} [{str(error.status)}][{str(len(str(error.message)))}b]")
            data = {"status": error.status, "reasons": error.message}
            await ws.send(js.dumps({"message":"error", "data": data}))
