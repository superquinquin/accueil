"""
IMPL MEMBER STRUCT
MIRROR ODOO RES.PARTNER MODEL WITH FEW USEFUL FIELDS
"""
from typing import Union, Dict, Any

class Member:
    def __init__(
        self, 
        id, 
        shift_id,
        registration_id,
        parent_id,
        name, 
        barcode,
        has_associated_member, 
        is_associated_member, 
        shift_type, 
        exchange_state, 
        state,
        member
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
        
    
    def generate_display_name(self) -> None:
        """DISPLAY NAME TEMPLATE FOR CLIENT.
        CONTAINING Partner_id, Partner_id.name AND ASSOCIATED Partner_id.name
        """
        if self.has_associated_member:
            self.display_name = f"{self.barcode} - {self.name} en binôme avec {self.associate.name}"
        else:
            self.display_name = f"{self.barcode} - {self.name}"
            
            
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