"""
This module loads the variables defined in the .env file (if it exists)
into the environment and loads configuration variables for other components
to import.
"""

import logging
import os
import sys

from dotenv import load_dotenv

# Load data from .env file (will not override actual env variables if set)
load_dotenv()

# Application
FLASK_ENV = "development"
APP_PORT = int(os.getenv("APP_PORT", 3100))

# Settings for processing etc.
INPUT_RESOLUTION_MAX = int(os.getenv("INPUT_RESOLUTION_MAX", 256))
SIMPLIFICATION_RATIO = float(os.getenv("SIMPLIFICATION_RATIO", 0.5))

# Jobs
NUM_OF_WORKER_PROCESSES = int(os.getenv("NUMBER_OF_WORKER_PROCESSES", 4))
KEEP_ALL_FILES = os.getenv("KEEP_ALL_FILES") == "True"
KEEP_ALL_LOG_FILES = os.getenv("KEEP_ALL_LOG_FILES") == "True"
GARBAGE_COLLECTION_INTERVAL_SECS = int(
    os.getenv("GARBAGE_COLLECTION_INTERVAL_SECS", 30)
)
GARBAGE_COLLECTION_INACTIVE_JOB_TTL_SECS = int(
    os.getenv("GARBAGE_COLLECTION_INACTIVE_JOB_TTL_SECS", 1800)
)

# Models
NIFTYNET_MODEL_TIMEOUT = int(os.getenv("NIFTYNET_MODEL_TIMEOUT", 300))
MODEL_ABDOMINAL_SEGMENTATION_HOST = "https://organsegmentation-model-app.azurewebsites.net"
MODEL_ABDOMINAL_SEGMENTATION_PORT = int(os.getenv("MODEL_ABDOMINAL_SEGMENTATION_PORT", 5000))

# Other service endpoints
HOLOSTORAGE_ACCESSOR_HOST = "https://organsegmentation-storageaccessor-app.azurewebsites.net"
HOLOSTORAGE_ACCESSOR_PORT = int(os.getenv("HOLOSTORAGE_ACCESSOR_PORT", 3200))

bool_vars = [KEEP_ALL_FILES, KEEP_ALL_LOG_FILES]
string_vars = [FLASK_ENV, MODEL_ABDOMINAL_SEGMENTATION_HOST, HOLOSTORAGE_ACCESSOR_HOST]
num_vars = [
    APP_PORT,
    INPUT_RESOLUTION_MAX,
    NUM_OF_WORKER_PROCESSES,
    MODEL_ABDOMINAL_SEGMENTATION_PORT,
    HOLOSTORAGE_ACCESSOR_PORT,
    GARBAGE_COLLECTION_INTERVAL_SECS,
    GARBAGE_COLLECTION_INACTIVE_JOB_TTL_SECS,
    NIFTYNET_MODEL_TIMEOUT,
]

if any(var is None for var in bool_vars) or not all(string_vars) or not all(num_vars):
    logging.error("Fatal error: Not all required environment variables are set")

    # Note: This return code is kind of a hack. When invoked through gunicorn,
    # any other return code seems to restart the server, which is usually good.
    # In this case however, it is preferable to error out immediately.
    sys.exit(4)
