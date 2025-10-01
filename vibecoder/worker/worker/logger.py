from __future__ import annotations

import logging

import structlog

logging.basicConfig(level=logging.INFO, format="%(message)s")
structlog.configure(processors=[structlog.processors.TimeStamper(fmt="iso"), structlog.processors.JSONRenderer()])


def get_logger(service: str):
    return structlog.get_logger().bind(svc=service)
