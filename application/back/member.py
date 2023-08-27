"""
IMPL MEMBER STRUCT
MIRROR ODOO RES.PARTNER MODEL WITH FEW USEFUL FIELDS
"""
from __future__ import annotations
from datetime import datetime, date
from typing import Union, Dict, Any, Optional

class Member:
    def __init__(
        self,
        *,        
        id: int, 
        name: str, 
        barcode: str,
        cycle_type: str = "standard",
        date: Optional[str] = None,
        start_hours: Optional[str] = None,
        end_hours: Optional[str] = None,
        gender: Optional[str] = None,
        shift_id: Optional[int] = None,
        registration_id: Optional[int] = None,
        parent_id: Optional[int] = None,
        has_associated_member: bool = False, 
        is_associated_member: bool = True, 
        shift_type: Optional[str] = None, 
        exchange_state: Optional[str] = None, 
        state: Optional[str] = None,
        member: Optional[Member] = None,
        start_cycle: Optional[datetime] = None,
        end_cycle: Optional[datetime] = None,
        std_counter: Optional[int] = None,
        ftop_counter: Optional[int] = None,
        mail: Optional[str] = None,
        ) -> None:
        
        self.id: int = id
        self.shift_id: Union[None, int] = shift_id
        self.registration_id: Union[None, int] = registration_id
        self.parent_id: Union[None, int] = parent_id
        self.name: str = name
        self.barcode: int = barcode
        self.has_associated_member: bool = has_associated_member
        self.is_associated_member: bool = is_associated_member
        
        self.shift_type: Union[None, str] = shift_type
        self.exchange_state: Union[None, str] = exchange_state
        self.state: Union[None, str] = state
        self.associate: Union[None, Member] = member
        
        self.cycle_type = cycle_type
        self.start_cycle_date = start_cycle
        self.end_cycle_date = end_cycle
        
        self.gender = gender
        self.std_counter = std_counter
        self.ftop_counter = ftop_counter
        self.mail = mail
        self.date = date
        self.start_hours = start_hours
        self.end_hours = end_hours
        
        self.generate_mail_name()
    
    def generate_display_name(self) -> None:
        """DISPLAY NAME TEMPLATE FOR CLIENT.
        CONTAINING Partner_id, Partner_id.name AND ASSOCIATED Partner_id.name
        """
        if self.has_associated_member:
            self.display_name = f"<strong>{self.barcode}</strong> - {self.name} en binôme avec {self.associate.name}"
        else:
            self.display_name = f"<strong>{self.barcode}</strong> - {self.name}"
    
    
    def generate_mail_name(self) -> None:
        self.mail_name = self.name
        name = self.name.split(",")
        if len(name) > 1:
            self.mail_name = name[1].Strip()
            
    def payload(self) -> Dict[str, Any]:
        """BUILD PAYLOAD WITH MEMBER NECESSARY DATA

        Returns:
            dict: _description_
        """
        
        d = {
            "id": self.id,
            "registration_id": self.registration_id,
            "display_name": self.display_name,
            "state": self.state
            } 
        
        return d