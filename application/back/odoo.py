"""
IMPL ODOO STRUCT
TROUGHT ERPPEEK
"""

import time
import erppeek
import re
from erppeek import Record, RecordList
from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta
from dateutil.parser import parser
from typing import List, Tuple, Dict, Any, Union, Optional

from application.back.shift import Shift
from application.back.member import Member
from application.back.mail import Mail
from application.back.utils import translate_day, reject_particular_shift, NORMAL_SHIFTS_PATTERN

class Odoo:
    """ODOO INSTANCE
    communicate with odoo database

    STATUS
    @connected (bool): wether the instance is connected to odoo database
                        when False, try to reconnect every 60s

    ERPPEEK API ATTR
    @client: odoo erppeek client instance
    @log: erppeek log
    @tz: erppeek tz
    @user: erppeek user.
    """
  
  
    def __init__(self) -> None:
        #STATUS
        self.builded = False
        self.connected = False

        #CONN
        self.client = None
        self.log = None
        self.tz = None
        self.user = None


    def connect(self, url: str, login: str, password: str, db: str, verbose: bool):
        while self.connected == False:
            try:
                self.client = erppeek.Client(url, verbose=verbose)
                self.log = self.client.login(login, password=password, database=db)
                self.user = self.client.ResUsers.browse(self.log)
                self.tz = self.user.tz

                self.connected = True
            except Exception as e:
                print(e) #log latter
                time.sleep(60)


    def get(self, model: str, cond:List[Tuple[str]]) -> Record:
        """short for odoo client get method"""
        return self.client.model(model).get(cond)
    
    def browse(self, model:str, cond:List[Tuple[str]]) -> RecordList:
        """short for odoo client browse method"""
        return self.client.model(model).browse(cond)
    
    def create(self, model:str, object:Dict[str, Any]) -> Record:
        """short for odoo client create method"""
        return self.client.model(model).create(object)
    

    def fetch_members_from_barcode(self, barcode_base: str):
        m = self.browse(
            "res.partner", 
            [
                ("barcode_base","=", barcode_base), 
                ("cooperative_state", "not in", ["unsubscribed"]),
            ]
        )
        if not m:
            return ([], 0)
        
        members = [tuple((mb.id, mb.barcode_base, mb.name)) for mb in m] 
        l = len(members)
        
        return (members, l)
    
    def fetch_members_from_name(self, name:str):
        m = self.browse(
            "res.partner",
            [
                ("name","ilike", name),
                ("cooperative_state", "not in", ["unsubscribed"]),
            ]
        )
        if not m:
            return ([], 0)
        members = [tuple((mb.id, mb.barcode_base, mb.name)) for mb in m] 
        l = len(members)
        return (members, l)
    
    
    ###### IMPL FETCH SHIFTS ##############
    def fetch_today_shifts(self, cache: Dict[str, Any]) -> Dict[str, Any]:
        """SHIFTS STRUCT CONSTRUCTOR
        FETCH TODAY SHIFTS TRHOUGH ERPPEEK API
        COLLECT INTO "SHIFTS" CACHE

        Args:
            cache (dict): app cache

        Returns:
            (dict): cache with updated shifts
        """
        
        dt_floor= datetime.today().replace(hour=0, 
                                          minute=0, 
                                          second=0, 
                                          microsecond=0)
        dt_ceiling = datetime.today().replace(hour=23, 
                                          minute=59, 
                                          second=59, 
                                          microsecond=59)

        shifts = self.browse(
            "shift.shift",
            [
                ("date_begin_tz", ">=", dt_floor.isoformat()),
                ("date_begin_tz", "<=", dt_ceiling.isoformat()),
                ("shift_type_id.id", "=", 1)
            ]
        )
   
        for shift in shifts:
            print(f"{shift.id} - {shift.name} : {shift.date_begin_tz} - {shift.date_end_tz}")

            shift_id = shift.id
            begin = datetime.fromisoformat(shift.date_begin_tz).strftime("%Hh%M")
            end = datetime.fromisoformat(shift.date_end_tz).strftime("%Hh%M")
            tickets = self.browse(
                "shift.ticket",
                [("shift_id", "=", shift_id)]
            )

            s = Shift(
                shift_id,
                shift.shift_type_id.id,
                shift.shift_template_id.id,
                {str(t.shift_type): t.id for t in tickets},
                translate_day(shift.name),
                shift.week_name,
                begin,
                end,
                shift.state
            )
            s.correct_auto_singleton_transform()
            cache['shifts'][shift_id] = s

        return cache
    
    #### IMPL FETCH MEMBERS ####

    def populate_shifts_with_members(self, cache: Dict[str, Any]) -> Dict[str, Any]:
        """MEMBER STRUCT CONSTRUCTOR
        FETCH ASSIGNED MEMBERS TO ASSOCIATED SHIFTS
        COLLECT THEM INTO RELATED SHIFT.MEMBERS FIELD

        Args:
            cache (dict): cache dictionnary

        Returns:
            dict: updated cache
        """
        for sid in cache["shifts"].keys():
            cache = self.fetch_shift_members(sid, cache)
        return cache


    def fetch_shift_members(self, sid: int, cache: Dict[str, Any]) -> Dict[str, Any]:
        cycles = {
            "abcd": self.fetch_cycle("Service volants - DSam. - 21:00", "ABCD"), 
            "cdab": self.fetch_cycle("Service volants - BSam. - 21:00", "CDAB")
        }

        members = self.browse(
            "shift.registration",
            [
                ("shift_id", "=", sid),
                ("state", "not in", ["cancel", "waiting", "replaced"])
            ]
        )

        for m in members:
            member_id = m.partner_id.id
            member = self.create_main_member(m, cycles)
            cache["shifts"][sid].members[member_id] = member
            
        return cache
    
    def fetch_cycle(self, shift_name: str, cycle_name: str):
        """
        names:
        "Service volants - DSam. - 21:00"
        "Service volants - BSam. - 21:00"
        """
        begin_start = datetime.now() - relativedelta(hours=10)
        begin_end = datetime.now() + relativedelta(days=28)
        cycle = self.browse(
            "shift.shift", 
            [
                ("date_begin",">", begin_start), 
                ("date_begin","<=", begin_end), 
                ("name", "=", shift_name)
            ]
        )
        
        if len(cycle) > 1:
            # must handle that ... but might not happen actually
            cycle = cycle[0]
        elif len(cycle) == 1:
            cycle = cycle[0]
        else:
            return (None, None, None, None)
        end_date_dt = parser().parse(timestr=cycle.date_begin)
        delta = (datetime.now() - (end_date_dt + relativedelta(days=-28))).total_seconds()
        cycle_start_date = (datetime.now() + relativedelta(seconds=-delta, days=2)).strftime("%d/%m/%Y")
        cycle_end_date = end_date_dt.strftime("%d/%m/%Y")
        return (cycle_name, cycle_start_date, cycle_end_date, cycle.id)

    def is_from_cycle(self, cycle_id:int, member_id: int) -> bool:
        return bool(self.get("shift.registration", [("shift_id", "=", cycle_id), ("partner_id.id", "=", member_id)]))
        
    def create_main_member(self, m: Record, cycles: Dict[str, Any]):
            member_id = m.partner_id.id
            leader = m.partner_id.is_squadleader
            shift_id = m.shift_id.id
            registration_id = m.id
            has_associated_member = m.partner_id.nb_associated_people
            is_associated_member = m.partner_id.is_associated_people
            dt = parser().parse(m.date_begin)
            date = dt.strftime("%d/%m/%Y")
            start_hours = (dt + relativedelta(hours=2)).strftime("%HH%M")
            end_hours = (dt + relativedelta(hours=4, minutes=45)).strftime("%HH%M")
            print(f"{member_id} - {shift_id} - {m.name} - {has_associated_member}")
            
            cycle_type, start_cycle, end_cyle = "standard", None, None
            for (name, start_date, end_date, sid) in cycles.values():
                if sid and member_id and self.is_from_cycle(sid, member_id):
                    cycle_type = name
                    start_cycle = start_date
                    end_cyle = end_date
                    break
                
            if has_associated_member > 0:
                has_associated_member, assoc = self.fetch_associated_member(m.partner_id.id)
            else:
                assoc = None
            member = Member(
                id=member_id,
                shift_id=shift_id,
                registration_id=registration_id,
                name=m.name,
                leader=leader,
                date=date,
                start_hours=start_hours,
                end_hours=end_hours,
                barcode=m.partner_id.barcode_base,
                has_associated_member=has_associated_member,
                is_associated_member=is_associated_member,
                shift_type=m.shift_type,
                exchange_state=m.exchange_state,
                state=m.state,
                member=assoc,
                cycle_type=cycle_type,
                start_cycle=start_cycle,
                end_cycle=end_cyle,
                std_counter=int(m.partner_id.final_standard_point),
                ftop_counter=int(m.partner_id.final_ftop_point),
                gender=m.partner_id.gender or None,
                mail=m.partner_id.email or None
            )
            member.generate_display_name()
            return member
    
    
    def fetch_associated_member(self, is_parent_id: int) -> Member:
        """MEMBER STRUCT CONSTRUCTOR FOR ASSOCIATED MEMBERS
        FETCH MEMEBERS FROM RES.PARTNER MODEL USING PARENT (ASSOCIATED MEMBER) ID.
        COLLECT THEM INTO RELATED SHIFT.MEMBERS FIELD
        
        ASSOCIATED MEMBERS IS LIKELY TO BE LIMITED TO 1 
        (1 ASSOCIATED MEMBER FOR EACH MAIN MEMBER)
        HOWEVER I APPEAR THAT THIS LIMITATION IS NOT STRICT
        YOU CAN FIND MEMBERS WITH MORE THAN 1 ASSOCIATED
        ===> IN THIS REGARD, BROWSE ALL ASSOCIATED MEMBERS
            COLLECT FIRST ONE ONLY.

        Args:
            is_parent_id (int): Main associate partner_id.

        Returns:
            Member: Member struct with limited informations.
        """        
  
        try:
            """MEMBERS ARE SUPPOSED TO HAVE 1 ASSOCIATE MAX"""
            m = self.get(
                "res.partner", 
                [("parent_id", "=", is_parent_id)]
            )
        except ValueError:
            """IF MULTIPLE ASSOCIATED SELECT FIRST ONE"""
            m = self.browse(
                "res.partner", 
                [("parent_id", "=", is_parent_id)]
            )[0]
        
        if m:
            has_associate = True
            member = Member(
                id=m.id,
                parent_id=is_parent_id,
                name=m.name,
                barcode=m.barcode,
            )
            
        else:
            member = None
            has_associate = False
        
        return (has_associate, member)

    
    
    ###### POST METHOD ########
    
    def post_presence(self, registration_id: int) -> None:
        """ON CLIENT PRESENCE CONFIRMATION
        CALL ON SHIFT.REGISTRATION MODEL
        SET SHIFT.REGISTRATION ROW STATUS TO "done"

        Args:
            registration_id (int): shift.registration Id key
        """
        service = self.get(
            "shift.registration", 
            [("id", "=", registration_id)]
        )
        service.state = "done"
        
        
    def post_to_open(self, registration_id: int) -> None:
        """ON CLIENT reseting presence CONFIRMATION
        CALL ON SHIFT.REGISTRATION MODEL
        SET SHIFT.REGISTRATION ROW STATUS TO "open"

        Args:
            registration_id (int): shift.registration Id key
        """
        service = self.get(
            "shift.registration", 
            [("id", "=", registration_id)]
        )
        service.state = "open"
    
    
    def get_ftop_shift(self) -> Optional[Record]:
        now = datetime.now() + timedelta(hours=8)
        floor = now - timedelta(hours=24)
        shift = self.browse(
            "shift.shift",
            [
                ("date_begin_tz", ">=", floor.isoformat()),
                ("date_begin_tz", "<=", now.isoformat()),
                ("shift_type_id.id", '=', 2)
            ]
        )
        if shift:
            shift = shift[0]
        return shift or None
    
    def handle_ftop_shift_enclosure(self, cache: Dict[str, Any]) -> None:
        config = cache["config"]
        shift = self.get_ftop_shift()
        if shift and config.AUTO_CLOSE_FTOP_SHIFT:
            self._close_shift(shift)
    
    def post_absence(self, services: RecordList, cache: Dict[str, Any]) -> None:
        """
        TIMED THREAD LAUCHED BY SCHEDULER STRUCT RUNNER
        UPDATING SHIFT.REGISTRATION STATUS
        OF MEMBERS THAT HAVE NOT BEEN PRESENT DURING TODAY SHIFT
        SELECT ALL OPEN REGISTRATION FROM LAST 24H, UNLESS MEMBER IS EXEMPTED
        APPLY "ABSENT" STATUS TO THEM
        """
        print('updating absence status')
        non_exempted = [s for s in services if self.is_not_exempted(s.partner_id.id)]
        self.client.write(
            "shift.registration", 
            [s.id for s in non_exempted], 
            {"state": "absent"}
        )
        
        config = cache["config"]
        if config.AUTO_ABS_MAIL:
            cycles = {
                "abcd": self.fetch_cycle("Service volants - DSam. - 21:00", "ABCD"), 
                "cdab": self.fetch_cycle("Service volants - BSam. - 21:00", "CDAB")
            }
            for rid in non_exempted:
                member = self.create_main_member(rid, cycles)
                if member.mail:
                    Mail(
                        config.EMAIL_LOGIN, 
                        config.EMAIL_PASSWORD,
                        config.SMTP_PORT,
                        config.SMTP_SERVER,
                        config.EMAIL_BDM,
                        [member.mail] 
                    ).send_abs_mail(member)             

    
    
    def _close_shift(self, shift: Record) -> None:
        """close shift record"""
        print('closing shift: ', f"{shift.id} - {shift.name}")
        
        try:
            shift.button_done()
        except Exception as e:
            # marshall none 
            print(e)
            pass
    
    
    def closing_shifts_routine(self, cache: Dict[str, Any]) -> None:
        """
        details:
            select all shift registration of last h24
            select all shift of last h24
            
            start closing routine:
            - set open shift/waiting shift registration state to absent
            - close shift records
        """
        config = cache["config"]
        now = datetime.now()
        floor = now - timedelta(hours=24)
  
        shifts = self.browse(
            "shift.shift",
            [
                ("date_begin_tz", ">=", floor.isoformat()),
                ("date_begin_tz", "<=", now.isoformat()),
                ("shift_type_id.id", '=', 1)
            ]
        )
        
        services = self.browse(
            "shift.registration",
            [
                ("date_begin",">=", floor.isoformat()),
                ("date_begin","<=", now.isoformat()),
                ("state","in", ["open", "draft"]),
                ("shift_id.id", 'in', [shift.id for shift in shifts])
            ]
        )        
                
        if config.AUTO_ABS_NOTATION:
            self.post_absence(services, cache)
        if config.AUTO_CLOSE_SHIFT:
            [self._close_shift(shift) for shift in shifts]
    
    
    
    def is_not_exempted(self, partner_id: int) -> bool:
        """TEST COOPERATIVE STATUS OF MEMBER BEFORE APPLYING ABSENCE STATUS.
        QUERY res.partner model

        Args:
            partner_id (int): model member Id key

        Returns:
            bool: False if member is exempted
        """
        exemption = True
        coop_state = self.get("res.partner", [("id", "=", partner_id)]).cooperative_state
        
        if coop_state == "exempted":
            exemption = False
        return exemption
    
    

    def register_member_to_shift(
        self, 
        shift_id: int, 
        partner_id: int, 
        shift_ticket_id: int, 
        stype: str
        ) -> Record:
        
        """
        ADD shift registration record
        Set record state to done
        """

        service = self.create(
            "shift.registration",
            {
            "partner_id": partner_id,
            "shift_id": shift_id,
            "shift_type": stype,
            "shift_ticket_id": shift_ticket_id,
            "related_shift_state": 'confirm',
            "state": 'open'
            }
        )
        
        service.state = "done"
        return service

    
    
    
    
    
    
    
    
    # def get_special_shift(self, name: str, cache: Dict[str, Any]) -> RecordList:
    #     now = datetime.now() + timedelta(hours=8)
    #     floor = now - timedelta(hours=24)
        
    #     shift = self.browse(
    #         "shift.shift",
    #         [
    #             ("date_begin_tz", ">=", floor.isoformat()),
    #             ("date_begin_tz", "<=", now.isoformat()),
    #             ("name", 'like', name)
    #         ]
    #     )
    #     if bool(shift):
    #         shift = shift[0]
    #         services = self.browse(
    #             "shift.registration",
    #             [
    #                 ("shift_id", "=", shift.id), 
    #                 ("state","in", ["open", "draft"])
    #             ]
    #         )
    #         return (shift, services)
    #     else:
    #         return (None, None)
    
    # def set_ftop_presence(self, services: RecordList, cache: Dict[str, Any]) -> None:
    #     config = cache["config"]
    #     now = datetime.now()
    #     floor = now - timedelta(days=27)
    #     abs = []
    #     all_shift_from_cycle = self.browse(
    #         "shift.shift",
    #         [
    #             ("date_begin_tz", ">=", floor.isoformat()),
    #             ("date_begin_tz", "<=", now.isoformat()),
    #         ]
    #     ).id

    #     for service in services:
    #         done = self.browse(
    #             "shift.registration",
    #             [
    #                 ("shift_id", "in", all_shift_from_cycle),
    #                 ("partner_id", "=", service.partner_id.id),
    #                 ("state", "=", "done")
    #             ]
    #         )
    #         if bool(done):
    #             service.state = "done"
    #         elif bool(done) is False and config.AUTO_ABS_NOTATION:
    #             abs.append(service)
    #             service.state = "absent"
        
    #     if config.AUTO_ABS_MAIL:
    #         cycles = {
    #             "abcd": self.fetch_cycle("Service volants - DSam. - 21:00", "ABCD"), 
    #             "cdab": self.fetch_cycle("Service volants - BSam. - 21:00", "CDAB")
    #         }
    #         for rid in abs:
    #             member = self.create_main_member(rid, cycles)
    #             if member.mail:
    #                 Mail(
    #                     config.EMAIL_LOGIN, 
    #                     config.EMAIL_PASSWORD,
    #                     config.SMTP_PORT,
    #                     config.SMTP_SERVER,
    #                     config.EMAIL_BDM,
    #                     [member.mail]
    #                 ).send_abs_mail(member, True)      
        
    # def handle_special_shift_closure(self, name: str, cache: Dict[str, Any]) -> None:
    #     config = cache["config"]
    #     (shift, services) = self.get_special_shift(name, cache)
    #     if services:
    #         self.set_ftop_presence(services, cache)
    #         if config.AUTO_CLOSE_SHIFT:
    #             self._close_shift(shift)
        