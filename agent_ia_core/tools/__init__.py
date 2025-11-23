"""
Tools para el sistema de Function Calling.
Cada tool es una función que el LLM puede llamar para obtener información.
"""

from .base import BaseTool
from .cv_analyzer_tool import CVAnalyzerTool
from .job_search_tool import (
    JobSearchTool,
    CompanySearchTool,
    JobMatchTool
)
from .linkedin_tool import (
    LinkedInRecruiterTool,
    LinkedInCompanyTool,
    ProfileSuggestionsTool
)
from .context_tools import (
    GetUserProfileTool,
    GetSearchHistoryTool
)
from .web_search_tool import GoogleWebSearchTool
from .registry import ToolRegistry

__all__ = [
    'BaseTool',
    'CVAnalyzerTool',
    'JobSearchTool',
    'CompanySearchTool',
    'JobMatchTool',
    'LinkedInRecruiterTool',
    'LinkedInCompanyTool',
    'ProfileSuggestionsTool',
    'GetUserProfileTool',
    'GetSearchHistoryTool',
    'GoogleWebSearchTool',
    'ToolRegistry'
]
