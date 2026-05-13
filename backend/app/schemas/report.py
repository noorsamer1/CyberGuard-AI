from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.enums import ReportType


class ReportOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    incident_id: int
    report_type: ReportType
    file_path: str
    created_at: datetime
