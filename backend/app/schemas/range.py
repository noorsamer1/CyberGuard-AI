from pydantic import BaseModel, Field


class RangeClientIpOut(BaseModel):
    client_ip: str
    note: str = (
        "Use this IP in X-Range-Client-Ip when launching attacks from your device so "
        "range telemetry shows your workstation address instead of the Docker bridge."
    )


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
    execution_commands: list[str] = Field(
        default_factory=list,
        description="Exact curl/probe commands the range runner executes (for UI terminal replay).",
    )
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
    executed_commands: list[str] = Field(
        default_factory=list,
        description="Commands actually run during this launch (matches terminal animation).",
    )
