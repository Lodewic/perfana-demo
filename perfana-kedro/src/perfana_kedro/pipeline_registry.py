"""Project pipelines."""
from typing import Callable, Dict

from kedro.io import DataCatalog
from kedro.pipeline import Pipeline
from pipelines import correlations_pipeline

from perfana_kedro.pipelines import connections_pipeline, perfana_data_pipelines


def register_pipelines():
    """Method that will be assigned to the callable returned by templated_pipelines(...), by a Hook."""
    raise NotImplementedError(
        """
    register_pipelines() is expected to be overwritten by ProjectHooks.
    Make sure the hooks is found in hooks.py and enabled in settings.py
    """
    )


def register_templated_pipelines(catalog: DataCatalog) -> Callable:
    """Register the project's pipelines depending on the catalog.

    Create pipelines dynamically based on parameters and datasets defined in the catalog.
    The function must return a callable without any arguments that will replace the `register_pipelines()` method
    in this same module, using an `after_catalog_created_hook`.

    Args:
        catalog: The DataCatalog loaded from the KedroContext.

    Returns:
        A callable that returns a mapping from pipeline names to ``Pipeline`` objects.
    """
    # create pipelines with access to catalog
    # created_pipeline = ...
    snapshots_pipeline = perfana_data_pipelines.create_snapshots_pipeline(catalog)
    correlation_pipeline = correlations_pipeline.create_pipeline(catalog)

    def register_pipelines() -> Dict[str, Pipeline]:
        """Register the project's pipelines.

        Returns:
            A mapping from pipeline names to ``Pipeline`` objects.
        """
        pipelines: Dict[str, Pipeline] = {
            "connections": connections_pipeline.connection_pipeline,
            "mongo_snapshots": snapshots_pipeline,
            "correlations": correlation_pipeline,
        }
        pipelines["__default__"] = sum(pipelines.values())
        pipelines["__no_statistic__"] = Pipeline(
            nodes=[node for node in pipelines["__default__"].nodes if "statistic" not in node.tags]
        )
        return pipelines

    return register_pipelines
