from pathlib import Path

from kedro.extras.datasets.pickle import PickleDataSet
from kedro.io import DataCatalog, MemoryDataSet
from kedro.pipeline import Pipeline

from kedro_azureml.datasets.pipeline_dataset import AzureMLPipelineDataSet
from kedro_azureml.runner import AzurePipelinesRunner


def test_can_invoke_dummy_pipeline(
    dummy_pipeline: Pipeline, patched_azure_runner: AzurePipelinesRunner
):
    runner = patched_azure_runner
    catalog = DataCatalog()
    input_data = ["yolo :)"]
    catalog.add("input_data", MemoryDataSet(data=input_data))
    results = runner.run(
        dummy_pipeline,
        catalog,
    )
    assert results["output_data"] == input_data, "No output data found"


def test_runner_fills_missing_datasets(
    dummy_pipeline: Pipeline, patched_azure_runner: AzurePipelinesRunner
):
    input_data = ["yolo :)"]
    runner = patched_azure_runner
    catalog = DataCatalog()
    catalog.add("input_data", MemoryDataSet(data=input_data))
    for node_no in range(3):
        results = runner.run(
            dummy_pipeline.filter(node_names=[f"node{node_no+1}"]),
            catalog,
        )
    assert results["output_data"] == input_data, "Invalid output data"


def test_runner_pipeline_data_passing(dummy_pipeline: Pipeline, tmp_path: Path):
    input_path = str(tmp_path / "input_data.pickle")
    input_dataset = AzureMLPipelineDataSet(
        {"type": PickleDataSet, "backend": "cloudpickle", "filepath": input_path}
    )
    input_data = ["yolo :)"]
    input_dataset.save(input_data)

    output_path = str(tmp_path / "i2.pickle")
    output_dataset = AzureMLPipelineDataSet(
        {"type": PickleDataSet, "backend": "cloudpickle", "filepath": output_path}
    )

    runner = AzurePipelinesRunner(
        pipeline_data_passing=True, data_paths={"input_data": tmp_path, "i2": tmp_path}
    )
    catalog = DataCatalog()
    runner.run(
        dummy_pipeline.filter(node_names=["node1"]),
        catalog,
    )
    assert Path(output_path).stat().st_size > 0, "No output data found"
    output_data = output_dataset.load()
    assert output_data == input_data, "Output data is not the same as input data"
