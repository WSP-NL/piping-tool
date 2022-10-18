# Introduction

Welcome to the Sterke-Lekdijk repo! You can find the user manual for this app in the "manual" subfolder, or through a link in the welcome text you see upon entering a VIKTOR workspace (also present in the welcome.md file in this repository).

# Developing app


This app makes use of code quality tools. These tools are isolated in a seperate requirements file (`dev-requirements.txt`). The following sections helps you with the setup and using these tools.

## Creating a virtual enviroment

To create a venv on Linux:

```
python3 -m venv env
```

Activate the virtual environment:
```
source ./env/bin/activate
```

Install dependencies:
```
pip install -r dev-requirements.txt
```

## Code quality commands
Formatting with black and isort (replace with viktor-cli.exe for Windows):
```
python -m black app/ tests/
python -m isort .
```

Static code analysis:
```
python -m pylint app/ tests/
```

Run tests:
```
viktor-cli test 
```