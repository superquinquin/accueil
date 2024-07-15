
import logging
import traceback
from time import perf_counter
from sanic import Request
from sanic.response import HTTPResponse, json

from accueil.exceptions import AccueilException


logger = logging.getLogger("endpointAccess")


async def error_handler(request: Request, exception: Exception):
    perf = round(perf_counter() - request.ctx.t, 5)
    status = getattr(exception, "status", 500)
    logger.error(
        f"{request.host} > {request.method} {request.url} : {str(exception)} [{request.load_json()}][{str(status)}][{str(len(str(exception)))}b][{perf}s]"
    )
    if not isinstance(exception.__class__.__base__, AccueilException):
        # log traceback of non handled errors
        logger.error(traceback.format_exc())
    return json({"status": status, "reasons": str(exception)})

async def go_fast(request: Request) -> HTTPResponse:
    request.ctx.t = perf_counter()

async def log_exit(request: Request, response: HTTPResponse) -> HTTPResponse:
    perf = round(perf_counter() - request.ctx.t, 5)
    if response.status == 200:
        logger.info(
            f"{request.host} > {request.method} {request.url} [{request.load_json()}][{str(response.status)}][{str(len(response.body))}b][{perf}s]"
        )

