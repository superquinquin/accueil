"""
SOCKETIO EVENTS RESPONSE
"""

from flask import url_for
from flask_socketio import emit, join_room

from .. import socketio, cache
from application.back.odoo import Odoo
from application.back.shift import Shift
from application.back.member import Member

@socketio.on('shift-init')
def init_shift():
    """CLIENT INITIAL CALL TO POPULATE INDEX TEMPLATE (SHIFT)
    WHITH RELEVANT DATA Shift & Member data
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
    """CLIENT INITIAL CALL TO POPULATE INDEX TEMPLATE (ALL_SHIFT)
    WHITH RELEVANT DATA Shift & Member data
    """
    global cache
    
    context = []
    for shift in cache['shifts'].values():
        payload = shift.payload()
        payload["members"] = [m.payload() for m in list(shift.members.values())]
        context.append(payload)
    emit('load-init-data', context, include_self=True) 



@socketio.on('confirm-presence')
def confirm_presence(context: dict):
    """RESPONSE TO CLIENT CONFIRMING PRESENCE TO SHIFT.
    MODIFY SHIFT.REGISTRATION STATE BY "done".

    Args:
        context (dict): _description_
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
def search_member(context):
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
def register_member_catching_up(context):
    global cache
    
    print(context)
    config = cache["config"]
    
    api = Odoo()
    api.connect(
        config.API_URL, 
        config.SERVICE_ACCOUNT_LOGGIN, 
        config.SERVICE_ACCOUNT_PASSWORD, 
        config.API_DB, 
        config.API_VERBOSE
    )
    
    # is the main member
    (is_assoc, parent_id, stype) = api.associated_member(context["partner_id"])
    sid = cache["shifts"][int(context["shift_id"])].shift_tikets_id.get("ftop")
    
    if is_assoc:
        service = api.register_member_to_shift(
            int(context["shift_id"]),
            int(parent_id),
            sid,
            stype
        )
    
    else:
        service = api.register_member_to_shift(
            int(context["shift_id"]),
            int(context["partner_id"]),
            sid,
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
