import traceback
import json as js
from sanic import Blueprint, Request, Websocket
from sanic.response import json, HTTPResponse
from sanic_ext import render

from accueil.channel import Channel
from accueil.models.odoo import Odoo
from accueil.models.shift import Shift



basebp = Blueprint("Basebp", "/")
registrationbp = Blueprint("shiftsbp", "/registration")

@basebp.get("/")
async def shifts(request: Request) -> HTTPResponse:
    shifts = request.app.ctx.current_shifts.values()    
    return await render("shifts.html", context= {"shifts": [shift.payload for shift in shifts]})

@basebp.get("/all")
async def all_shifts(request: Request) -> HTTPResponse:
    shifts = request.app.ctx.shifts.values()
    return await render("shifts.html", context= {"shifts": [shift.payload for shift in shifts]})

@basebp.get("/admin")
async def all_shifts_admin_view(request: Request) -> HTTPResponse:
    return json()


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
            payload = js.loads(payload)
            message = payload["message"]
            data = payload["data"]
            if message == "attend":
                odoo: Odoo = request.app.ctx.odoo
                shifts = request.app.ctx.shifts
                
                shift = shifts.get(data["shift_id"])
                member = shift.members.get(data["partner_id"])
                odoo.set_attendancy(member)
                await ws.send(js.dumps({"message":"closeCmodal", "data": data}))
            elif message == "reset":
                odoo: Odoo = request.app.ctx.odoo
                shifts = request.app.ctx.shifts
                
                shift = shifts.get(data["shift_id"])
                member = shift.members.get(data["partner_id"])
                odoo.reset_attendancy(member)
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
                await ws.send(js.dumps({"message":"CloseCatchingUpModal", "data": payload["data"]}))
                
            else:
                # unintented messages shouldn't be send from the application frame.
                ws.close()
            
            await channel.broadcast(js.dumps(payload)) 
        except Exception as e:
            print(traceback.format_exc())
            print(e)
        
        
        