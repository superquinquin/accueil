from __future__ import annotations

import os
import time
import logging
import traceback
from contextlib import ContextDecorator
from xmlrpc.client import Fault
from datetime import datetime, timedelta
from functools import wraps
from http.client import CannotSendRequest
from odooly import Client, Record, RecordList, Model
from urllib.parse import urlsplit, urlunsplit, quote

from typing import Any, Callable

from accueil.models.shift import Shift, Cycle, ShiftMember
from accueil.exceptions import OdooError
from accueil.utils import get_appropriate_shift_type

logger = logging.getLogger("odoo")

Conditions = list[tuple[str, str, Any]]

def _jsonable(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, (list, tuple)):
        return type(value)(_jsonable(v) for v in value)
    return value

def normalize_conditions(conditions: Conditions) -> Conditions:
    return [_jsonable(clause) for clause in conditions]

def resilient(degree: int = 3):
    def decorator(f: Callable):
        @wraps(f)
        def wrapper(*args, **kwargs):
            self: OdooSession = args[0]
            success, tries = False, 0
            while success is False and tries <= degree:
                try:
                    res = f(*args, **kwargs)
                    success = True
                    return res
                except (CannotSendRequest, AssertionError):
                    tries += 1
                    self.renew_session()
            raise ConnectionError("Cannot establish connection with odoo.")
        return wrapper
    return decorator



class OdooConnector(object):
    def __init__(self, host: str, database: str, verbose: bool = False, **kwargs) -> None:
        self.host = host
        self.database = database
        self.verbose = verbose

    @property
    def url(self) -> str:
        user = os.environ.get("ERP_BASIC_USER", None)
        password = os.environ.get("ERP_BASIC_PASSWORD", None)
        if not all([user, password]):
            return self.host
        split = urlsplit(self.host)
        host = split.netloc.rsplit("@", 1)[-1]
        userinfo = f"{quote(str(user), safe='')}:{quote(str(password), safe='')}"
        return urlunsplit((split.scheme, f"{userinfo}@{host}", split.path, split.query, split.fragment))

    @staticmethod
    def credentials() -> tuple[str, str | None, str | None]:
        username = os.environ.get("ERP_USERNAME", None)
        password = os.environ.get("ERP_PASSWORD", None)
        api_key = os.environ.get("ERP_API_KEY", None)
        if username is None or not any([password, api_key]):
            raise ValueError(
                "ERP_USERNAME and one of ERP_PASSWORD / ERP_API_KEY must be set"
            )
        return (username, api_key or password, api_key)

    @classmethod
    def from_env(cls) -> OdooConnector:
        host = os.environ.get("ERP_URL", None)
        database = os.environ.get("ERP_DB", None)
        if host is None or database is None:
            raise ValueError("Missing ERP host or database")
        return cls(host, database)

    def make_session(self, max_retries: int = 5, retries_interval: int = 5) -> OdooSession:
        username, password, api_key = self.credentials()
        
        success, tries, last_error = False, 0, None
        while (success is False and tries <= max_retries):
            try:
                client = Client(
                    self.url, 
                    self.database, 
                    username, 
                    password,
                    api_key=api_key, 
                    verbose=self.verbose,
                )
                success = True
                return OdooSession(client, self)
            
            except Exception as exc:
                last_error = exc
                time.sleep(retries_interval)
                tries += 1

        raise ConnectionError(
            f"Unable to generate an Odoo Session: {type(last_error).__name__}: {last_error}"
        ) from last_error


