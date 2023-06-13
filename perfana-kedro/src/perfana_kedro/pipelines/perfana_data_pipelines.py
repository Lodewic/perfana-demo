from kedro.io import DataCatalog
from kedro.pipeline import Pipeline, node

from perfana_kedro.nodes.snapshot_data.snapshot_data import (
    count_snapshots_per_test_run,
    filter_test_runs,
    get_and_parse_grafana_snapshots_objects,
    get_test_run_config_json,
    get_test_run_snapshots_data,
)
from perfana_kedro.nodes.utils import add_dataset_copy_with_suffix_filepath


def create_snapshots_pipeline(catalog: DataCatalog):
    static_nodes = [
        node(
            get_test_run_snapshots_data,
            inputs=["params:credentials.mongodb.connection_string"],
            outputs="df_mongo_test_runs",
        ),
        node(
            count_snapshots_per_test_run,
            inputs=["df_mongo_test_runs"],
            outputs="df_counts_per_test_run",
            tags=["statistic"],
        ),
    ]

    parameters = catalog.datasets.parameters.load()
    test_run_filters = parameters["test_run_filter_groups"]

    feed_dict = {}
    nodes_per_test_run_filter = []
    for i, test_run_filter in enumerate(test_run_filters):
        test_run_filter_key = f"params:test_run_filters_group.{i}"
        feed_dict[test_run_filter_key] = test_run_filter

        for key, value in test_run_filter.items():
            feed_dict[f"{test_run_filter_key}.{key}"] = value

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
        nodes_temp = [
            node(
                filter_test_runs,
                inputs={
                    "df_test_runs": "df_mongo_test_runs",
                    "application": f"{test_run_filter_key}.application",
                    "test_environment": f"{test_run_filter_key}.test_environment",
                    "test_type": f"{test_run_filter_key}.test_type",
                },
                outputs=f"df_test_runs_subset__{test_run_filter_string}",
            ),
            node(
                get_test_run_config_json,
                inputs=[
                    "params:credentials.mongodb.connection_string",
                    f"df_test_runs_subset__{test_run_filter_string}",
                ],
                outputs=[
                    f"df_test_run_configs__{test_run_filter_string}",
                    f"test_run_configs_json__{test_run_filter_string}",
                ],
            ),
            node(
                get_and_parse_grafana_snapshots_objects,
                inputs=[
                    "grafana_api_token",
                    f"df_test_runs_subset__{test_run_filter_string}",
                ],
                outputs=[
                    f"df_grafana_snapshots__{test_run_filter_string}",
                    f"list_grafana_snapshots__{test_run_filter_string}",
                ],
            ),
        ]
        nodes_per_test_run_filter.extend(nodes_temp)

        # update catalog DataSets
        for dataset_name in [
            "df_grafana_snapshots",
            "df_test_run_configs",
            "test_run_configs_json",
        ]:
            add_dataset_copy_with_suffix_filepath(
                catalog=catalog,
                dataset_name=dataset_name,
                suffix=test_run_filter_string,
            )

    catalog.add_feed_dict(feed_dict)
    pipeline = Pipeline(nodes=static_nodes + nodes_per_test_run_filter)
    return pipeline


def create_aggregation_pipeline(catalog: DataCatalog):
    parameters = catalog.datasets.parameters.load()
    test_run_filters = parameters["test_run_filter_groups"]

    feed_dict = {}
    nodes_per_test_run_filter = []
    for i, test_run_filter in enumerate(test_run_filters):
        test_run_filter_key = f"params:test_run_filters_group.{i}"
        feed_dict[test_run_filter_key] = test_run_filter

        for key, value in test_run_filter.items():
            feed_dict[f"{test_run_filter_key}.{key}"] = value

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
        nodes_temp = [
            node(
                filter_test_runs,
                inputs={
                    "df_test_runs": "df_mongo_test_runs",
                    "application": f"{test_run_filter_key}.application",
                    "test_environment": f"{test_run_filter_key}.test_environment",
                    "test_type": f"{test_run_filter_key}.test_type",
                },
                outputs=f"df_test_runs_subset__{test_run_filter_string}",
            ),
            node(
                get_test_run_config_json,
                inputs=[
                    "params:credentials.mongodb.connection_string",
                    f"df_test_runs_subset__{test_run_filter_string}",
                ],
                outputs=[
                    f"df_test_run_configs__{test_run_filter_string}",
                    f"test_run_configs_json__{test_run_filter_string}",
                ],
            ),
            node(
                get_and_parse_grafana_snapshots_objects,
                inputs=[
                    "grafana_api_token",
                    f"df_test_runs_subset__{test_run_filter_string}",
                ],
                outputs=[
                    f"df_grafana_snapshots__{test_run_filter_string}",
                    f"list_grafana_snapshots__{test_run_filter_string}",
                ],
            ),
        ]
        nodes_per_test_run_filter.extend(nodes_temp)

        # update catalog DataSets
        for dataset_name in [
            "df_grafana_snapshots",
            "df_test_run_configs",
            "test_run_configs_json",
        ]:
            add_dataset_copy_with_suffix_filepath(
                catalog=catalog,
                dataset_name=dataset_name,
                suffix=test_run_filter_string,
            )

    catalog.add_feed_dict(feed_dict)
    pipeline = Pipeline(nodes=nodes_per_test_run_filter)
