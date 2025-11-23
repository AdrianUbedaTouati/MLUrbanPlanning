# Tools Module
#
# Estructura:
# - agent_tools/  → Tools que se pasan al agente (con nombres claros de función)
# - core/         → Infraestructura, clases base, registry

# Exportar desde core
from .core.base import BaseTool
from .core.registry import ToolRegistry
from .core.schema_converters import (
    SchemaConverter,
    ToolCallConverter,
    convert_tools_for_provider,
)

# Exportar desde agent_tools
from .agent_tools.get_user_profile import GetUserProfileTool
from .agent_tools.search_jobs import JobSearchTool, SearchRecentJobsTool
from .agent_tools.recommend_companies import CompanyRecommendationTool
from .agent_tools.web_search import GoogleWebSearchTool
from .agent_tools.browse_webpage import BrowseWebpageTool
from .agent_tools.browse_interactive import BrowseInteractiveTool
from .agent_tools.analyze_cv import CVAnalyzerTool
from .agent_tools.linkedin import LinkedInRecruiterTool, LinkedInCompanyTool, ProfileSuggestionsTool

__all__ = [
    # Core
    'BaseTool',
    'ToolRegistry',
    'SchemaConverter',
    'ToolCallConverter',
    'convert_tools_for_provider',
    # Agent Tools
    'GetUserProfileTool',
    'JobSearchTool',
    'SearchRecentJobsTool',
    'CompanyRecommendationTool',
    'GoogleWebSearchTool',
    'BrowseWebpageTool',
    'BrowseInteractiveTool',
    'CVAnalyzerTool',
    'LinkedInRecruiterTool',
    'LinkedInCompanyTool',
    'ProfileSuggestionsTool',
]
