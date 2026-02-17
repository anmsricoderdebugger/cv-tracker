from enum import Enum

from pydantic import BaseModel


class ExportFormat(str, Enum):
    csv = "csv"
    xlsx = "xlsx"
    pdf = "pdf"


class ExportRequest(BaseModel):
    format: ExportFormat = ExportFormat.csv
