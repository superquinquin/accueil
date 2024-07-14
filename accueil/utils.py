

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