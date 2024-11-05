from __future__ import annotations

import time
import logging
from datetime import datetime, date, timedelta
from functools import wraps
from http.client import CannotSendRequest
from attrs import define, field, validators
from erppeek import Client, Record

from typing import Any

from accueil.models.shift import Shift, Cycle, ShiftMember
from accueil.utils import get_appropriate_shift_type

logger = logging.getLogger("odoo")

@define(repr=False)
class Odoo(object):
    __login: str = field(validator=[validators.instance_of(str)]) # type: ignore
    __password: str = field(validator=[validators.instance_of(str)]) # type: ignore
    _db_name: str = field(validator=[validators.instance_of(str)])
    _url: str = field(validator=[validators.instance_of(str)])
    verbose: bool = field(default=False)
    client: Client | None = field(default=None, init=False)

    @classmethod
    def initialize(cls, login: str, password: str, db_name: str, url: str, verbose: bool= False) -> Odoo:
        odoo = cls(
            login,
            password,
            db_name,
            url,
            verbose
        )
        odoo.connect()
        return odoo

    def connect(self, max_retries: int=5) -> None:
        if not all([self.__login, self.__password, self._url, self._db_name]):
            raise ValueError("Odoo client badly initialized")

        _conn, _tries = False, 0
        while (_conn is False and _tries <= max_retries):
            try:
                self.client = Client(self._url, verbose=self.verbose)
                log = self.client.login(self.__login, password=self.__password, database=self._db_name)
                user = self.client.ResUsers.browse(log) # type: ignore
                tz = user.tz
                _conn = True
            except Exception as e:
                time.sleep(5)
                _tries += 1

        if _conn is False:
            raise ConnectionError("cannot connect to Odoo.")

    def _refresher(f): # type: ignore
        @wraps(f) # type: ignore
        def wrapper(*args, **kwargs):
            self = args[0]
            _ok, _tries, _max_tries = False, 0, 3
            while _tries <= _max_tries and _ok is False:
                try:
                    res = f(*args, **kwargs) # type: ignore
                    _ok = True
                except (CannotSendRequest, AssertionError):
                    _tries += 1
                    self.connect()
            if _ok is False:
                raise ConnectionError("cannot connect to odoo")
            return res # type: ignore
        return wrapper

    @_refresher # type: ignore
    def get(self, model: str, conds: list[tuple[str, str, Any]]):
        result = self.client.model(model).get(conds) # type: ignore
        return result

    @_refresher # type: ignore
    def browse(self, model: str, conds: list[tuple[str, str, Any]],  limit=None):
        result = self.client.model(model).browse(conds,  limit) # type: ignore
        return result

    @_refresher # type: ignore
    def create(self, model: str, object: dict[str, Any]):
        result = self.client.model(model).create(object) # type: ignore
        return result

    # --

    def build_shifts(self, cycles: list[Cycle], ftop: bool = False) -> list[Shift]:
        """build shifts, shiftMembers and add members to shifts"""
        shifts = self.get_today_shifts(ftop=ftop)
        for shift in shifts:
            if ftop is False:
                # not interacting with ftop members. only use of ftop shift is for closing.
                # Unsure if for closing ftop shift, setting members state necessary or not ?
                # keep cond unless, needed to act on ftop and that ftop needs members to be collected.
                logger.info(f"COLLECTING {shift} ...")
                members = self.get_shift_members(shift.shift_id, cycles)
                shift.add_shift_members(*members)
        return shifts

    def get_today_shifts(self, ftop: bool = False) -> list[Shift]:
        floor = datetime.combine(date.today(), datetime.min.time())
        ceiling = datetime.combine(date.today(), datetime.max.time())
        shift_type = 1 if ftop is False else 2

        today_shifts = self.browse(
            "shift.shift",
            [
                ("date_begin_tz", ">=", floor.isoformat()),
                ("date_begin_tz", "<=", ceiling.isoformat()),
                ("shift_type_id.id", "=", shift_type)
            ]
        )
        shifts = []
        for shift_record in today_shifts: # type: ignore
            ticket_record = self.browse("shift.ticket",[("shift_id", "=", shift_record.id)])
            shift = Shift.from_record(shift_record, ticket_record) # type: ignore
            shifts.append(shift)
        return shifts

    def get_cycles(self) -> list[Cycle]:
        """names: "Service volants - DSam. - 21:00", "Service volants - BSam. - 21:00" """
        shift_records = self.browse(
            "shift.shift",
            [
                ("date_begin",">", datetime.now() - timedelta(hours=10)),
                ("date_begin","<=", datetime.now() + timedelta(days=28)),
                ("name", "in", ["Service volants - DSam. - 21:00", "Service volants - BSam. - 21:00"])
            ]
        )
        cycles = []
        for shift_record in shift_records: # type: ignore
            cycle = Cycle.from_record(shift_record)
            if cycle.is_current():
                cycles.append(cycle)
        return cycles

    def is_from_cycle(self, cycle: Cycle , member: Record) -> bool:
        return bool(self.get("shift.registration", [("shift_id", "=", cycle.shift_id), ("partner_id.id", "=", member.partner_id.id)]))

    def get_member_cycle(self, member: Record, cycles: list[Cycle]) -> Cycle | None:
        for cycle in cycles:
            if self.is_from_cycle(cycle, member):
                return cycle
        return None

    def build_member(self, registration_record: Record, cycles: list[Cycle]) -> ShiftMember:
        cycle = self.get_member_cycle(registration_record, cycles)
        member = ShiftMember.from_record(registration_record, cycle)
        if member.has_associated_members:
            associated_members = self.get_associated_members(member.partner_id)
            member.add_associated_members(*associated_members)
        return member

    def get_shift_members(self, shift_id: int, cycles: list[Cycle]) -> list[ShiftMember]:
        shift_members = self.browse("shift.registration", [("shift_id", "=", shift_id)])
        members = [self.build_member(shift_member, cycles) for shift_member in shift_members] # type: ignore
        return members

    def get_associated_members(self, parent_id: int) -> list[ShiftMember]:
        associated_records = self.browse("res.partner", [("parent_id", "=", parent_id)])
        associated_members = []
        for associated_record in associated_records: # type: ignore
            associated_member = ShiftMember.associated_member_from_record(associated_record)
            associated_members.append(associated_member)
        return associated_members

    def get_member_record(self, partner_id: int) -> Record:
        return self.get("res.partner", [("id", "=", partner_id)]) # type: ignore

    def get_members_from_barcodebase(self, barcode_base: int):
        """limit to the 25 first elements"""
        members = self.browse("res.partner", [("barcode_base","=", barcode_base), ("cooperative_state", "not in", ["unsubscribed"])])
        payload = [{"partner_id": m.id, "name": m.name, "barcode_base": m.barcode_base} for m in members[:25]] # type: ignore
        return payload

    def get_members_from_name(self, name: str):
        """limit to the 25 first elements"""
        members = self.browse("res.partner",[("name","ilike", name),("cooperative_state", "not in", ["unsubscribed"])])
        payload = [{"partner_id": m.id, "name": m.name, "barcode_base": m.barcode_base} for m in members[:25]] # type: ignore
        return payload

    # --

    def set_attendancy(self, member: ShiftMember) -> None:
        service: Record = self.get("shift.registration", [("id", "=", member.registration_id)]) # type: ignore
        service.state = "done"
        member.state = "done"

    def reset_attendancy(self, member: ShiftMember) -> None:
        service: Record = self.get("shift.registration", [("id", "=", member.registration_id)]) # type: ignore
        service.state = "open"
        member.state = "open"

    def registrate_attendancy(self, partner_id: int, shift: Shift) -> Record:
        member_record = self.get_member_record(partner_id)
        if member_record.is_associated_people:
            member_record = self.get_member_record(member_record.parent_id.id) # type: ignore

        shift_type: str = member_record.shift_type # type: ignore
        if shift_type == "standard":
            std_points: int = int(member_record.final_standard_point) # type: ignore
            shift_type = get_appropriate_shift_type(shift_type, std_points)
        shift_ticket_id = getattr(shift, f"{shift_type}_ticket_id")

        service = self.create("shift.registration", {
            "partner_id": member_record.id,
            "shift_id": shift.shift_id,
            "shift_type": shift_type,
            "shift_ticket_id": shift_ticket_id,
            "related_shift_state": 'confirm',
            "state": 'open'
            }
        )
        service.state = "done"
        return service

    def set_regular_shift_absences(self, shift: Shift) -> list[ShiftMember]:
        absent_members = [member for member in shift.members.values() if (member.coop_state != "exempted" and member.state in ["open", "draft"])]
        [setattr(member, "state", "absent")  for member in absent_members]
        self.client.write("shift.registration", [s.registration_id for s in absent_members], {"state": "absent"}) # type: ignore
        return absent_members

    def set_regular_shifts_absences(self, shifts: list[Shift]) -> list[list[ShiftMember]]:
        return [self.set_regular_shift_absences(shift) for shift in shifts]

    def close_shifts(self, shifts: list[Shift]) -> None:
        [self.close_shift(shift) for shift in shifts]

    def close_shift(self, shift: Shift) -> None:
        record = self.get("shift.shift", [("id", "=", shift.shift_id)])
        try:
            record.button_done() # type: ignore
        except Exception as e:
            # marshall none
            print(e)
            pass
