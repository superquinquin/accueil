from __future__ import annotations

import os
from sanic import Sanic
from sanic.log import LOGGING_CONFIG_DEFAULTS

from typing import Any



from accueil.routes import basebp, registrationbp
from accueil.channel import Channel
from accueil.mail import MailManager
from accueil.models.odoo import Odoo
from accueil.listeners import start_scheduler
from accueil.middlewares import go_fast, log_exit, error_handler
from accueil.parsers import get_config

Payload = dict[str, Any]

BANNER = """\
   _____ ____  ____    ___                        _ __
  / ___// __ \/ __ \  /   | ____________  _____  (_) /
  \__ \/ / / / / / / / /| |/ ___/ ___/ / / / _ \/ / / 
 ___/ / /_/ / /_/ / / ___ / /__/ /__/ /_/ /  __/ / /  
/____/\___\_\___\_\/_/  |_\___/\___/\__,_/\___/_/_/   
                                            v1.0.0
"""

class Accueil:
    def __init__(
        self,
        *,
        env: str = "development",
        sanic: Payload | None = {},
        odoo: Payload | None = None,
        mail: Payload | None = None,
        options: Payload | None = None,
        logging: Payload | None = None,
        ) -> None:
        self.env = env
        self.print_banner()        

        self.app = Sanic("Accueil", log_config=self.setup_logging_configs(logging))
        self.app.static('/static', sanic.get("static"))
        self.app.config.update({"ENV": env})
        self.app.config.update({k.upper():v for k,v in sanic.get("app", {}).items()})
        self.app.config.update({k.upper():v for k,v in options.items()})
        
        self.app.blueprint(basebp)
        self.app.blueprint(registrationbp)
        
        self.app.on_request(go_fast, priority=100)
        self.app.on_response(log_exit, priority=100)
        self.app.error_handler.add(Exception, error_handler)
        
        self.app.ctx.channels = {"registration": Channel("registration", [])}
        self.app.ctx.odoo = Odoo.initialize(**odoo["erp"])
        self.app.ctx.mail_manager = MailManager.initialize(**mail)
        self.app.register_listener(start_scheduler, "after_server_start")
                
    @classmethod
    def create_app(cls) -> Accueil:
        cfg = get_config(os.environ.get("CONFIG_FILEPATH", "./configs/config.yaml"))
        return cls(**cfg)
        
    def print_banner(self) -> None:
        print(BANNER)
        print(f"Booting {self.env}")
    
    def setup_logging_configs(self, logging: dict[str, Any] | None) -> dict[str, Any]:
        if logging is None:
            return LOGGING_CONFIG_DEFAULTS
        logging["loggers"].update(LOGGING_CONFIG_DEFAULTS["loggers"])
        logging["handlers"].update(LOGGING_CONFIG_DEFAULTS["handlers"])
        logging["formatters"].update(LOGGING_CONFIG_DEFAULTS["formatters"])
        return logging