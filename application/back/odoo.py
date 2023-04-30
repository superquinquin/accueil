"""
IMPL ODOO STRUCT
TROUGHT ERPPEEK
"""

import time
import erppeek
from datetime import datetime, timedelta, date
from typing import List, Tuple

from application.back.shift import Shift
from application.back.member import Member
from application.back.utils import translate_day

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


    def get(self, model: str, cond:List[Tuple[str]]) -> erppeek.Record:
        """short for odoo client get method"""
        return self.client.model(model).get(cond)
    
    def browse(self, model:str, cond:List[Tuple[str]]) -> erppeek.RecordList:
        """short for odoo client browse method"""
        return self.client.model(model).browse(cond)
    
    def create(self, model:str, object:dict) -> erppeek.Record:
        """short for odoo client create method"""
        return self.client.model(model).create(object)
    


    ###### IMPL FETCH SHIFTS ##############
    def fetch_today_shifts(self, cache: dict) -> dict:
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
        
        shifts = self.browse("shift.shift",
                         [("date_begin_tz", ">=", dt_floor.isoformat()),
                          ("date_begin_tz", "<=", dt_ceiling.isoformat())]
                )
        
        for shift in shifts:
            print(f"{shift.id} - {shift.name} : {shift.date_begin_tz} - {shift.date_end_tz}")
            
            shift_id = shift.id
            begin = datetime.fromisoformat(shift.date_begin_tz).strftime("%Hh%M")
            end = datetime.fromisoformat(shift.date_end_tz).strftime("%Hh%M")
            s = Shift(shift_id,
                    shift.shift_type_id.id,
                    shift.shift_template_id.id,
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
    
    def fetch_shifts_assigned_members(self, cache:dict) -> dict:
        """MEMBER STRUCT CONSTRUCTOR
        FETCH ASSIGNED MEMBERS TO ASSOCIATED SHIFTS
        COLLECT THEM INTO RELATED SHIFT.MEMBERS FIELD

        Args:
            cache (dict): cache dictionnary

        Returns:
            dict: updated cache
        """
        members = self.browse("shift.registration", 
                             [("shift_id", "in", list(cache["shifts"].keys())),
                              ("state", "not in", ["cancel", "waiting", "draft"])]
                )
        
        for m in members:
            member_id = m.partner_id.id
            shift_id = m.shift_id.id
            registration_id = m.id
            has_associated_member = m.partner_id.nb_associated_people
            is_associated_member = m.partner_id.is_associated_people
            print(f"{member_id} - {shift_id} - {m.name} - {has_associated_member}")

            if has_associated_member > 0:
                has_associated_member, assoc = self.fetch_associated_member(m.partner_id.id)
            else:
                assoc = None
            
            member = Member(member_id,
                            shift_id,
                            registration_id,
                            None,
                            m.name,
                            has_associated_member,
                            is_associated_member,
                            m.shift_type,
                            m.exchange_state,
                            m.state,
                            assoc)
            
            member.generate_display_name()
            cache["shifts"][shift_id].members[member_id] = member
            
        return cache
    
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
            m = self.get("res.partner", 
                            [("parent_id", "=", is_parent_id)]
                )
        except ValueError:
            """IF MULTIPLE ASSOCIATED SELECT FIRST ONE"""
            m = self.browse("res.partner", 
                                        [("parent_id", "=", is_parent_id)]
                            )[0]
        
        if m:
            has_associate = True
            member = Member(m.id,
                            None,
                            None,
                            is_parent_id,
                            m.name,
                            False,
                            True,
                            None,
                            None,
                            None,
                            None)
            
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
        service = self.get("shift.registration", 
                           [("id", "=", registration_id)]
                )
        service.state = "done"
        
        
        
    
    def post_absence(self) -> None:
        """
        TIMED THREAD LAUCHED BY SCHEDULER STRUCT RUNNER
        UPDATING SHIFT.REGISTRATION STATUS
        OF MEMBERS THAT HAVE NOT BEEN PRESENT DURING TODAY SHIFT
        SELECT ALL OPEN REGISTRATION FROM LAST 24H, UNLESS MEMBER IS EXEMPTED
        APPLY "ABSENT" STATUS TO THEM
        
        OPTIONAL: CLOSING SHIFT ?
        """
        print('updating absence status')
        now = datetime.now()
        floor = now - timedelta(hours=24)
        
        services = self.browse("shift.registration",
                               [("date_begin",">=", floor.isoformat()),
                                ("date_begin","<=", now.isoformat()),
                                ("state","=", "open")]
                    )
        ids = [s.id for s in services if self.is_not_exempted(s.partner_id.id)]
        self.client.write("shift.registration",ids, {"state": "absent"})
        
        ## ???? api.execute('res.partner','run_process_target_status', []) ????
        ## AUTO SHIFTS VALIDATION "EXECUTE BUTON_DONE"
    
    
    
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