from __future__ import annotations

from datetime import datetime, timedelta
from erppeek import Record
from attrs import define, field, validators
from typing import Any, Optional, Literal

from accueil.utils import translate_day



@define
class Cycle(object):
    shift_id: int = field(validator=[validators.instance_of(int)])
    name: str = field(validator=[validators.instance_of(str)])
    begin: datetime = field(validator=[validators.instance_of(datetime)])
    end: datetime = field(validator=[validators.instance_of(datetime)])

    @property
    def cycle(self) -> str:
        cycle = "ABCD"
        if "BSam" in self.name:
            cycle = "CDAB"
        return cycle
    
    @classmethod
    def from_record(cls, shift_record: Record) -> Cycle:
        end = datetime.fromisoformat(shift_record.date_begin_tz) # is actually end of cycle
        begin = end - timedelta(days=28)
        return cls(
            shift_record.id,
            shift_record.name,
            begin,
            end
        )
    
    def is_current(self) -> bool:
        now = datetime.now()
        return (now >= self.begin and now <= self.end)

@define(repr=False, slots=False, kw_only=True)
class ShiftMember:
    #ids
    partner_id: int = field(validator=[validators.instance_of(int)])
    name: str = field(validator=[validators.instance_of(str)])
    barcode: int = field(validator=[validators.instance_of(int)])

    shift_id: Optional[int] = field(default=None,)
    registration_id: Optional[int] = field(default=None)
    parent_partner_id: Optional[int] = field(default=None) #only for associated
    
    shift_type: Optional[str] = field(default=None)
    begin: Optional[datetime] = field(default=None)
    end: Optional[datetime] = field(default=None)
    exchange_state: Optional[str] = field(default=None)
    state: Optional[str] = field(default=None)
    coop_state: Optional[str] = field(default=None)
    
    gender: Optional[str] = field(default="neutral")
    leader: bool = field(default=False)
    std_counter: Optional[int] = field(default=None)
    ftop_counter: Optional[int] = field(default=None)
    mail: Optional[str] = field(default=None)
    has_associated_members: bool = field(default=False)
    is_associated_member: bool = field(default=False)    
    
    associated_members: Optional[list[ShiftMember]] = field(default=None) 
    cycle: Optional[Cycle] = field(default=None)
    cycle_type: Literal["standard", "ftop"] = field(default=None)

    
    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}: {self.partner_id} {self.name}>"
    
    @property
    def display_name(self) -> str:
        display_name = f"<strong>{self.barcode}</strong> -"
        if self.leader:
            display_name += f' <span class="leader">🌟</span> '
        if len(self.associated_members) > 0:
            display_name += f" {self.name} en binôme avec {self.associated_members[0].name}"
        else:
            display_name += f" {self.name}"
        if self.state == "done":
            display_name += "<span>✓</span>"
        return display_name
    
    @property
    def mail_name(self) -> str:
        mail_name = self.name
        name = self.name.split(",")
        if len(name) > 1:
            mail_name = name[1].strip()        
        return mail_name
    
    @property
    def payload(self) -> dict[str, Any]:
        return {
            "partner_id": self.partner_id,
            "registration_id": self.registration_id,
            "shift_id": self.shift_id,
            "state": self.state,
            "display_name": self.display_name
        }
    
    @classmethod
    def from_record(cls, record: Record, cycle: Cycle | None = None) -> ShiftMember:
        """shift.registration record"""
        return cls(
            partner_id = record.partner_id.id,
            name = record.name,
            barcode = record.partner_id.barcode_base,
            shift_id = record.shift_id.id,
            registration_id = record.id,
            shift_type = record.shift_type,
            begin = datetime.fromisoformat(record.date_begin) + timedelta(hours=2),
            end = datetime.fromisoformat(record.date_begin) + timedelta(hours=4, minutes=45),
            exchange_state = record.exchange_state,
            state = record.state,
            coop_state = record.partner_id.cooperative_state,
            gender = record.partner_id.gender or None,
            leader = record.partner_id.is_squadleader,
            std_counter = int(record.partner_id.final_standard_point),
            ftop_counter = int(record.partner_id.final_ftop_point),
            mail = record.partner_id.email or None,
            has_associated_members = bool(record.partner_id.nb_associated_people),
            is_associated_member = record.partner_id.is_associated_people,
            associated_members=[],
            cycle = cycle,
            cycle_type = "ftop" if cycle else "standard"
        )
    
    @classmethod
    def associated_member_from_record(cls, record: Record) -> ShiftMember:
        """res.partner record"""
        return cls(
            partner_id = record.id,
            parent_partner_id = record.parent_id,
            name = record.name,
            barcode = record.barcode_base,
            gender = record.gender or None
        )

    def add_associated_members(self, *members: ShiftMember) -> None:
        if self.associated_members is None:
            self.associated_members = list(members)
        else:
            self.associated_members.extend(list(members))
    
    def into_html(self) -> str:
        return f"""
            <li id="{self.registration_id}" registration_id="{self.registration_id}" class="{self.state}" 
            shift_id="{self.shift_id}" partner_id="{self.partner_id}" state="{self.state}" 
            onclick="askConfirmationReset({self.registration_id})">{self.display_name}</li>  
        """
  
    



@define(repr=False)
class Shift(object):
    shift_id: int = field(validator=[validators.instance_of(int)])
    shift_type_id: int = field(validator=[validators.instance_of(int)])
    shift_tmpl_id: int = field(validator=[validators.instance_of(int)])
    standard_ticket_id: int = field(validator=[validators.instance_of(int)])
    ftop_ticket_id: int = field(validator=[validators.instance_of(int)])
    name: str =  field(validator=[validators.instance_of(str)])
    week_name: str =  field(validator=[validators.instance_of(str)])
    begin: datetime = field(validator=[validators.instance_of(datetime)])
    end: datetime = field(validator=[validators.instance_of(datetime)])
    state: str = field(validator=[validators.instance_of(str)])
    members: dict[int, ShiftMember] = field(validator=[validators.instance_of(dict)])
    
    @property
    def day(self) -> str:
        return translate_day(self.name)

    @property
    def shift_display_name(self) -> str:
        begin = self.begin.strftime("%Hh%M")
        end = self.end.strftime("%Hh%M")
        return f"{self.day} {begin} - {end}"
    
    @property
    def payload(self) -> dict[str, Any]:
        return {
            "shift_id": self.shift_id,
            "shift_display_name": self.shift_display_name,
            "members": [member.payload for member in self.get_active_members()]
        }
    
    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}: {self.shift_id} {self.name} {self.state}>"
    
    @classmethod
    def from_record(cls, shift_record: Record, ticket_record: Record) -> Shift:
        """Initialize Shift from `shift.shift` and `shift.ticket` records"""
        tickets = {str(t.shift_type): t.id for t in ticket_record}
        return cls(
            shift_record.id,
            shift_record.shift_type_id.id,
            shift_record.shift_template_id.id,
            tickets.get("standard", None),
            tickets.get("ftop", None),
            shift_record.name,
            shift_record.week_name,
            datetime.fromisoformat(shift_record.date_begin_tz),
            datetime.fromisoformat(shift_record.date_end_tz),
            shift_record.state,
            {}
        )
    
    def add_shift_members(self, *members: ShiftMember) -> None:
        self.members.update({member.partner_id:member for member in members})
        
    def refresh_shift_members(self, *members: ShiftMember) -> None:
        self.members = {member.partner_id:member for member in members}
        
    def get_active_members(self) -> list[ShiftMember]:
        active_state = ["cancel", "waiting", "replaced"]
        return [member for member in self.members.values() if member.state not in active_state]