"""
IMPL SHIFT STRUCT
BASED ON SHIFT.SHIFT MODEL
"""
from typing import Dict
from application.back.member import Member

class Shift:
    def __init__(self, 
                 id, 
                 shift_type_id, 
                 shift_tmpl_id, 
                 shift_tikets_id,
                 day, 
                 wk_name, 
                 begin, 
                 end, 
                 state) -> None:
        self.id: int = id
        self.shift_type_id: int = shift_type_id
        self.shift_tmpl_id: int = shift_tmpl_id
        self.shift_tikets_id: Dict[str, int] = shift_tikets_id
        self.day: str = day
        self.week_name: str = wk_name
        self.begin: str = begin,
        self.end: str = end
        self.sate: str = state
        self.members: Dict[Member] = {}
    
    
    def correct_auto_singleton_transform(self):
        """CORRECT BEGIN_DATE_TZ THAT AUTOMATICALLY RETURN IN TUPLE FORMAT
        TRANSLATE self.begin to string
        """
        self.begin = self.begin[0]
        
    def format_shift_name(self) -> str:
        """RECONSTRUCT SHIFT NAME
        WITH DAY NAME, BEGIN HOUR AND END HOUR

        Returns:
            str: shift name to be deisplayed in client.
        """
        return  f"{self.day} {self.begin} - {self.end}"
    
    def payload(self) -> dict:
        """BUILD PAYLOAD WITH SHIFT NECESSARY DATA
        Returns:
            dict: payload
        """
        d = {
            "shift_id": self.id,
            "display_shift_name": self.format_shift_name()
            }
        return d