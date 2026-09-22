#!/bin/bash

sanic asgi:app --host=0.0.0.0 --port=8010 --single-process --no-motd
