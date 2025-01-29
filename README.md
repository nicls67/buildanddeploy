# BuildAndDeploy

### A Python tool to build and deploy your projects

## Overview

**BuildAndDeploy** is a lightweight Python tool designed to streamline the process of building and deploying your
software projects. It provides an easy-to-use interface and a set of features that simplify the build and deployment
pipeline, making it suitable for both small and large-scale projects.

## Build

To build your project, simply call `build.py` and provide your working directory.

````bash
python build.py <working directory>
````

Working directory must contain a ``config.yaml`` file with build configuration. The following parameters shall be
provided inside the configuration :

* Project repository: ``git_repository``: the url the git repository you want to build
* A list of build stages to execute (``stages``), each stage containing the following parameters :
    * ``name``: name of the stage
    * ``command``: command to execute to build the stage


