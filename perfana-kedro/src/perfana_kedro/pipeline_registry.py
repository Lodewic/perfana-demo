"""Project pipelines."""
from typing import Dict

from kedro.pipeline import Pipeline

from perfana_kedro.pipelines import connections_pipeline, perfana_data_pipelines


def register_pipelines() -> Dict[str, Pipeline]:
    """Register the project's pipelines.

    Returns:
        A mapping from pipeline names to ``Pipeline`` objects.
    """
    pipelines: Dict[str, Pipeline] = {
        "connections": connections_pipeline.connection_pipeline,
        "mongo_snapshots": perfana_data_pipelines.mongo_snapshots_pipeline,
    }
    pipelines["__default__"] = sum(pipelines.values())
    return pipelines
