# Agent Tools - Herramientas que se pasan al agente
# Cada archivo tiene el nombre de la tool que expone

from .get_user_profile import GetUserProfileTool
from .get_full_cv import GetFullCVTool
from .search_jobs import JobSearchTool, SearchRecentJobsTool
from .recommend_companies import CompanyRecommendationTool
from .web_search import GoogleWebSearchTool
from .browse_webpage import BrowseWebpageTool
from .browse_interactive import BrowseInteractiveTool
from .analyze_cv import CVAnalyzerTool
from .linkedin import LinkedInRecruiterTool, LinkedInCompanyTool, ProfileSuggestionsTool

__all__ = [
    'GetUserProfileTool',
    'GetFullCVTool',
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
