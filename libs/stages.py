import glob
import os
import shutil
import subprocess
from logging import Logger

import libs.constants as constants


def execute_stages(stages: list, artifacts_enabled: bool | None, continue_if_fail: bool, logger: Logger,
                   disp_output: bool = False) -> bool:
    """
    Executes a list of pipeline stages, handles their artifacts, and provides execution results.

    Each stage in the given pipeline consists of commands to execute and optional artifact processing.
    The function performs the following:
    - Executes the specified commands for each stage.
    - Optionally processes artifacts if defined, including copying, renaming, archiving, and assembling.

    :param stages: A list of stages to execute. Each stage is expected to be a dictionary containing the
       keys 'name' for the stage name and 'command' for the shell command to execute.
       Optionally, a stage can have an 'artifacts' key, which itself contains artifact settings
       such as 'paths', 'enabled', 'name', 'archive', and 'assemble'.
    :type stages: list[dict]

    :param artifacts_enabled: A boolean or None flag that overrides whether artifacts are
       processed or not. If None, the 'artifacts.enabled' property in each stage determines the value.
    :type artifacts_enabled: bool | None

    :param continue_if_fail: A boolean flag that allows continuing stages execution if the previous stage failed.
    :type continue_if_fail: bool

    :param logger: A logger instance to use for logging messages.
    :type logger: Logger

    :param disp_output: A boolean flag indicating whether to display the output (stdout and stderr)
       of the executed commands. Default is False.
    :type disp_output: bool

    :return: A two-element tuple where the first value is a boolean indicating success status
       (True for success, False for failure), and the second value is a string message providing
       additional information about the execution result.
    :rtype: tuple[bool, str]
    """
    logger.info("")

    if stages is None or len(stages) == 0:
        logger.warning("No stage to execute")
        return True

    # Go into the git directory
    os.chdir(constants.GIT)

    for stage in stages:
        logger.info("")
        logger.info(f"Executing stage {stage[constants.NAME]}")

        # Execute command
        try:
            result = subprocess.run(stage[constants.COMMAND], shell=True, check=True, text=True, stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE)
            if disp_output:
                logger.info("Command output:")
                logger.info(result.stdout)
                logger.info(result.stderr)
        except subprocess.CalledProcessError as e:
            logger.error(f"Error executing stage {stage[constants.NAME]}:\n{e.stderr}")
            if continue_if_fail:
                continue
            else:
                return False

        ###########
        # Artifacts
        ###########
        if constants.ARTIFACTS in stage:
            process_artifacts = artifacts_enabled if artifacts_enabled is not None else stage[constants.ARTIFACTS][
                constants.ENABLED]
            if process_artifacts:
                logger.info("   Retrieving artifacts...")
                for i, path in enumerate(stage[constants.ARTIFACTS][constants.PATHS]):
                    artifact_path = path
                    # Get artifact full path
                    if '*' in path:
                        matching_files = glob.glob(path, recursive=True)
                        if len(matching_files) == 1:
                            artifact_path = matching_files[0]
                        elif len(matching_files) > 1:
                            logger.error(f"   Error : Multiple artifacts found for path: {path}")
                            return False
                        else:
                            logger.error(f"   Error : No artifact found for path: {path}")
                            return False

                    # Check if artifact is a file or a folder
                    if os.path.isdir(artifact_path):
                        artifact_isdir = True
                    else:
                        artifact_isdir = False

                    ###############
                    # Copy artifact
                    ###############
                    if artifact_path is not None:
                        try:
                            if artifact_isdir:
                                shutil.copytree(artifact_path, os.path.join('..', constants.ARTIFACTS,
                                                                            artifact_path.split('/')[-1].split('\\')[
                                                                                -1]))
                            else:
                                shutil.copy2(artifact_path, os.path.join('..', constants.ARTIFACTS))
                            logger.info(f"   Copied artifact: {artifact_path}")
                        except Exception as e:
                            logger.error(f"   Error copying artifact {artifact_path} to 'artifacts': {e}")
                            return False

                    ###################################################
                    # Compute file and directories names for next steps
                    ###################################################
                    original_name = artifact_path.split('/')[-1].split('\\')[-1]
                    extension = original_name.split('.')[-1] if not artifact_isdir else None
                    if constants.NAME in stage[constants.ARTIFACTS]:
                        if len(stage[constants.ARTIFACTS][constants.PATHS]) > 1:
                            artifact_name = stage[constants.ARTIFACTS][constants.NAME] + f"_{i + 1}"
                        else:
                            artifact_name = stage[constants.ARTIFACTS][constants.NAME]
                    else:
                        artifact_name = original_name.split('.')[0]

                    ################################################################################################
                    # Rename artifact
                    #    -> Rename if a name is defined and if zip is not activated and if assemble is not activated
                    ################################################################################################
                    if constants.NAME in stage[constants.ARTIFACTS] and not stage[constants.ARTIFACTS][
                        constants.ARCHIVE] and not stage[constants.ARTIFACTS][
                        constants.ASSEMBLE]:
                        new_name = artifact_name
                        if extension is not None:
                            new_name += f".{extension}"

                        try:
                            os.rename(
                                os.path.join('..', constants.ARTIFACTS, original_name),
                                os.path.join('..', constants.ARTIFACTS, new_name)
                            )
                            logger.info(f"   Renamed artifact '{original_name}' to '{new_name}'")
                        except Exception as e:
                            logger.error(f"   Error renaming '{original_name}' to '{new_name}': {e}")
                            return False

                    ####################################################################
                    # Archive artifact
                    #   -> Archive if archive is activated and assemble is not activated
                    ####################################################################
                    if stage[constants.ARTIFACTS][constants.ARCHIVE] and not stage[constants.ARTIFACTS][
                        constants.ASSEMBLE]:
                        try:
                            if artifact_isdir:
                                shutil.make_archive(os.path.join('..', constants.ARTIFACTS, artifact_name),
                                                    'zip', os.path.join('..', constants.ARTIFACTS), original_name)
                                shutil.rmtree(os.path.join('..', constants.ARTIFACTS, original_name))
                            else:
                                temp_dir = os.path.join('..', constants.ARTIFACTS, artifact_name)
                                os.mkdir(temp_dir)
                                shutil.move(os.path.join('..', constants.ARTIFACTS, original_name), temp_dir)
                                shutil.make_archive(temp_dir,
                                                    'zip', os.path.join('..', constants.ARTIFACTS, artifact_name))
                                shutil.rmtree(temp_dir)
                            logger.info(f"   Created archive '{artifact_name}.zip'")
                        except Exception as e:
                            logger.error(f"   Error creating archive: {e}")
                            return False

                ####################
                # Assemble artifacts
                ####################
                if stage[constants.ARTIFACTS][constants.ASSEMBLE]:
                    archive_name = stage[constants.ARTIFACTS][constants.NAME] if constants.NAME in stage[
                        constants.ARTIFACTS] else constants.ARTIFACTS
                    try:
                        shutil.make_archive(os.path.join('..', archive_name),
                                            'zip', os.path.join('..', constants.ARTIFACTS))
                        shutil.rmtree(os.path.join('..', constants.ARTIFACTS))
                        os.mkdir(os.path.join('..', constants.ARTIFACTS))
                        shutil.move(os.path.join('..', archive_name + '.zip'), os.path.join('..', constants.ARTIFACTS))
                        logger.info(f"   Created archive '{archive_name}.zip'")
                    except Exception as e:
                        logger.error(f"   Error creating archive: {e}")
                        return False

            else:
                logger.info("   Skipping artifacts generation")

        logger.info("Stage " + stage[constants.NAME] + " executed successfully")

    logger.info("")
    logger.info("All stages executed successfully")
    return True
