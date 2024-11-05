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
        sanic: Payload,
        odoo: Payload,
        mail: Payload | None = None,
        options: Payload | None = None,
        logging: Payload | None = None,
        ) -> None:
        self.env = env
        self.print_banner()

        self.app = Sanic("Accueil", log_config=self.setup_logging_configs(logging))

        static = sanic.get("static", None)
        if static is None:
            raise KeyError("Missing `static` field in sanic configs.")
        self.app.static('/static', static)
        self.app.config.update({"ENV": env})
        self.app.config.update({k.upper():v for k,v in sanic.get("app", {}).items()})
        if options is not None:
            self.app.config.update({k.upper():v for k,v in options.items()})

        self.app.blueprint(basebp)
        self.app.blueprint(registrationbp)

        self.app.on_request(go_fast, priority=100)
        self.app.on_response(log_exit, priority=100)
        self.app.error_handler.add(Exception, error_handler)

        self.app.ctx.channels = {"registration": Channel("registration", [])}
        self.app.ctx.odoo = Odoo.initialize(**odoo["erp"])
        if mail is not None:
            self.app.ctx.mail_manager = MailManager.initialize(**mail)
        else:
            self.app.ctx.mail_manager = None
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
