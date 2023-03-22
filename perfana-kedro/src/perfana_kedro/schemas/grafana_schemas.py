from datetime import datetime
from typing import Any, Dict, List, Literal, Optional, Tuple, Union

from pydantic import BaseModel, Field, root_validator


class SnapshotDataFields(BaseModel):
    class SnapshotDataField(BaseModel):
        class SnapshotDataFieldConfig(BaseModel):
            interval: Optional[int]
            displayNameFromDS: Optional[str] = None

        config: SnapshotDataFieldConfig
        name: str
        type: Literal["number", "time", "string", "table"]
        values: List[Union[None, float, str]]

    fields: List[SnapshotDataField]
    meta: Dict[str, Any]
    refId: Optional[str] = None


class SnapshotDataDataPoints(BaseModel):
    datapoints: List[Tuple[float, int]]
    meta: Dict[str, Any]
    alias: str


class SnapshotDataTable(BaseModel):
    rows: List[Any]
    columns: List[Any]


class GrafanaPanel(BaseModel):
    id: int
    has_data: Optional[bool]
    title: Optional[str]
    snapshotData: List[Union[SnapshotDataFields, SnapshotDataDataPoints, SnapshotDataTable]] = []
    preferredVisualisationType: Optional[str] = None
    panel_type: str = Field(alias="id")

    @root_validator(pre=True)
    def check_if_panel_has_data(cls, values):
        values = dict(values)
        panel_has_data = "snapshotData" in values.keys()
        values["has_data"] = panel_has_data
        return values


class GrafanaDashboard(BaseModel):
    id: int
    title: str
    panels: List[GrafanaPanel] = []
    description: Optional[str] = None
    uid: str
    tags: List[str]


class GrafanaSnapshot(BaseModel):
    class SnapshotMeta(BaseModel):
        isSnapshot: bool
        version: int
        created: datetime

    dashboard: GrafanaDashboard
    meta: SnapshotMeta
    key: Optional[str] = None
    testRunId: Optional[str] = None
