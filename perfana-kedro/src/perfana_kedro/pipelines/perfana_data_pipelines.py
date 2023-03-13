from kedro.pipeline import Pipeline, node

from perfana_kedro.nodes.snapshot_data.snapshot_data import (
    count_snapshots_per_test_run,
    filter_test_runs,
    format_snapshot_objects_as_dataframe,
    get_and_parse_grafana_snapshots_objects,
    get_filtered_test_run_ids,
    get_test_run_config_json,
    get_test_run_snapshots_data,
    parse_test_run_config_as_dataframe,
)

mongo_snapshots_pipeline = Pipeline(
    nodes=[
        node(
            get_test_run_snapshots_data,
            inputs=["params:credentials.mongodb.connection_string"],
            outputs="df_mongo_test_runs",
        ),
        node(count_snapshots_per_test_run, inputs=["df_mongo_test_runs"], outputs="df_counts_per_test_run"),
        node(get_filtered_test_run_ids, inputs=["df_mongo_test_runs", "parameters"], outputs="test_run_ids_subset"),
        node(filter_test_runs, inputs=["df_mongo_test_runs", "test_run_ids_subset"], outputs="df_test_runs_subset"),
        node(
            get_test_run_config_json,
            inputs=["params:credentials.mongodb.connection_string", "test_run_ids_subset"],
            outputs="test_run_configs_flat",
        ),
        node(parse_test_run_config_as_dataframe, inputs=["test_run_configs_flat"], outputs="df_test_run_configs"),
        node(
            get_and_parse_grafana_snapshots_objects,
            inputs=["grafana_api_token", "df_test_runs_subset"],
            outputs="list_grafana_snapshots",
        ),
        node(format_snapshot_objects_as_dataframe, inputs=["list_grafana_snapshots"], outputs="df_grafana_snapshots"),
    ]
)
