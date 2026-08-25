from datetime import datetime
from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship


class Scan(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    url: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    score: Optional[float] = None
    violation_count: int = 0
    status: str = "pending"  # pending | running | completed | failed
    error_message: Optional[str] = None
    violations: List["Violation"] = Relationship(back_populates="scan")


class Violation(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    scan_id: int = Field(foreign_key="scan.id")
    rule_id: str
    impact: str  # critical | serious | moderate | minor
    description: str
    target: str
    html_snippet: str
    wcag_tags: str  # stored as comma-separated string
    fix_snippet: Optional[str] = None
    fix_explanation: Optional[str] = None
    scan: Optional[Scan] = Relationship(back_populates="violations")
