from kedro.pipeline import pipeline, node

pipeline = pipeline(
    [node(sum, inputs=["a", "b"], outputs=["c"],  name="node1"), node(sum, inputs=["a", "b"], outputs=["d"], name="node2", tags="node_tag")],
    tags="pipeline_tag",
)
