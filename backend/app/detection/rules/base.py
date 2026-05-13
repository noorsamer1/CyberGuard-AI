from dataclasses import dataclass
from typing import Optional

from sqlalchemy.orm import Session

from app.models.enums import Severity
from app.models.event import Event


@dataclass
class RuleHit:
    title: str
    description: str
    severity: Severity
    rule_name: str
    reasoning: str
    event_id: Optional[int] = None


class DetectionRule:
    name: str = "base"

    def evaluate(self, db: Session, event: Event) -> list[RuleHit]:
        raise NotImplementedError
