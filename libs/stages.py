import glob
import os
import shlex
import shutil
import subprocess
from datetime import datetime
from logging import Logger
from typing import Any

import libs.constants as constants
from version import APP_NAME, BUILD_AND_DEPLOY_VER


def execute_stages(
    stages: list[dict[str, Any]],
    artifacts_enabled: bool | None,
    continue_if_fail: bool,
    logger: Logger,
    disp_output: bool = False,
    save_output: bool = False,
) -> bool:
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

    :param save_output: A boolean flag indicating whether to save the output (stdout and stderr)
       of the executed commands to a text file in the logs directory. Default is False.
    :type save_output: bool

    :return: A boolean indicating success status (True for success, False for failure).
    :rtype: bool
    """
    logger.info("")

    if not stages:
        logger.warning("No stage to execute")
        return True

    # Go into the git directory
    os.chdir(constants.GIT)

    for stage in stages:
        logger.info("")
        logger.info(f"Executing stage {stage[constants.NAME]}")

        # Execute commands
        for command in stage[constants.COMMAND]:
            logger.info(f"   Executing command: {command}")
            try:
                result = subprocess.run(
                    shlex.split(str(command)),
                    shell=False,
                    check=True,
                    text=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                )
                if disp_output:
                    logger.info("Command output:")
                    logger.info(str(result.stdout))
                    logger.info(str(result.stderr))

                if save_output:
                    with open(
                        os.path.join(
                            "..", constants.LOGS, f"{stage[constants.NAME]}.txt"
                        ),
                        "a",
                    ) as f:
                        _ = f.write(f"{APP_NAME} version {BUILD_AND_DEPLOY_VER}\n")
                        _ = f.write(
                            f"Started {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n\n"
                        )
                        _ = f.write(f">>> {command}\n")
                        _ = f.write(str(result.stdout))
                        _ = f.write(str(result.stderr))
                        _ = f.write("\n")

            except subprocess.CalledProcessError as e:
                logger.error(
                    f"Error executing stage {stage[constants.NAME]}:\n{e.stderr}"
                )
                if save_output:
                    with open(
                        os.path.join(
                            "..", constants.LOGS, f"{stage[constants.NAME]}.txt"
                        ),
                        "a",
                    ) as f:
                        if e.stdout:
                            _ = f.write(str(e.stdout))
                        if e.stderr:
                            _ = f.write(str(e.stderr))
                if continue_if_fail:
                    continue
                else:
                    return False

        ###########
        # Artifacts
        ###########
        if constants.ARTIFACTS in stage:
            process_artifacts: bool = (
                artifacts_enabled
                if artifacts_enabled is not None
                else bool(stage[constants.ARTIFACTS][constants.ENABLED])
            )
            if process_artifacts:
                logger.info("   Retrieving artifacts...")
                for i, path in enumerate(stage[constants.ARTIFACTS][constants.PATHS]):
                    artifact_path: str = str(path)
                    # Get artifact full path
                    if "*" in artifact_path:
                        matching_files = glob.glob(artifact_path, recursive=True)
                        if len(matching_files) == 1:
                            artifact_path = str(matching_files[0])
                        elif len(matching_files) > 1:
                            logger.error(
                                f"   Error : Multiple artifacts found for path: {artifact_path}"
                            )
                            return False
                        else:
                            logger.error(
                                f"   Error : No artifact found for path: {artifact_path}"
                            )
                            return False

                    # Check if artifact is a file or a folder
                    artifact_isdir = os.path.isdir(artifact_path)

                    ###############
                    # Copy artifact
                    ###############
                    try:
                        if artifact_isdir:
                            _ = shutil.copytree(
                                artifact_path,
                                os.path.join(
                                    "..",
                                    constants.ARTIFACTS,
                                    os.path.basename(artifact_path),
                                ),
                            )
                        else:
                            _ = shutil.copy2(
                                artifact_path,
                                os.path.join("..", constants.ARTIFACTS),
                            )
                        logger.info(f"   Copied artifact: {artifact_path}")
                    except Exception as e:
                        logger.error(
                            f"   Error copying artifact {artifact_path} to 'artifacts': {e}"
                        )
                        return False

                    ###################################################
                    # Compute file and directories names for next steps
                    ###################################################
                    original_name = os.path.basename(artifact_path)
                    extension: str | None = (
                        original_name.split(".")[-1] if not artifact_isdir else None
                    )
                    artifact_name: str
                    if constants.NAME in stage[constants.ARTIFACTS]:
                        if len(list(stage[constants.ARTIFACTS][constants.PATHS])) > 1:
                            artifact_name = str(
                                stage[constants.ARTIFACTS][constants.NAME] + f"_{i + 1}"
                            )
                        else:
                            artifact_name = str(
                                stage[constants.ARTIFACTS][constants.NAME]
                            )
                    else:
                        artifact_name = str(original_name.split(".")[0])

                    ################################################################################################
                    # Rename artifact
                    #    -> Rename if a name is defined and if zip is not activated and if assemble is not activated
                    ################################################################################################
                    if (
                        constants.NAME in stage[constants.ARTIFACTS]
                        and not bool(stage[constants.ARTIFACTS][constants.ARCHIVE])
                        and not bool(stage[constants.ARTIFACTS][constants.ASSEMBLE])
                    ):
                        new_name = artifact_name
                        if extension is not None:
                            new_name += f".{extension}"

                        try:
                            os.rename(
                                os.path.join("..", constants.ARTIFACTS, original_name),
                                os.path.join("..", constants.ARTIFACTS, new_name),
                            )
                            logger.info(
                                f"   Renamed artifact '{original_name}' to '{new_name}'"
                            )
                        except Exception as e:
                            logger.error(
                                f"   Error renaming '{original_name}' to '{new_name}': {e}"
                            )
                            return False

                    #########################################################################
                    # Archive artifact
                    #   -> Archive if archive is activated and assemble is not activated
                    #      or artifact is a directory
                    #########################################################################
                    if not bool(stage[constants.ARTIFACTS][constants.ASSEMBLE]) and (
                        bool(stage[constants.ARTIFACTS][constants.ARCHIVE])
                        or artifact_isdir
                    ):
                        try:
                            if artifact_isdir:
                                _ = shutil.make_archive(
                                    os.path.join(
                                        "..", constants.ARTIFACTS, artifact_name
                                    ),
                                    "zip",
                                    os.path.join("..", constants.ARTIFACTS),
                                    original_name,
                                )
                                shutil.rmtree(
                                    os.path.join(
                                        "..", constants.ARTIFACTS, original_name
                                    )
                                )
                            else:
                                temp_dir = os.path.join(
                                    "..", constants.ARTIFACTS, artifact_name
                                )
                                os.mkdir(temp_dir)
                                _ = shutil.move(
                                    os.path.join(
                                        "..", constants.ARTIFACTS, original_name
                                    ),
                                    temp_dir,
                                )
                                _ = shutil.make_archive(
                                    temp_dir,
                                    "zip",
                                    os.path.join(
                                        "..", constants.ARTIFACTS, artifact_name
                                    ),
                                )
                                shutil.rmtree(temp_dir)
                            logger.info(f"   Created archive '{artifact_name}.zip'")
                        except Exception as e:
                            logger.error(f"   Error creating archive: {e}")
                            return False

                ####################
                # Assemble artifacts
                ####################
                if bool(stage[constants.ARTIFACTS][constants.ASSEMBLE]):
                    archive_name: str = str(
                        stage[constants.ARTIFACTS][constants.NAME]
                        if constants.NAME in stage[constants.ARTIFACTS]
                        else constants.ARTIFACTS
                    )
                    try:
                        _ = shutil.make_archive(
                            os.path.join("..", archive_name),
                            "zip",
                            os.path.join("..", constants.ARTIFACTS),
                        )
                        shutil.rmtree(os.path.join("..", constants.ARTIFACTS))
                        os.mkdir(os.path.join("..", constants.ARTIFACTS))
                        _ = shutil.move(
                            os.path.join("..", archive_name + ".zip"),
                            os.path.join("..", constants.ARTIFACTS),
                        )
                        logger.info(f"   Created archive '{archive_name}.zip'")
                    except Exception as e:
                        logger.error(f"   Error creating archive: {e}")
                        return False

            else:
                logger.info("   Skipping artifacts generation")

        logger.info("Stage " + str(stage[constants.NAME]) + " executed successfully")

    logger.info("")
    logger.info("All stages executed successfully")
    return True
