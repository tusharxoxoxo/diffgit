# DiffGit

## Setup
```bash
# Create and activate virtual environment (optional but recommended)
python -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate

# Install dependencies
pip install flake8
```

## Usage

```bash
# Run the main code
python code.py

# Process the code
python code_processor.py
```
## Brief

In this, I have tried to generate a dataset in JSON for the top two most trending Python repository on github this month
![image](https://github.com/user-attachments/assets/4bf4656d-aa48-4724-89f7-3b3dcf7f391a)

## Output Dataset Structure

1. hummingbot_lint
Each entry in this section represents a linting issue found in the Hummingbot project. The structure of each entry is as follows:

```json
[
    {
        "path": "string - The file path where the issue was found",
        "line": "integer - The line number where the issue occurs",
        "column": "integer - The column number where the issue starts",
        "message": "string - The linting message describing the issue",
        "type": "string - The type of linting error (e.g., E501, F401)",
        "code_snippet": "string - A snippet of the code where the issue occurs",
        "snippet_start_line": "integer - The starting line number of the code snippet"
    }
]
```

2. transformers_lint.json

```json
[
    {
        "path": "string - The file path where the issue was found",
        "line": "integer - The line number where the issue occurs",
        "column": "integer - The column number where the issue starts",
        "message": "string - The linting message describing the issue",
        "type": "string - The type of linting error (e.g., E501, F401)",
        "code_snippet": "string - A snippet of the code where the issue occurs",
        "snippet_start_line": "integer - The starting line number of the code snippet"
    }
]
```

3. processed_flake8_dataset

```json
[
    {
        "path": "string - The file path where the issue was found",
        "line": "integer - The line number where the issue occurs",
        "column": "integer - The column number where the issue starts",
        "message": "string - The linting message describing the issue",
        "type": "string - The type of linting error (e.g., E501, F401)",
        "code_snippet": "string - A snippet of the code where the issue occurs",
        "snippet_start_line": "integer - The starting line number of the code snippet"
    }
]
```
