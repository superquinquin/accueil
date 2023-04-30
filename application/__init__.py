from flask import Flask
from flask_socketio import SocketIO

from application.config import define_config, define_client_config, parser
from application.back.odoo import Odoo
from application.back.scheduler import Scheduler

config = define_config(parser().config)
socketio = SocketIO(async_mode='gevent') #
cache = {"config": config, "shifts": {}, "current_shifts": []}
schedule = Scheduler()
schedule.build_routine(cache, from_runner=False)

def create_app(config_name: str = None, main: bool = True) -> Flask :
    global cache 
    
    config = define_config(config_name)
    define_client_config(config)
    
    app = Flask(__name__,
                static_url_path= config.STATIC_URL)
    app.config.from_object(config)
    
    
    import application.back.routes as routes
    import application.back.events
    app.add_url_rule('/', view_func=routes.shifts)
    app.add_url_rule('/all', view_func=routes.all_shifts)
    
    socketio.init_app(app, 
                      cors_allowed_origins= config.CORS_ALLOWED_ORIGINS,
                      logger= config.LOGGER,
                      engineio_logger= config.ENGINEIO_LOGGER)
    
    return app
