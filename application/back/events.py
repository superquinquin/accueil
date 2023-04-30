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

