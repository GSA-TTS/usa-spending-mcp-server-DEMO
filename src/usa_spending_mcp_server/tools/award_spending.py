import json
import logging
from datetime import date
from typing import Any, Optional

from fastmcp import FastMCP

from usa_spending_mcp_server.client import USASpendingClient

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


def register_award_spending_tools(mcp: FastMCP, client: USASpendingClient):
    """Register award spending tools"""
    pass
