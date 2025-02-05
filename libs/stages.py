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
            for path in stage['artifacts']['paths']:
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

                # Copy artifact
                if artifact_path is not None:
                    try:
                        shutil.copy2(artifact_path, os.path.join('..', 'artifacts'))
                        print(f"Copied artifact: {artifact_path}")
                    except Exception as e:
                        print(f"Error copying artifact {artifact_path} to 'artifacts': {e}")

        print("Stage " + stage['name'] + " executed successfully")

    return True, "All stages executed successfully"
