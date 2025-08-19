from .client import Client as _Client

_global_client = _Client()

get_devices = _global_client.get_devices
get_device_attributes = _global_client.get_device_attributes
get_frameworks = _global_client.get_frameworks
upload_model = _global_client.upload_model
get_models = _global_client.get_models
get_model = _global_client.get_model
submit_compile_job = _global_client.submit_compile_job
submit_quantize_job = _global_client.submit_quantize_job
submit_profile_job = _global_client.submit_profile_job
submit_inference_job = _global_client.submit_inference_job
submit_link_job = _global_client.submit_link_job
submit_compile_and_profile_jobs = _global_client.submit_compile_and_profile_jobs
submit_compile_and_quantize_jobs = _global_client.submit_compile_and_quantize_jobs
get_jobs = _global_client.get_jobs
get_job_summaries = _global_client.get_job_summaries
get_job = _global_client.get_job
set_verbose = _global_client.set_verbose
upload_dataset = _global_client.upload_dataset
get_datasets = _global_client.get_datasets
get_dataset = _global_client.get_dataset

__all__ = [
    "get_devices",
    "get_device_attributes",
    "get_frameworks",
    "upload_model",
    "get_model",
    "get_models",
    "submit_compile_job",
    "submit_quantize_job",
    "submit_profile_job",
    "submit_inference_job",
    "submit_link_job",
    "submit_compile_and_profile_jobs",
    "submit_compile_and_quantize_jobs",
    "get_job",
    "get_jobs",
    "get_job_summaries",
    "set_verbose",
    "upload_dataset",
    "get_dataset",
    "get_datasets",
]
