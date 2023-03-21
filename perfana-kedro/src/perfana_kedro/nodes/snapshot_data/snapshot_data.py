import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import httpx
import pandas as pd
import requests
from pydantic import ValidationError
from pymongo import MongoClient
from tqdm import tqdm

from perfana_kedro.schemas import grafana_schemas

logger = logging.getLogger(__name__)


def aggregate_test_runs_to_snapshot_keys(
    mongo_connection_string: str,
) -> Dict[str, List[str]]:
    mongo_client = MongoClient(host=mongo_connection_string, connect=True)

    mongo_snapshotkeys = list(
        mongo_client.perfana.snapshots.aggregate(
            [
                {
                    "$group": {
                        "_id": "$testRunId",
                        "snapshotKeys": {"$push": "$snapshotKey"},
                    }
                }
            ]
        )
    )
    test_runs_snapshot_mapping = {x["_id"]: x["snapshotKeys"] for x in mongo_snapshotkeys}
    return test_runs_snapshot_mapping


def filter_test_runs(
    df_test_runs,
    application: str = "OptimusPrime",
    test_environment: str = "acme",
    test_type: str = "loadTest",
):
    test_run_ids = (
        df_test_runs.query(
            f"application == '{application}' & testEnvironment == '{test_environment}' & testType == '{test_type}' and completed"
        )
        .sort_values("start", ascending=False)["testRunId"]
        .to_list()
    )

    df_test_runs_filtered = df_test_runs.loc[df_test_runs["testRunId"].isin(test_run_ids)]
    return df_test_runs_filtered


def get_test_run_snapshots_data(mongo_connection_string: str) -> pd.DataFrame:
    mongo_client = MongoClient(host=mongo_connection_string, connect=True)
    mongo_snapshotkeys = list(
        mongo_client.perfana.snapshots.aggregate(
            [
                {
                    "$group": {
                        "_id": "$testRunId",
                        "snapshotKeys": {"$push": "$snapshotKey"},
                    }
                }
            ]
        )
    )

    mongo_runs = list(
        mongo_client.perfana.testRuns.find({"testRunId": {"$in": [x["_id"] for x in mongo_snapshotkeys]}})
    )

    df_test_runs = pd.merge(
        pd.json_normalize(mongo_runs),
        pd.json_normalize(mongo_snapshotkeys),
        left_on=["testRunId"],
        right_on=["_id"],
        suffixes=["", "_snapshot"],
    )
    return df_test_runs


def parse_test_run_config_as_dataframe(
    test_run_configs: List[Dict[str, Any]]
) -> Tuple[pd.DataFrame, List[Dict[str, Any]]]:
    df_test_run_configs = pd.json_normalize(test_run_configs)
    return df_test_run_configs


def get_test_run_config_json(
    mongo_connection_string: str, df_test_runs: Optional[pd.DataFrame] = None
) -> Tuple[pd.DataFrame, List[Dict[str, Any]]]:
    mongo_client = MongoClient(host=mongo_connection_string, connect=True)
    mongo_query = mongo_client.perfana.testRunConfigs
    aggregates: List[Dict[str, Any]] = []
    if df_test_runs is not None:
        test_run_ids = df_test_runs["testRunId"].unique().tolist()
        aggregates.append({"$match": {"$expr": {"$in": ["$testRunId", test_run_ids]}}})
    aggregates.append(
        {
            "$group": {
                "_id": "$testRunId",
                "_key": {"$push": "$key"},
                "_value": {"$push": "$value"},
            }
        }
    )

    mongo_test_run_configs = list(mongo_query.aggregate(aggregates))
    mongo_test_run_configs = [
        {"testRunId": x["_id"], "config": dict(zip(x["_key"], x["_value"]))} for x in mongo_test_run_configs
    ]

    df_test_run_configs = parse_test_run_config_as_dataframe(mongo_test_run_configs)
    return df_test_run_configs, mongo_test_run_configs


def count_snapshots_per_test_run(df_test_runs: pd.DataFrame) -> pd.DataFrame:
    return df_test_runs.groupby(["application", "testEnvironment", "testType"]).count()


def get_snapshot_list(grafana_api_token: str, client: Optional[httpx.Client] = None):
    url = "http://grafana:3000/api/dashboard/snapshots"
    if client is None:
        if grafana_api_token is None:
            raise ValueError("API token cannot be None if Client is None.")
        headers = create_auth_headers(grafana_api_token)
        response = requests.get(url, headers=headers)
    else:
        response = client.get(url)

    if response.status_code != 200:
        logger.error(f"Response status was {response.status_code}: {response.text}")
        raise ValueError(response.text)
    return response.json()


def create_auth_headers(token):
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


