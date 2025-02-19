"""
This pipeline performs automatic multi-organ segmentation on abdominal CT with Dense
V-networks. It leverages a pre-trained network built with Niftynet and running in a
separate container.

Model: https://github.com/NifTK/NiftyNetModelZoo/blob/master/dense_vnet_abdominal_ct_model_zoo.md
Paper: Eli Gibson, Francesco Giganti, Yipeng Hu, Ester Bonmati, Steve Bandula, Kurinchi Gurusamy,
Brian Davidson, Stephen P. Pereira, Matthew J. Clarkson and Dean C. Barratt (2017), Automatic
multi-organ segmentation on abdominal CT with dense v-networks https://doi.org/10.1109/TMI.2018.2806309
"""

import os
import sys

from config import MODEL_ABDOMINAL_SEGMENTATION_HOST, MODEL_ABDOMINAL_SEGMENTATION_PORT
from core.adapters.dicom_file import (
    read_dicom_as_np_ndarray_and_normalise,
    flip_numpy_array_dimensions_y_only,
)
from core.adapters.nifti_file import (
    convert_dicom_np_ndarray_to_nifti_image,
    read_nifti_as_np_array,
    write_nifti_image,
)

from core.adapters.glb_file import write_mesh_as_glb_with_colour
from core.clients import niftynet
from core.services.marching_cubes import generate_mesh, seperate_segmentation
from core.services.np_image_manipulation import downscale_and_conditionally_crop
from core.tasks.shared.dispatch_output import dispatch_output
from core.tasks.shared.receive_input import fetch_and_unzip
from jobs.jobs_io import (
    get_input_directory_path_for_job,
    get_logger_for_job,
    get_result_file_path_for_job,
    get_temp_file_path_for_job,
)
from jobs.jobs_state import JobState, update_job_state

this_plid = os.path.basename(__file__).replace(".py", "")
hu_threshold = 0
segment_type=[]
meshes = []


def run(job_id: str, input_endpoint: str, medical_data: dict) -> None:
    logger = get_logger_for_job(job_id)
    update_job_state(job_id, JobState.STARTED.name, logger)

    update_job_state(job_id, JobState.FETCHING_INPUT.name, logger)
    dicom_directory_path = get_input_directory_path_for_job(job_id)
    fetch_and_unzip(input_endpoint, dicom_directory_path)

    update_job_state(job_id, JobState.READING_INPUT.name, logger)

    dicom_image_array = read_dicom_as_np_ndarray_and_normalise(dicom_directory_path)

    # NOTE: Numpy array is flipped in the Y axis here as this is the specific image input for the NiftyNet model

    dicom_image_array = flip_numpy_array_dimensions_y_only(dicom_image_array)

    crop_dicom_image_array = downscale_and_conditionally_crop(dicom_image_array)

    update_job_state(job_id, JobState.PREPROCESSING.name, logger)
    nifti_image = convert_dicom_np_ndarray_to_nifti_image(crop_dicom_image_array)
    initial_nifti_output_file_path = get_temp_file_path_for_job(job_id, "temp.nii")
    write_nifti_image(nifti_image, initial_nifti_output_file_path)

    update_job_state(job_id, JobState.PERFORMING_SEGMENTATION.name, logger)

    segmented_nifti_output_file_path = get_temp_file_path_for_job(
        job_id, "segmented.nii.gz"
    )

    # Call the Monai model
    niftynet.call_model(
        MODEL_ABDOMINAL_SEGMENTATION_HOST,
        MODEL_ABDOMINAL_SEGMENTATION_PORT,
        initial_nifti_output_file_path,
        segmented_nifti_output_file_path,
        job_id,
    )

    update_job_state(job_id, JobState.POSTPROCESSING.name, logger)
    segmented_array = read_nifti_as_np_array(
        segmented_nifti_output_file_path, normalise=False
    )
    
    # Updated using the method from HoloRepository 2020 View to generate mesh
    for segment in seperate_segmentation(segmented_array, unique_values=segment_type):
        try:
            mesh = generate_mesh(segment, 0)
            meshes.append(mesh)
        except:
            pass

    write_mesh_as_glb_with_colour(meshes,get_result_file_path_for_job(job_id), 30)

    update_job_state(job_id, JobState.DISPATCHING_OUTPUT.name, logger)
    try:
        dispatch_output(job_id, this_plid, medical_data)
    except Exception as e:
        logger.error(f"Error DISPATCHING OUTPUT: {e}")

    update_job_state(job_id, JobState.FINISHED.name, logger)


if __name__ == "__main__":
    run(sys.argv[1], sys.argv[2], sys.argv[3])
