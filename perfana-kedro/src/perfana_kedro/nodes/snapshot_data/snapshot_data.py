import logging
from typing import Any, Dict, List, Optional

import httpx
import pandas as pd
import requests
from pymongo import MongoClient
from tqdm import tqdm

from perfana_kedro.schemas import grafana_schemas

logger = logging.getLogger(__name__)


def aggregate_test_runs_to_snapshot_keys(mongo_connection_string: str) -> Dict[str, List[str]]:
    mongo_client = MongoClient(host=mongo_connection_string, connect=True)

    mongo_snapshotkeys = list(
        mongo_client.perfana.snapshots.aggregate(
            [{"$group": {"_id": "$testRunId", "snapshotKeys": {"$push": "$snapshotKey"}}}]
        )
    )
    test_runs_snapshot_mapping = {x["_id"]: x["snapshotKeys"] for x in mongo_snapshotkeys}
    return test_runs_snapshot_mapping


def filter_test_runs(mongo_connection_string: str, parameters: Dict[str, Any]) -> List[str]:
    test_run_ids: List[str] = []
    return test_run_ids


def get_test_run_snapshots_data(
    test_runs_snapshot_mapping: Dict[str, List[str]], mongo_connection_string: str
) -> pd.DataFrame:
    mongo_client = MongoClient(host=mongo_connection_string, connect=True)

    mongo_runs = list(
        mongo_client.perfana.testRuns.find({"testRunId": {"$in": [x for x in test_runs_snapshot_mapping.keys()]}})
    )

    df_test_runs = pd.merge(
        pd.json_normalize(mongo_runs),
        pd.json_normalize(test_runs_snapshot_mapping),
        left_on=["testRunId"],
        right_on=["_id"],
        suffixes=["", "_snapshot"],
    )
    return df_test_runs


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


def get_snapshot(
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
        raise ValueError(response.text)
    response_dict = response.json()
    response_dict["key"] = key
    response_dict["testRunId"] = testRunId
    try:
        snapshot_obj = grafana_schemas.GrafanaSnapshot.parse_obj(response_dict)
    except Exception as e:
        logger.error(response_dict)
        raise e
    return snapshot_obj


def get_snapshots(
    grafana_api_token: str, test_run_id_mapping: Dict[str, List[str]]
) -> List[grafana_schemas.GrafanaSnapshot]:
    snapshots = []
    headers = create_auth_headers(grafana_api_token)

    with httpx.Client(headers=headers) as client:
        for i, (test_run_id, snapshot_keys) in tqdm(
            enumerate(test_run_id_mapping.items()), desc="Getting snapshots for runs"
        ):
            for key in snapshot_keys:
                snapshot = get_snapshot(key=key, testRunId=test_run_id, client=client)
                snapshots.append(snapshot)
            if i > 10:
                break
    return snapshots
