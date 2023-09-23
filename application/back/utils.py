from datetime import datetime, timedelta
from typing import Tuple, List, Any
 

def translate_day(name: str) -> str:
    name_part = ["lun", "mar", "mer", "jeu", "ven", "sam", "dim"]
    day = ["Lundi","Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi","Dimanche"]

    for d in zip(name_part, day):
        if d[0] in name.lower():
            return d[1]
        

def get_delay(time: datetime.time) -> float:
    now = datetime.now()
    next_task = datetime.now().replace(hour=time.hour,minute=time.minute)
    return (next_task - now).total_seconds()

def get_delay_from_datetime(time:Tuple[int, int, int]) -> float:
    """gte delay in sec between specific time and a delta"""
    now = datetime.now()
    next_start = (now.replace(hour=time[0], 
                             minute=time[1], 
                             second=time[2], 
                             microsecond=0) 
                  + timedelta(days= 1))
    
    return (next_start - now).total_seconds()
    



def reject_particular_shift() -> List[Tuple[str, str, Any]]:
    """filter service than should not be affected by the application."""
    prtclr = [
        "TRAV",
        "COMM", 
        "ACH", 
        "BUV", 
        "ACC", 
        "HYG", 
        "AME", 
        "Service volants",
        "BDM", 
        "COMPTA", 
        "INFO",
        "MICR"
    ]
    return [("name", "not like", n) for n in prtclr]


def get__appropriate_stype(stype: str, point: int) -> str:
    """
    determine wether member with standard shift type 
    should be attributed to ftop or standart shift tickets.
    
    std point == 0 (up to date) -> ftop
    std point < 0  (catch up) -> std
    
    shift tickets impact type of point to increment when service is done.
    """
    if stype == "standard" and point == 0:
        stype =  "ftop"
    elif stype == "standard" and point < 0:
        stype = "standard"
    elif stype == "ftop":
        stype = "ftop"
        
    return stype

