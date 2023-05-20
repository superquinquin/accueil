"""
SOCKETIO EVENTS RESPONSE
"""

from flask import url_for
from flask_socketio import emit, join_room
from typing import Dict, Any


from .. import socketio, cache
from application.back.odoo import Odoo
from application.back.shift import Shift
from application.back.member import Member
from application.back.utils import get__appropriate_stype


@socketio.on('shift-init')
def init_shift():
    """
    from current_dshifts cache,
    generate shift payload
    generate shift registration payload
    of current shifts
    
    emit:
        emit payload to populate client
        with shifts and shifts registrations 
        of current shifts
    """
    global cache
    
    context = []
    for shift in cache['current_shifts']:
        payload = shift.payload()
        payload["members"] = [m.payload() for m in list(shift.members.values())]
        context.append(payload)
    emit('load-init-data', context, include_self=True) 
    

@socketio.on('all-shift-init')
def init_all_shifts():
    """
    from shifts cache,
    generate shift payload
    generate shift registration payload
    
    emit:
        emit payload to populate client
        with shifts and shifts registrations
    """
    global cache
    
    context = []
    for shift in cache['shifts'].values():
        payload = shift.payload()
        payload["members"] = [m.payload() for m in list(shift.members.values())]
        context.append(payload)
    emit('load-init-data', context, include_self=True) 



@socketio.on('confirm-presence')
def confirm_presence(context: Dict[str, Any]):
    """
    modify status of shift registration record
    
    context:
        registration_id: shift registration record id to update
        shift_id       : shift record id containing registration to update
        partner_id     : search cache member to update status localy.
    
    emit:
        broadcast new status for shift registration.
        update accordingly the style of the shift registration record.
    """
    global cache
    config = cache["config"]
    api = Odoo()
    api.connect(
        config.API_URL, 
        config.SERVICE_ACCOUNT_LOGGIN, 
        config.SERVICE_ACCOUNT_PASSWORD, 
        config.API_DB, 
        config.API_VERBOSE
    )
    
    api.post_presence(context['registration_id'])
    shift  = cache["shifts"][context["shift_id"]]
    member = shift.members[context["partner_id"]]
    member.state = "done"
    emit('update-on-presence', context,  broadcast=True, include_self=True)


@socketio.on('search-member')
def search_member(context: Dict[str, Any]):
    """
    On client searching member to create shift registration record
    search corresponding res partner
    
    context:
        input (str): can be string reprensention of int or a name
        
    emit:
        return to client corresponding partners
    """
    global cache
    
    config = cache["config"]
    
    api = Odoo()
    api.connect(
        config.API_URL, 
        config.SERVICE_ACCOUNT_LOGGIN, 
        config.SERVICE_ACCOUNT_PASSWORD, 
        config.API_DB, 
        config.API_VERBOSE
    )

    if context["input"].isnumeric():
        m = api.get("res.partner", [("barcode_base","=", context["input"])])
        members = tuple((m.id, m.barcode_base, m.name))
        l = 1
    
    else:
        m = api.browse("res.partner", [("name","ilike", context["input"])])
        members = [tuple((mb.id, mb.barcode_base, mb.name)) for mb in m] 
        l = len(members)
        
    socketio.emit("populate-search-members", {"members":members, "l": l}, include_self= True)




@socketio.on('register-catching-up')
def register_member_catching_up(context: Dict[str, Any]):
    """
    determine main member attached to this request.
    determine if catching up member and select shift type accordingly.
    create shift registration record from context shared by client
    
    context:
        shift_id  : shift related to the shift registration
        partner_id: partner related to the shift registration
        
    emit:
        boradcast new shift registration.
        populate related shift with new record.
    """
    global cache
    config = cache["config"]
    
    api = Odoo()
    api.connect(
        config.API_URL, 
        config.SERVICE_ACCOUNT_LOGGIN, 
        config.SERVICE_ACCOUNT_PASSWORD, 
        config.API_DB, 
        config.API_VERBOSE
    )
    
    
    member = api.get("res.partner", [("id", "=", context["partner_id"])])
    if member.is_associated_people:
        main_member = api.get("res.partner", [("id", "=", member.parent_id)])
    else:
        main_member = member
            
    stype = main_member.shift_type
    if stype == "standard":
        std_points = main_member.final_standard_point
        stype = get__appropriate_stype(stype, std_points)
    stid = cache["shifts"][int(context["shift_id"])].shift_tikets_id.get(stype)
    
    service = api.register_member_to_shift(
        int(context["shift_id"]),
        int(main_member.id),
        stid,
        stype
    )
    
    member = api.create_main_member(service)
    cache["shifts"][int(context["shift_id"])].members[int(context["partner_id"])] = member
    
    payload = {
        "shift_id": int(context["shift_id"]),
        "members": member.payload()
    }
    
    socketio.emit(
        "add-catching-up-member-to-shift",
        payload,
        include_self= True,
        broadcast=True
    )