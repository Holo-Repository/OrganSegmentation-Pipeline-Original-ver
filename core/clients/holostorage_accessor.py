"""
This module contains functionality related to communicating with the
HoloStorageAccessor service. This is where requests should be prepared
such that they comply with the API spec, and the network calls are made.
"""

import json
import logging
from datetime import datetime
from os import path

import requests

from config import HOLOSTORAGE_ACCESSOR_HOST, HOLOSTORAGE_ACCESSOR_PORT
    
from jobs.jobs_io import (get_result_file_path_for_job, get_logger_for_job)


# Note: Could be refactored such that more data is kept in job-specific temp
# directories and less stuff has to be handed from component to component.

holostorage_baseurl = f"{HOLOSTORAGE_ACCESSOR_HOST}"
api_version = "v1"
holograms_endpoint = f"{holostorage_baseurl}/api/{api_version}/holograms"

def send_file_request_to_accessor(job_id: str, plid: str, medical_data: dict) -> None:
    logger = get_logger_for_job(job_id)

    output_file_path = get_result_file_path_for_job(job_id)
    logger.info(f"output_file_path: {output_file_path}")
    file_size_in_kb = int(path.getsize(output_file_path) / 1024)

    meta_data = create_meta_data(file_size_in_kb, plid)
    request_body = {**medical_data, **meta_data}

    # Stringify nested dicts
    request_body["patient"] = json.dumps(request_body["patient"])
    request_body["author"] = json.dumps(request_body["author"])

    # Just by including files, requests will set 'Content-Type' to 'multipart/form-data
    files = {"hologramFile": open(output_file_path, "rb")}

    response = requests.post(holograms_endpoint, data=request_body, files=files)

    if response.status_code == 200:
        logger.info(f"Success! Created hologram: {response.text}")
    else:
        raise Exception(f"Failed to created hologram: {response.text}")


def create_meta_data(file_size_in_kb: int, plid: str) -> dict:
    """
    Returns a dict with the metadata fields defined HoloStorageAccessor API v1.1.0
    (fileSizeInKb, creationDate, creationDescription, contentType, creationMode)
    """
    return {
        "fileSizeInKb": file_size_in_kb,
        "creationDate": datetime.now().strftime("%Y-%m-%dT%H:%M:%S.000Z"),
        "contentType": "model/glb-binary",
        "creationDescription": f"Generated by HoloPipelines with the {plid} pipeline",
        "creationMode": "GENERATE_FROM_IMAGING_STUDY",
    }
