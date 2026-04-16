"""HTTP-klienter för Skolverkets API:er."""

from skolverket_mcp.clients.planned_educations import PlannedEducationsClient
from skolverket_mcp.clients.school_registry import SchoolRegistryClient
from skolverket_mcp.clients.syllabus import SyllabusClient

__all__ = ["PlannedEducationsClient", "SchoolRegistryClient", "SyllabusClient"]
