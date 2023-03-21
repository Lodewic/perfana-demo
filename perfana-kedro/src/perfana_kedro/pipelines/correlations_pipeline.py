from kedro.io import DataCatalog
from kedro.pipeline import Pipeline, node
from nodes.correlation.clean_and_format import calculate_correlation_metrics, format_dashboard_as_wide
from nodes.correlation.visualize import visualize_correlation_plotly
from nodes.utils import add_dataset_copy_with_suffix_filepath


def create_pipeline(catalog: DataCatalog) -> Pipeline:
    parameters = catalog.datasets.parameters.load()
    test_run_filter_groups = parameters["test_run_filter_groups"]

    nodes = []
    feed_dict = {}
    for i, test_run_filter in enumerate(test_run_filter_groups):
        test_run_filter_key = f"params:test_run_filters_group.{i}"

        if "correlations" in test_run_filter.keys():
            test_run_filter_string = "__".join(
                [
                    str(x)
                    for x in [
                        test_run_filter["application"],
                        test_run_filter["test_type"],
                        test_run_filter["test_environment"],
                    ]
                ]
            )
            for shortname, dashboard_title in test_run_filter["correlations"]["dashboards"].items():
                feed_dict[f"{test_run_filter_key}.correlations.dashboards.{shortname}"] = dashboard_title
                add_dataset_copy_with_suffix_filepath(
                    catalog=catalog,
                    dataset_name="dashboard_correlation",
                    suffix=f"{shortname}__{test_run_filter_string}",
                )
                add_dataset_copy_with_suffix_filepath(
                    catalog=catalog,
                    dataset_name="correlation_plot",
                    suffix=f"{shortname}__{test_run_filter_string}",
                )

                nodes_tmp = [
                    node(
                        format_dashboard_as_wide,
                        inputs={
                            "df_snapshots": f"df_grafana_snapshots__{test_run_filter_string}",
                            "dashboard_title": f"{test_run_filter_key}.correlations.dashboards.{shortname}",
                        },
                        outputs=f"df_wide_metrics__{shortname}__{test_run_filter_string}",
                    ),
                    node(
                        calculate_correlation_metrics,
                        inputs={"df_wide": f"df_wide_metrics__{shortname}__{test_run_filter_string}"},
                        outputs=f"dashboard_correlation__{shortname}__{test_run_filter_string}",
                    ),
                    node(
                        visualize_correlation_plotly,
                        inputs={"df_correlation": f"dashboard_correlation__{shortname}__{test_run_filter_string}"},
                        outputs=f"correlation_plot__{shortname}__{test_run_filter_string}",
                    ),
                ]
                nodes.extend(nodes_tmp)
    catalog.add_feed_dict(feed_dict)

    pipeline = Pipeline(nodes=nodes)
    return pipeline
