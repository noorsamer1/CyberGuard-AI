from pydantic import BaseModel, Field


class RangeStatus(BaseModel):
    enabled: bool
    target_url: str
    public_url: str
    healthy: bool
    message: str
    # Teaching context: how the range maps to Docker from the API container
    range_target_hostname: str = "range-target"
    range_target_ip: str | None = None
    api_runner_hostname: str | None = None


class RangeScenarioOut(BaseModel):
    id: str
    name: str
    description: str
    severity: str
    mitre_tactics: list[str]
    mitre_techniques: list[str]
    execution_mode: str = "local_range"
    target_url: str
    cli_examples: list[str] = Field(default_factory=list)
    safety_notes: list[str] = Field(default_factory=list)
    expected_detections: list[str] = Field(default_factory=list)


class RangeRunResult(BaseModel):
    scenario_id: str
    name: str
    requests_executed: int
    logs_collected: int
    events_ingested: int
    alerts_generated: int
    incidents_created: int
    message: str
