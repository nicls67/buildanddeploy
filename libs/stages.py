import glob
import os
import shutil
import subprocess


def execute_stages(stages: list, artifacts_enabled: bool | None, continue_if_fail: bool, disp_output: bool = False) -> (
        bool, str):
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

    :param continue_if_fail: A boolean flag that allows to continue stages execution if previous stage failed.
    :type continue_if_fail: bool

    :param disp_output: A boolean flag indicating whether to display the output (stdout and stderr)
       of the executed commands. Default is False.
    :type disp_output: bool

    :return: A two-element tuple where the first value is a boolean indicating success status
       (True for success, False for failure) and the second value is a string message providing
       additional information about the execution result.
    :rtype: tuple[bool, str]
    """
    if stages is None or len(stages) == 0:
        return True, "No stage to execute"

    # Go into git directory
    os.chdir('git')

    for stage in stages:
        print("\nExecuting stage " + stage['name'] + '...')

        # Execute command
        try:
            result = subprocess.run(stage['command'], shell=True, check=True, text=True, stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE)
            if disp_output:
                print(result.stdout)
                print(result.stderr)
        except subprocess.CalledProcessError as e:
            if continue_if_fail:
                print(f"Error executing stage {stage['name']}:\n{e.stderr}")
                continue
            else:
                return False, f"Error executing stage {stage['name']}:\n{e.stderr}"

        ###########
        # Artifacts
        ###########
        if 'artifacts' in stage:
            process_artifacts = artifacts_enabled if artifacts_enabled is not None else stage['artifacts']['enabled']
            if process_artifacts:
                print("   Retrieving artifacts...")
                for i, path in enumerate(stage['artifacts']['paths']):
                    artifact_path = path
                    # Get artifact full path
                    if '*' in path:
                        artifact_path = None
                        matching_files = glob.glob(path, recursive=True)
                        if len(matching_files) == 1:
                            artifact_path = matching_files[0]
                        elif len(matching_files) > 1:
                            return False, f"   Error : Multiple artifacts found for path: {path}"
                        else:
                            return False, f"   Error : No artifact found for path: {path}"

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
                                shutil.copytree(artifact_path, os.path.join('..', 'artifacts',
                                                                            artifact_path.split('/')[-1].split('\\')[
                                                                                -1]))
                            else:
                                shutil.copy2(artifact_path, os.path.join('..', 'artifacts'))
                            print(f"   Copied artifact: {artifact_path}")
                        except Exception as e:
                            return False, f"   Error copying artifact {artifact_path} to 'artifacts': {e}"

                    ###################################################
                    # Compute file and directories names for next steps
                    ###################################################
                    original_name = artifact_path.split('/')[-1].split('\\')[-1]
                    extension = original_name.split('.')[-1] if not artifact_isdir else None
                    if 'name' in stage['artifacts']:
                        if len(stage['artifacts']['paths']) > 1:
                            artifact_name = stage['artifacts']['name'] + f"_{i + 1}"
                        else:
                            artifact_name = stage['artifacts']['name']
                    else:
                        artifact_name = original_name.split('.')[0]

                    ################################################################################################
                    # Rename artifact
                    #    -> Rename if a name is defined and if zip is not activated and if assemble is not activated
                    ################################################################################################
                    if 'name' in stage['artifacts'] and not stage['artifacts']['archive'] and not stage['artifacts'][
                        'assemble']:
                        new_name = artifact_name
                        if extension is not None:
                            new_name += f".{extension}"

                        try:
                            os.rename(
                                os.path.join('..', 'artifacts', original_name),
                                os.path.join('..', 'artifacts', new_name)
                            )
                            print(f"   Renamed '{original_name}' to '{new_name}'")
                        except Exception as e:
                            return False, f"   Error renaming '{original_name}' to '{new_name}': {e}"

                    ####################################################################
                    # Archive artifact
                    #   -> Archive if archive is activated and assemble is not activated
                    ####################################################################
                    if stage['artifacts']['archive'] and not stage['artifacts']['assemble']:
                        try:
                            if artifact_isdir:
                                shutil.make_archive(os.path.join('..', 'artifacts', artifact_name),
                                                    'zip', os.path.join('..', 'artifacts'), original_name)
                                shutil.rmtree(os.path.join('..', 'artifacts', original_name))
                            else:
                                temp_dir = os.path.join('..', 'artifacts', artifact_name)
                                os.mkdir(temp_dir)
                                shutil.move(os.path.join('..', 'artifacts', original_name), temp_dir)
                                shutil.make_archive(temp_dir,
                                                    'zip', os.path.join('..', 'artifacts', artifact_name))
                                shutil.rmtree(temp_dir)
                            print(f"   Created archive '{artifact_name}.zip'")
                        except Exception as e:
                            return False, f"   Error creating archive: {e}"

                ####################
                # Assemble artifacts
                ####################
                if stage['artifacts']['assemble']:
                    archive_name = stage['artifacts']['name'] if 'name' in stage['artifacts'] else 'artifacts'
                    try:
                        shutil.make_archive(os.path.join('..', archive_name),
                                            'zip', os.path.join('..', 'artifacts'))
                        shutil.rmtree(os.path.join('..', 'artifacts'))
                        os.mkdir(os.path.join('..', 'artifacts'))
                        shutil.move(os.path.join('..', archive_name + '.zip'), os.path.join('..', 'artifacts'))
                        print(f"   Created archive '{archive_name}.zip'")
                    except Exception as e:
                        return False, f"   Error creating archive: {e}"

            else:
                print("   Skipping artifacts")

        print("Stage " + stage['name'] + " executed successfully")

    return True, "All stages executed successfully"
