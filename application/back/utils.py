from datetime import datetime, timedelta
from typing import Tuple
 

def translate_day(name: str) -> str:
    name_part = ["lun", "mar", "mer", "jeu", "ven", "sam", "dim"]
    day = ["Lundi","Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi","Dimanche"]

    for d in zip(name_part, day):
        if d[0] in name.lower():
            return d[1]
        

def get_delay(time: datetime.time) -> int:
    now = datetime.now().time()
    
    return (abs(time.hour - now.hour) * 60 +
            abs(time.minute - now.minute)) * 60

def get_delay_from_datetime(time:Tuple[int, int, int]):
    now = datetime.now()
    next_start = (now.replace(hour=time[0], 
                             minute=time[1], 
                             second=time[2], 
                             microsecond=0) 
                  + timedelta(days= 1))
    
    return (next_start - now).total_seconds()
    



def reject_particular_shift():
    prtclr = ["TRAV",
        "COMM", 
        "ACH", 
        "BUV", 
        "ACC", 
        "HYG", 
        "AME", 
        "Service volants",
        "BDM", 
        "COMPTA", 
        "INFO"
    ]
    return [("name", "not like", n) for n in prtclr]
