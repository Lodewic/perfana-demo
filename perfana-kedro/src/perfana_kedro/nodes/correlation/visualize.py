import pandas as pd


def visualize_correlation_plotly(df_correlation: pd.DataFrame):
    import plotly.figure_factory as ff
    import plotly.graph_objects as go
    from scipy.spatial.distance import pdist, squareform

    data_array = df_correlation.values
    labels = df_correlation.columns

    # Initialize figure by creating upper dendrogram
    fig = ff.create_dendrogram(data_array, orientation="bottom", labels=labels)
    for i in range(len(fig["data"])):
        fig["data"][i]["yaxis"] = "y2"

    # Create Side Dendrogram
    dendro_side = ff.create_dendrogram(data_array, orientation="right")
    for i in range(len(dendro_side["data"])):
        dendro_side["data"][i]["xaxis"] = "x2"

    # Add Side Dendrogram Data to Figure
    for data in dendro_side["data"]:
        fig.add_trace(data)

    # Create Heatmap
    dendro_leaves = dendro_side["layout"]["yaxis"]["ticktext"]
    dendro_leaves = list(map(int, dendro_leaves))
    data_dist = pdist(data_array)
    heat_data = squareform(data_dist)
    heat_data = heat_data[dendro_leaves, :]
    heat_data = heat_data[:, dendro_leaves]

    heatmap = [go.Heatmap(x=dendro_leaves, y=dendro_leaves, z=heat_data, colorscale="Viridis")]

    heatmap[0]["x"] = fig["layout"]["xaxis"]["tickvals"]
    heatmap[0]["y"] = dendro_side["layout"]["yaxis"]["tickvals"]

    # Add Heatmap Data to Figure
    for data in heatmap:
        fig.add_trace(data)

    # Edit Layout
    fig.update_layout(
        {
            "width": 1600,
            "height": 1600,
            "title": "Hierarchical clustering based on correlation between metrics",
            "showlegend": False,
            "hovermode": "closest",
        }
    )
    # Edit xaxis
    fig.update_layout(
        xaxis={
            "domain": [0.15, 1],
            "mirror": False,
            "showgrid": False,
            "showline": False,
            "zeroline": False,
            "ticks": "",
        }
    )
    # Edit xaxis2
    fig.update_layout(
        xaxis2={
            "domain": [0, 0.15],
            "mirror": False,
            "showgrid": False,
            "showline": False,
            "zeroline": False,
            "showticklabels": False,
            "ticks": "",
        }
    )

    # Edit yaxis
    fig.update_layout(
        yaxis={
            "domain": [0, 0.85],
            "mirror": False,
            "showgrid": False,
            "showline": False,
            "zeroline": False,
            "showticklabels": False,
            "ticks": "",
        }
    )
    # Edit yaxis2
    fig.update_layout(
        yaxis2={
            "domain": [0.825, 0.975],
            "mirror": False,
            "showgrid": False,
            "showline": False,
            "zeroline": False,
            "showticklabels": False,
            "ticks": "",
        }
    )
    return fig
