"""
IMPL SCHEDULER
INTERNALISE CRON LIKE TASKS.
EASIER TO LOG AND OBS THREAD PROCESS
"""


from typing import List, Dict, Tuple, Callable, Any
from collections import deque
from datetime import datetime, timedelta
from threading import Timer
from copy import deepcopy

from application.back.odoo import Odoo
from application.back.shift import Shift
from application.back.utils import get_delay, get_delay_from_datetime


class Scheduler:
    """
    MANAGE TIMED THREAD TASKS
    MANAGE cache SHIFTS AND CURRENT_SHIFTS CONTENT
    
    MAIN PROCESS:
    +-------------------------------------+
    |               cache                 |
    | shifts (Dict[shift_id(int): Shift]) | <---------+
    | current_shifts (List[Shift])        |           |
    +-------------------------------------+           |
        ▲                                             |
        |                                             |
    (+)shifts                                (+ -)current_shifts  
    (+)current_shifts                                 |    
        |               (deque)                       |
    =>build_routine --> routine --> timed task ==> [rm, add]
        ▲                  ▲                          |
        |                  |                          |    
        +------------------+--------------------------+
        |
        |
        ▼
    Odoo.post_absence  
    Odoo.close_shifts    
    
                              
    @routine (deque) : DEQUE FILLED WITH TIMED TASKS
    TASKS SCHEMA:
        SHIFT_ID: TARGET cache["shifts"] ELEMENT
        DATETIME: EXCUTION TIMER 
        CALLBACK METHOD: self.add or self.rm 
        add or remove elements from cache["current_shifts"]
    """
    def __init__(self) -> None:
        self.routine: deque =  deque()

    def build_routine(self, cache: Dict[str, Any], from_runner: bool =True) -> None:
        """MAIN SCHEDULER METHOD
        COLLECT INTO cache TODAY SHIFTS INFORMATIONS AND ASSIGNED MEMBERS
        BUILD ROUTINE TASKS DEQUE AND RUN THREAD RUNNER CYCLE.
        
        IS USED TO BOTH INIT SCHEDULED PROCESS AND RESUME THREAD RUNNER EACH DAY.

        Args:
            cache (dict): cache dictionnary
            from_runner (bool, optional): Deactivate post absence method. Defaults to True.
        """
        
        config = cache['config']
        api = Odoo()
        api.connect(
            config.API_URL, 
            config.SERVICE_ACCOUNT_LOGGIN, 
            config.SERVICE_ACCOUNT_PASSWORD, 
            config.API_DB, 
            config.API_VERBOSE
        )
        if from_runner:
            api.closing_shifts_routine()
        
        cache["shifts"] = {}
        cache = api.fetch_today_shifts(cache)
        cache = api.fetch_shifts_assigned_members(cache)
        self._new_routine(cache)
        self._ROUTINE_RUNNER(cache)

    def rm(self, shift: Shift, cache: Dict[str, Any]) -> Dict[str, Any]:
        """CALLBACK METHOD.
        TAKES A SHIFT FROM cache["current_shifts"]
        REMOVE IT'S REFERENCE.
        
        cache["current_shifts"] is the list of currently 
        displayed shift on the template

        Args:
            shift (Shift): Shift object
            cache (dict): cache containing all shifts

        Returns:
            dict: Updated cache.
        """
        
        for i in range(len(cache["current_shifts"])):
            shift = cache["current_shifts"][i]
            if shift.id == shift.id:
                cache["current_shifts"].pop(i)
                break
        return cache

    def add(self, shift: Shift, cache: Dict[str, Any]) -> Dict[str, Any]:
        """CALLBACK METHOD.
        TAKES A SHIFT FROM cache["shifts"]
        PLACE IT'S REFERENCE IN cache["current_shifts"]
        
        cache["current_shifts"] is the list of currently 
        displayed shift on the template

        Args:
            shift (Shift): Shift object
            cache (dict): cache containing all shifts

        Returns:
            dict: Updated cache.
        """
        cache["current_shifts"].append(shift)
        return cache

    def _clear_passed_tasks(
        self, 
        tasks: List[Tuple[int, datetime, Callable]], 
        cache: Dict[str, Any]
        ) -> Tuple[List[Tuple[int, datetime, Callable]], Dict[str, Any]]:
        
        """TAKES LIST OF TASKS, 
        APPLY THEM UNTIL NEXT TASK DATETIME > CURRENT DATETIME.

        Returns:
            List[Tuple[int, datetime, str]]: list of incoming tasks
            dict: cache with updated current_shifts key
            
        """
        
        now = datetime.now().time()
        for task in deepcopy(tasks):
            if task[1] < now:
                cache = self._execute_once(task, cache)
                tasks.pop(0)
        return (tasks, cache)


    def _new_routine(self, cache: Dict[str, Any]) -> None:
        """SIMILAR TO A CRONTAB.
        BUILD SET OF TASKS CONTAINED IN A DEQUE.
        IN ORDER TO DISPLAY ONLY CURRENT SHIFTS
        
        TASKS ARE DETERMINED BY:
            A TARGETED SHIFT ID
            A DATETIME OF EXECUTION
            A CALL BACK METHOD TO EXECUTE 
            
        CALLBACK:
            ADD: ADD TARGETED SHIFT TO cache["current_shifts"]
            RM: RM TARGETED SHIFT TO cache["current_shifts"]
        
        OPTIONNAL PARAMETERS:
            ACCPT_EARLY_ENTRANCE: int : AFFECT SCHEDULED ADD DATETIME. ADD TASK HAPPEN SOONER
            ACCPT_LATE_ENTRANCE: int : AFFECT SCHEDULED RM DATETIME. RM TASK HAPPEN LATER
        """
        early = getattr(cache["config"], "ACCPT_EARLY_ENTRANCE", 15)
        late = getattr(cache["config"], "ACCPT_LATE_ENTRANCE", 0)
        
        tasks = []
        for shift in list(cache["shifts"].values()):
            begin = datetime.strptime(shift.begin, "%Hh%M") - timedelta(minutes=early)
            end = datetime.strptime(shift.end, "%Hh%M") + timedelta(minutes=late)
            tasks.append((shift.id, begin.time(), self.add))
            tasks.append((shift.id, end.time(), self.rm))      
        tasks.sort(key=lambda x: x[1])
        tasks, cache = self._clear_passed_tasks(tasks, cache)
        self.routine = deque(tasks)


    def _ROUTINE_RUNNER(self, cache: Dict[str, Any]) -> None:
        """RUNNER METHOD. CYCLING
        RUN TIMED THREAD FOR BUILDING ROUTINE AND EXECUTING ROUTINE TASK.
        
        while remain tasks to be executed: start timed thread to execute them
        when all task are done: start timed thread to build new task routine, 
        """
        
        if len(self.routine) > 0:
            task = self.routine.popleft()
            delay = get_delay(task[1])
            print("_________________________________________________________________")
            print(f"[{datetime.now().strftime('%d-%m-%Y %H:%M:%S')}] next task: {task} - scheduled in {delay} sec")
            print("_________________________________________________________________")
            timer = Timer(delay, self._execute, [task, cache])
            timer.start()
        else:
            delay = get_delay_from_datetime((0,10,0))
            print(f"""all scheduled tasks has been resolved.\
                  Awaiting for next new routine in {delay} sec""")
            timer = Timer(delay, self.build_routine, [cache])
            timer.start()
        
    def _execute(
        self, 
        task: Tuple[int, datetime, Callable], 
        cache: Dict[str, Any]
        ) -> None:
        """RUN THREAD RUNNER AFTER EXECUTION, LEADING TO EXECUTION OF NEXT TASK
        TAKES A TASK AND RESOLVE IT'S EFFECT.
        task affect directly cache["current_shifts"] data
        select shifts key and resolve effect of callback method add or rm

        Args:
            task (Tuple[int, datetime, str]): Task to realise,
            contain affected shift id, datetime of execution and callback of realised action
            cache (dict): cache dictionnary containing affected shift
        """
        shift, callback = cache["shifts"][task[0]], task[2]
        cache = callback(shift, cache)
        self._ROUTINE_RUNNER(cache)
        
    def _execute_once(
        self, 
        task:Tuple[int, datetime, Callable], 
        cache: Dict[str, Any]
        ) -> Dict[str, Any]:
        """DO NOT RUN THREAD RUNNER AFTERWARD EXECTUTION
        TAKES A TASK AND RESOLVE IT'S EFFECT.
        task affect directly cache["current_shifts"] data
        select shifts key and resolve effect of callback method add or rm

        Args:
            task (Tuple[int, datetime, str]): Task to realise,
            contain affected shift id, datetime of execution and callback of realised action
            cache (dict): cache dictionnary containing affected shift

        Returns:
            dict: return updated cache
        """
        shift, callback = cache["shifts"][task[0]], task[2]
        cache = callback(shift, cache)
        return cache
        

        