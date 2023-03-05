from kedro.pipeline import Pipeline, node

from perfana_kedro.nodes.snapshot_data.snapshot_data import (
    aggregate_test_runs_to_snapshot_keys,
    count_snapshots_per_test_run,
    get_test_run_snapshots_data,
)

mongo_snapshots_pipeline = Pipeline(
    nodes=[
        node(
            aggregate_test_runs_to_snapshot_keys,
            inputs=["params:credentials.mongodb.connection_string"],
            outputs=["test_runs_snapshot_mapping"],
        ),
        node(
            get_test_run_snapshots_data,
            inputs=["params:credentials.mongodb.connection_string", "test_runs_snapshot_mapping"],
            outputs="df_mongo_test_run_snapshots",
        ),
        node(count_snapshots_per_test_run, inputs=["df_mongo_test_run_snapshots"], outputs="df_counts_per_test_run"),
    ],
)
