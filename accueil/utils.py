
from xmlrpc.client import Fault

from accueil.exceptions import (
    AccueilException,
    TooManyRegistrationsSet,
    DuplicateRegistration,
    UnknownXmlrcpError
)

def translate_day(name: str) -> str:
    name_part = ["lun", "mar", "mer", "jeu", "ven", "sam", "dim"]
    day = ["Lundi","Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi","Dimanche"]

    for d in zip(name_part, day):
        if d[0] in name.lower():
            return d[1]
        
def get_appropriate_shift_type(shift_type: str, point: int) -> str:
    """
    determine wether member with standard shift type 
    should be attributed to ftop or standart shift tickets.
    
    std point == 0 (up to date) -> ftop
    std point < 0  (catch up) -> std
    
    shift tickets impact type of point to increment when service is done.
    """
    if shift_type == "standard" and point == 0:
        shift_type =  "ftop"
    elif shift_type == "standard" and point < 0:
        shift_type = "standard"
    elif shift_type == "ftop":
        shift_type = "ftop"
    return shift_type

def handle_odoo_exceptions(fault: Fault) -> AccueilException:
    if "already has 5 registrations in the preceding 28 days" in fault.faultCode:
        return TooManyRegistrationsSet()
    elif "This partner is already registered on this Shift" in fault.faultCode:
        return DuplicateRegistration()
    else:
        return UnknownXmlrcpError()
    
def into_batches(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i:i + n]

def translate_shift_status(status: str) -> str:
    translation_map = {
        "open": "Confirmé",
        "replaced": "Remplacé",
        "replacing": "Remplaçant",
        "absent": "Absent",
        "cancel": "Annulé",
        "draft": "Non Confirmé", 
        "done": "Présent",
        "waiting": "En attente",
        "excused": "Excusé"
    }
    return translation_map.get(status, status)

def translate_coop_status(status: str) -> str:
    translation_map = {
        "exempted": "Exempté",
        "up_to_date": "A jour", 
        "suspended": "Suspendu", 
        "alert": "En Alerte", 
        "vacation": "En Congés",
        "not_concerned": "Non Concerné", 
        "delay": "Delai",
        "unsubscribed": "Désinscrit"
        }
    return translation_map.get(status, status)