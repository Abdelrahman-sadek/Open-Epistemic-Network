from __future__ import annotations

import os
from typing import Optional

from neo4j import GraphDatabase, Driver


def get_neo4j_uri() -> str:
    return os.getenv("NEO4J_URI", "bolt://localhost:7687")


def get_neo4j_auth() -> tuple[str, str]:
    user = os.getenv("NEO4J_USER", "neo4j")
    password = os.getenv("NEO4J_PASSWORD", "password")
    return user, password


def create_neo4j_driver() -> Driver:
    uri = get_neo4j_uri()
    user, password = get_neo4j_auth()
    return GraphDatabase.driver(uri, auth=(user, password))


def get_neo4j_driver() -> Driver:
    """
    Simple process-wide singleton factory for the Neo4j driver.
    """
    global _NEO4J_DRIVER  # type: ignore[annotation-unchecked]
    try:
        return _NEO4J_DRIVER
    except NameError:
        _NEO4J_DRIVER = create_neo4j_driver()
        return _NEO4J_DRIVER

