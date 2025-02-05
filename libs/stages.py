import glob
import os
import shutil
import subprocess


def execute_stages(stages: list, disp_output: bool = False) -> (bool, str):
    """
    Executes a series of stages by running their associated commands. Each stage consists
    of a name and a command. The function navigates to the 'git' directory, processes each
    stage, executes the command for it, and optionally displays the output of the command
    based on the disp_output flag. If any stage command fails, the function stops execution
    and returns a failure status with an error message; otherwise, it indicates successful
    completion of all stages.

    :param stages: A list of dictionaries where each dictionary represents a stage. Each stage
        should include a 'name' key (string) for the stage name and a 'command' key (string)
        for the corresponding command to be executed.
    :param disp_output: A boolean flag to determine whether the output of each command should
        be displayed. Defaults to False.
    :return: A tuple where the first element is a boolean indicating success (True) or failure
        (False) and the second element is a string message describing the result.
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
            return False, f"Error executing stage {stage['name']}:\n{e.stderr}"

        # Artifacts
        if 'artifacts' in stage:
            print("Retrieving artifacts...")
            for i, path in enumerate(stage['artifacts']['paths']):
                artifact_path = path
                # Get artifact full path
                if '*' in path:
                    artifact_path = None
                    matching_files = glob.glob(path, recursive=True)
                    if len(matching_files) == 1:
                        artifact_path = matching_files[0]
                    elif len(matching_files) > 1:
                        print(f"Error : Multiple artifacts found for path: {path}")
                    else:
                        print(f"No matching artifact found for path: {path}")

                # Check if artifact is a file or a folder
                if os.path.isdir(artifact_path):
                    artifact_isdir = True
                else:
                    artifact_isdir = False

                # Copy artifact
                if artifact_path is not None:
                    try:
                        if artifact_isdir:
                            shutil.copytree(artifact_path, os.path.join('..', 'artifacts',
                                                                        artifact_path.split('/')[-1].split('\\')[-1]))
                        else:
                            shutil.copy2(artifact_path, os.path.join('..', 'artifacts'))
                        print(f"Copied artifact: {artifact_path}")
                    except Exception as e:
                        print(f"Error copying artifact {artifact_path} to 'artifacts': {e}")

                # Update artifact name, add artifact number to the name in case of multiple artifacts
                if 'name' in stage['artifacts']:
                    original_name = artifact_path.split('/')[-1].split('\\')[-1]
                    extension = original_name.split('.')[-1] if not artifact_isdir else None
                    if len(stage['artifacts']['paths']) > 1:
                        new_name = stage['artifacts']['name'] + f"_{i + 1}"
                    else:
                        new_name = stage['artifacts']['name']
                    if extension is not None:
                        new_name += f".{extension}"

                    try:
                        os.rename(
                            os.path.join('..', 'artifacts', original_name),
                            os.path.join('..', 'artifacts', new_name)
                        )
                        print(f"Renamed '{original_name}' to '{new_name}'")
                    except Exception as e:
                        print(f"Error renaming '{original_name}' to '{new_name}': {e}")

        print("Stage " + stage['name'] + " executed successfully")

    return True, "All stages executed successfully"