class OdooSession(ContextDecorator):
    client: Client
    connector: OdooConnector

    def __init__(self, client: Client, connector: OdooConnector) -> None:
        self.client = client
        self.connector = connector

    def __enter__(self) -> OdooSession:
        return self

    def __exit__(self, exc_type, exc, exc_tb) -> None:
        del self

    def renew_session(self) -> None:
        username, password, api_key = self.connector.credentials()
        client = Client(
            self.connector.url, self.client.env.db_name, username, password,
            api_key=api_key, verbose=False,
        )
        self.client = client

    def model(self, name: str) -> Model:
        return self.client.env[name]

    @resilient(degree=3)
    def get(self, model: str, conditions: Conditions) -> Record | None:
        return self.model(model).get(normalize_conditions(conditions))

    @resilient(degree=3)
    def browse(self, model: str, ids: list[int]) -> Record | RecordList:
        return self.model(model).browse(ids)

    @resilient(degree=3)
    def search(self, model: str, conditions: Conditions) -> RecordList:
        return self.model(model).search(normalize_conditions(conditions))

    @resilient(degree=3)
    def create(self, model: str, values: dict[str, Any]):
        return self.model(model).create(values)

    def today_shifts(self, ftop: bool = False, cycles: list[Cycle] | None = None) -> tuple[list[Shift], list[Cycle]]:
        dt = datetime.now()
        shifts, cycles = self.build_shifts(dt, ftop, cycles)
        return (shifts, cycles)

    def build_shifts(self, dt: datetime, ftop: bool = False, cycles: list[Cycle] | None = None) -> tuple[list[Shift], list[Cycle]]:
        if cycles is None:
            cycles = self.collect_cycles(dt)
        shifts = self.collect_shifts(dt, ftop)
        for shift in shifts:
            if ftop is False:
                # not interacting with ftop members. only use of ftop shift is for closing.
                # Unsure if for closing ftop shift, setting members state necessary or not ?
                # keep cond unless, needed to act on ftop and that ftop needs members to be collected.
                logger.info(f"COLLECTING {shift} ...")
                members = self.get_shift_members(shift.shift_id, cycles)
                shift.add_shift_members(*members)
        return (shifts, cycles)

    def collect_shifts(self, dt: datetime, ftop: bool = False) -> list[Shift]:
        floor = datetime.combine(dt, datetime.min.time())
        ceiling = datetime.combine(dt, datetime.max.time())
        shift_type = 1 if ftop is False else 2

        shifts_records = self.search(
            "shift.shift",
            [
                ("date_begin_tz", ">=", floor.isoformat()),
                ("date_begin_tz", "<=", ceiling.isoformat()),
                ("shift_type_id.id", "=", shift_type)
            ]
        )

        shifts = []
        for shift_record in shifts_records: 
            ticket_record = self.search("shift.ticket",[("shift_id", "=", shift_record.id)])
            shift = Shift.from_record(shift_record, ticket_record) 
            shifts.append(shift)
        return shifts

    def collect_cycles(self, dt: datetime) -> list[Cycle]:
        """names: "Service volants - DSam. - 21:00", "Service volants - BSam. - 21:00" """
        shift_records = self.search(
            "shift.shift",
            [
                ("date_begin",">", dt - timedelta(hours=10)),
                ("date_begin","<=", dt + timedelta(days=28)),
                ("name", "in", ["Service volants - DSam. - 21:00", "Service volants - BSam. - 21:00"])
            ]
        )
        cycles = []
        for shift_record in shift_records:
            cycle = Cycle.from_record(shift_record)
            if cycle.is_current():
                cycles.append(cycle)
        return cycles


    def is_from_cycle(self, cycle: Cycle , member: Record) -> bool:
        partner = member.partner_id
        if partner is None:
            raise OdooError(f"Partner record not found for member from shift.registration.id: {str(member.id)}")
        assert isinstance(partner, Record)

        reg = self.get("shift.registration", [("shift_id", "=", cycle.shift_id), ("partner_id.id", "=", partner.id)])
        return bool(reg)

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
        shift_members = self.search("shift.registration", [("shift_id", "=", shift_id)])
        members = [self.build_member(shift_member, cycles) for shift_member in shift_members] 
        return members

    def get_associated_members(self, parent_id: int) -> list[ShiftMember]:
        associated_records = self.search("res.partner", [("parent_id", "=", parent_id)])
        associated_members = []
        for associated_record in associated_records: 
            associated_member = ShiftMember.associated_member_from_record(associated_record)
            associated_members.append(associated_member)
        return associated_members

    def get_member_record(self, partner_id: int) -> Record:
        return self.get("res.partner", [("id", "=", partner_id)]) 

    def get_members_from_barcodebase(self, barcode_base: int):
        """limit to the 25 first elements"""
        members = self.search("res.partner", [("barcode_base","=", barcode_base), ("cooperative_state", "not in", ["unsubscribed"])])
        payload = [{"partner_id": m.id, "name": m.name, "barcode_base": m.barcode_base} for m in members[:25]] 
        return payload

    def get_members_from_name(self, name: str):
        """limit to the 25 first elements"""
        members = self.search("res.partner",[("name","ilike", name),("cooperative_state", "not in", ["unsubscribed"])])
        payload = [{"partner_id": m.id, "name": m.name, "barcode_base": m.barcode_base} for m in members[:25]] 
        return payload

    # --

    def set_attendancy(self, member: ShiftMember) -> None:
        service: Record = self.get("shift.registration", [("id", "=", member.registration_id)]) 
        service.state = "done"
        member.state = "done"

    def reset_attendancy(self, member: ShiftMember) -> None:
        service: Record = self.get("shift.registration", [("id", "=", member.registration_id)]) 
        service.state = "open"
        member.state = "open"

    def registrate_attendancy(self, partner_id: int, shift: Shift) -> Record:
        member_record = self.get_member_record(partner_id)

        if member_record.is_associated_people:
            parent = member_record.parent_id
            if parent is None:
                raise OdooError(f"Partner record not found for member from res.partner: {str(member_record.id)}")
            assert isinstance(parent, Record)
            
            parent_id = parent.id
            assert isinstance(parent_id, int)
            member_record = self.get_member_record(parent_id) 

        shift_type = member_record.shift_type 
        assert isinstance(shift_type, str)

        if shift_type == "standard":
            std = member_record.final_standard_point
            assert isinstance(std, str) and std.isnumeric()

            std_points = int(std)
            shift_type = get_appropriate_shift_type(shift_type, std_points)
        shift_ticket_id = getattr(shift, f"{shift_type}_ticket_id")

        service = self.create(
            "shift.registration", 
            {
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
        for member in absent_members:
            try:
                registration = self.get("shift.registration", [("id","=", member.registration_id)])
                registration.button_reg_absent() 
            except Exception as e:
                self._filter_xmlrpc_faults(e, raise_excpt=False)
        return absent_members

    def set_regular_shifts_absences(self, shifts: list[Shift]) -> list[list[ShiftMember]]:
        return [self.set_regular_shift_absences(shift) for shift in shifts]

    def close_shifts(self, shifts: list[Shift]) -> None:
        [self.close_shift(shift) for shift in shifts]

    def close_shift(self, shift: Shift) -> None:
        record = self.get("shift.shift", [("id", "=", shift.shift_id)])
        try:
            record.button_done() 
        except Exception as e:
            self._filter_xmlrpc_faults(e, raise_excpt=True)

    def _filter_xmlrpc_faults(self, excpt: Exception, raise_excpt: bool = False) -> None:
        """
        xmlrpc tend to act weirdly.
        Fault.faultCode should theorically be a int. However, this namespace is usually used to store error messages...
        Fault..faultString should theorically contain the error message. However, this namespace is usually used to store the xmlrpc trace of the exception...

        pass on marshall None exceptions
        raise on every other xmlrpc faults
        """
        trace = traceback.format_exc()

        if (
            isinstance(excpt, Fault) and
            isinstance(excpt.faultCode, str) and 
            excpt.faultCode.__contains__("cannot marshal None unless allow_none is enabled")
        ):
            # -- Bypass MARSHALL EXCEPTION
            logger.warning("Bypass Marshal None exception")
        elif raise_excpt is False:
            logger.error(excpt)
            logger.error(trace)
            return
        else:
            logger.error(excpt)
            logger.error(trace)
            raise excpt