def get_grafana_snapshot_object(
    key: str,
    grafana_api_token: Optional[str] = None,
    testRunId: Optional[str] = None,
    client: Optional[httpx.Client] = None,
) -> grafana_schemas.GrafanaSnapshot:
    url = f"http://grafana:3000/api/snapshots/{key}"
    if client is None:
        if grafana_api_token is None:
            raise ValueError("API token cannot be None if Client is None.")
        headers = create_auth_headers(grafana_api_token)
        response = requests.get(url, headers=headers)
    else:
        response = client.get(url)

    if response.status_code != 200:
        logger.error(f"Response status for key: {key} was {response.status_code}: {response.text}")
        # raise ValueError(response.text)
    response_dict = response.json()
    response_dict["key"] = key
    response_dict["testRunId"] = testRunId
    try:
        snapshot_obj = grafana_schemas.GrafanaSnapshot.parse_obj(response_dict)
    except Exception as e:
        logger.error(response_dict)
        raise e
    return snapshot_obj


def format_data_from_snapshot(
    snapshot: grafana_schemas.GrafanaSnapshot,
) -> pd.DataFrame:
    panel_data_list = []
    for panel in snapshot.dashboard.panels:
        if panel.has_data:
            df_panel = format_data_from_panel(panel)
            panel_data_list.append(df_panel)

    df_snapshot = pd.concat(panel_data_list, axis=0).assign(
        key=snapshot.key,
        testRunId=snapshot.testRunId,
        dashboard_title=snapshot.dashboard.title,
        dashboard_id=snapshot.dashboard.id,
    )
    return df_snapshot


def format_snapshot_objects_as_dataframe(
    snapshots: List[grafana_schemas.GrafanaSnapshot],
) -> pd.DataFrame:
    df_snapshots = pd.concat([format_data_from_snapshot(snapshot) for snapshot in snapshots], axis=0)
    df_snapshots = df_snapshots.groupby("testRunId", group_keys=False).apply(
        lambda df: df.assign(start_time=df["time"].min(), timestep=(df["time"] - df["time"].min()))
    )
    return df_snapshots


def get_and_parse_grafana_snapshots_objects(
    grafana_api_token: str, df_test_runs: pd.DataFrame
) -> Tuple[pd.DataFrame, List[grafana_schemas.GrafanaSnapshot]]:
    snapshots = []
    headers = create_auth_headers(grafana_api_token)

    with httpx.Client(headers=headers) as client:
        for i, (idx, row) in tqdm(
            enumerate(df_test_runs.iterrows()),
            desc=f"Getting snapshots for {df_test_runs.shape[0]} runs",
        ):
            for key in row["snapshotKeys"]:
                try:
                    snapshot = get_grafana_snapshot_object(key=key, testRunId=row["testRunId"], client=client)
                    snapshots.append(snapshot)
                except (ValueError, ValidationError):
                    pass

    df_snapshots = format_snapshot_objects_as_dataframe(snapshots)
    return df_snapshots, snapshots


def format_data_from_panel(panel: grafana_schemas.GrafanaPanel) -> pd.DataFrame:
    panel_records = []
    for snapshot_data in panel.snapshotData:
        if isinstance(snapshot_data, grafana_schemas.SnapshotDataFields):
            time_fields = [field for field in snapshot_data.fields if field.type == "time"]
            value_fields = [field for field in snapshot_data.fields if field.type == "number"]

            if len(time_fields) == 1 and len(value_fields) == 1:
                time_field = time_fields[0]
                value_field = value_fields[0]

                col_name = value_field.config.displayNameFromDS or "unkown"
                field_records = [
                    {
                        "panel_id": panel.id,
                        "time": datetime.fromtimestamp(t / 1000.0),
                        "panel": panel.title,
                        "name": col_name,
                        "value": v,
                    }
                    for t, v in zip(time_field.values, value_field.values)
                    if not isinstance(t, str) and t is not None
                ]
            else:
                logger.warning(
                    f"{panel.title} not parsed warning because it didn't match exactly 1 time field and 1 value field."
                )
                continue

        elif isinstance(snapshot_data, grafana_schemas.SnapshotDataDataPoints):
            col_name = snapshot_data.alias
            field_records = [
                {
                    "panel_id": panel.id,
                    "time": datetime.fromtimestamp(x[1] / 1000.0),
                    "panel": panel.title,
                    "name": col_name,
                    "value": x[0],
                }
                for x in snapshot_data.datapoints
            ]
        else:
            logger.error(f"{panel.title} skipped because it didn't match any valid schemas")
            continue

        panel_records.extend(field_records)

    df_panel = pd.DataFrame.from_records(panel_records)

    return df_panel
