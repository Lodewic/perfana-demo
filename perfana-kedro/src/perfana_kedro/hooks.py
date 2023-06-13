from kedro.framework.hooks import hook_impl
from kedro.framework.project import pipelines
from kedro.io import DataCatalog

from perfana_kedro import pipeline_registry


class ProjectHooks:
    @hook_impl
    def after_context_created(self, context) -> None:
        context.catalog

    @hook_impl
    def after_catalog_created(self, catalog: DataCatalog, conf_catalog) -> None:
        """Hook to fill in and extend templated pipelines."""
        pipeline_registry.register_pipelines = pipeline_registry.register_templated_pipelines(catalog)
        pipelines.configure("perfana_kedro.pipeline_registry")
