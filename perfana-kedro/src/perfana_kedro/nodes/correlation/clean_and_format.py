from typing import List

import pandas as pd


def flatten_multiindex_columns(df, sep: str = " | "):
    df.columns = [sep.join([e for e in x if e != ""]) for x in df.columns.values]
    return df


def format_dashboard_as_wide(df_snapshots: pd.DataFrame, dashboard_title: str) -> pd.DataFrame:
    df_dashboard_pivot = (
        df_snapshots.loc[df_snapshots["dashboard_title"] == dashboard_title]
        .drop_duplicates(
            subset=[
                "time",
                "dashboard_title",
                "panel_id",
                "name",
                "panel",
                "key",
                "testRunId",
            ]
        )
        .pivot(
            index=[
                "time",
                "start_time",
                "timestep",
                "testRunId",
                "key",
                "dashboard_title",
            ],
            columns=["panel", "name"],
            values="value",
        )
        .reset_index(level=[1, 2, 3, 4, 5])
        .pipe(lambda df: df.set_index(df.index.round(freq="s")))
        .pipe(flatten_multiindex_columns)
    )

    return df_dashboard_pivot


def calculate_correlation_metrics(
    df_wide: pd.DataFrame,
    timestep_freq: str = "10s",
    index_columns: List[str] = ["timestep", "testRunId", "key", "start_time"],
) -> pd.DataFrame:
    df_rounded = (
        df_wide.pipe(lambda d: d.loc[:, d.isna().sum() != d.shape[0]])
        .assign(timestep=lambda d: d["timestep"].dt.round(freq="10s").dt.total_seconds())
        .groupby(["timestep", "testRunId", "key", "start_time"])
        .mean()
        .fillna(0)
        # .corr()
        # .pipe(lambda d: d.loc[d.isna().sum(axis=0) != d.shape[1], d.isna().sum() != d.shape[0]])
    )

    # calculate correlation and keep only values that aren't all NaN
    df_correlation = df_rounded.corr(method="pearson").pipe(
        lambda d: d.loc[d.isna().sum(axis=0) != d.shape[1], d.isna().sum() != d.shape[0]]
    )
    return df_correlation
