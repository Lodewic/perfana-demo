from kedro.pipeline import Pipeline, node
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from perfana_kedro.nodes.connections.grafana_api import get_grafana_api_token


def create_mariadb_sessionmaker(connection_string: str):
    engine = create_engine(connection_string)
    return sessionmaker(engine)


connection_pipeline = Pipeline(
    nodes=[
        node(
            get_grafana_api_token,
            inputs=["params:credentials.grafana.user", "params:credentials.grafana.password"],
            outputs="grafana_api_token",
        )
    ]
)
