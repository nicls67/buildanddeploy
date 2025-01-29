import os
import subprocess


def execute_stages(stages: list, disp_output: bool = False) -> (bool, str):
    if stages is None or len(stages) == 0:
        return True, "No stage to execute"

    # Go into git directory
    os.chdir('git')

    for stage in stages:
        print("\nExecuting stage " + stage['name'] + '...')

        try:
            result = subprocess.run(stage['command'], shell=True, check=True, text=True, stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE)
            if disp_output:
                print(result.stdout)
        except subprocess.CalledProcessError as e:
            return False, f"Error executing stage {stage['name']}:\n{e.stderr}"

        print("Stage " + stage['name'] + " executed successfully")

    return True, "All stages executed successfully"
