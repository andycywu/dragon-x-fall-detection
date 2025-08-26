from qai_hub import public_api_pb2 as api_pb


def get_actual_job(
    job_pb: api_pb.Job,
):
    """
    Utility method for getting the job type-specific protobuf from the wrapped Job protobuf.

    Parameters
    ----------
    job_pb: api_pb.Job
        Protobuf for the Job.

    Returns
    -------
    job: api_pb.CompileJob | api_pb.InferenceJob | api_pb.LinkJob | api_pb.ProfileJob | api_pb.QuantizeJob
    """
    job_type = get_job_type(job_pb)

    if job_type == api_pb.JOB_TYPE_COMPILE:
        return job_pb.compile_job
    elif job_type == api_pb.JOB_TYPE_INFERENCE:
        return job_pb.inference_job
    elif job_type == api_pb.JOB_TYPE_LINK:
        return job_pb.link_job
    elif job_type == api_pb.JOB_TYPE_PROFILE:
        return job_pb.profile_job
    elif job_type == api_pb.JOB_TYPE_QUANTIZE:
        return job_pb.quantize_job
    else:
        raise NotImplementedError(f"Not implemented for {job_type}")


def get_job_type(
    job_pb: api_pb.Job,
) -> api_pb.JobType.ValueType:
    """
    Utility method for getting the job type protobuf enum for the wrapped Job protobuf.

    Parameters
    ----------
    job_pb: api_pb.Job
        Protobuf for the Job.

    Returns
    -------
    api_pb.JobType.ValueType
    """
    job_type = job_pb.WhichOneof("job")

    if job_type == "compile_job":
        return api_pb.JOB_TYPE_COMPILE
    elif job_type == "inference_job":
        return api_pb.JOB_TYPE_INFERENCE
    elif job_type == "link_job":
        return api_pb.JOB_TYPE_LINK
    elif job_type == "profile_job":
        return api_pb.JOB_TYPE_PROFILE
    elif job_type == "quantize_job":
        return api_pb.JOB_TYPE_QUANTIZE
    else:
        raise NotImplementedError(f"Not implemented for {job_type}")
