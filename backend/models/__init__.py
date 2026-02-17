from backend.models.user import User
from backend.models.job_description import JobDescription
from backend.models.monitored_folder import MonitoredFolder
from backend.models.cv_file import CVFile
from backend.models.parsed_cv import ParsedCV
from backend.models.match_result import MatchResult
from backend.models.processing_log import ProcessingLog

__all__ = [
    "User",
    "JobDescription",
    "MonitoredFolder",
    "CVFile",
    "ParsedCV",
    "MatchResult",
    "ProcessingLog",
]
