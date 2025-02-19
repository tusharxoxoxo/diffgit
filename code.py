import os
import subprocess
import json
import logging
from typing import Dict, List

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("clone_and_lint.log"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


def run_flake8(directory: str) -> List[Dict]:
    try:
        logger.info(f"Running flake8 on directory: {directory}")
        result = subprocess.run(
            [
                "flake8",
                "--max-line-length=120",
                "--statistics",
                "--show-source",
                directory,
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0 and result.stderr:
            logger.warning(f"Flake8 completed with warnings: {result.stderr}")

        # Parse flake8 output into structured format
        violations = []
        unparseable_lines = []
        syntax_warnings = []
        current_file = None
        current_file_content = None

        if result.stdout:
            for line in result.stdout.splitlines():
                if line.strip():
                    try:
                        if ":" in line:
                            parts = line.split(":", 3)
                            if len(parts) >= 4:
                                file_path, line_num, col, message = parts
                                file_path = file_path.strip()
                                line_num = int(line_num)

                                # Read the source file if it's different from the current one
                                if current_file != file_path:
                                    try:
                                        with open(file_path, "r") as f:
                                            current_file_content = f.readlines()
                                            current_file = file_path
                                    except Exception as e:
                                        logger.error(
                                            f"Failed to read file {file_path}: {str(e)}"
                                        )
                                        current_file_content = None

                                # Extract code snippet (3 lines before and after the violation)
                                code_snippet = ""
                                if current_file_content:
                                    start_line = max(0, line_num - 4)
                                    end_line = min(
                                        len(current_file_content), line_num + 3
                                    )
                                    code_snippet = "".join(
                                        current_file_content[start_line:end_line]
                                    )

                                violations.append(
                                    {
                                        "path": file_path,
                                        "line": line_num,
                                        "column": int(col),
                                        "message": message.strip(),
                                        "type": message.strip().split()[0]
                                        if message.strip()
                                        else "unknown",
                                        "code_snippet": code_snippet,
                                        "snippet_start_line": start_line + 1,
                                    }
                                )
                            elif len(parts) == 2 and "SyntaxWarning" in line:
                                syntax_warnings.append(line)
                    except (ValueError, IndexError):
                        if not line.startswith(" ") and not any(
                            x in line for x in ["SyntaxWarning", "line too long"]
                        ):
                            unparseable_lines.append(line)

        # Save unparseable lines to a separate log file
        if unparseable_lines:
            unparseable_file = f"{os.path.basename(directory)}_unparseable.log"
            with open(unparseable_file, "w") as f:
                f.write("\n".join(unparseable_lines))
            logger.info(f"Unparseable lines saved to {unparseable_file}")

        # Save syntax warnings to a separate log file
        if syntax_warnings:
            warnings_file = f"{os.path.basename(directory)}_syntax_warnings.log"
            with open(warnings_file, "w") as f:
                f.write("\n".join(syntax_warnings))
            logger.info(f"Syntax warnings saved to {warnings_file}")

        return violations
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse flake8 output: {str(e)}")
        return []
    except subprocess.SubprocessError as e:
        logger.error(f"Subprocess error running flake8: {str(e)}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error running flake8: {str(e)}")
        return []


def clone_repository(repo_url: str, target_dir: str) -> bool:
    try:
        logger.info(f"Attempting to clone {repo_url} to {target_dir}")
        result = subprocess.run(
            ["git", "clone", "--depth", "1", repo_url, target_dir],
            check=True,
            capture_output=True,
            text=True,
        )
        logger.info(f"Successfully cloned {repo_url} to {target_dir}")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Git clone failed for {repo_url}: {e.stderr}")
        return False
    except OSError as e:
        logger.error(f"OS error while cloning {repo_url}: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error while cloning {repo_url}: {str(e)}")
        return False


def main():
    # Define repositories to clone
    repositories = [
        {
            "url": "https://github.com/huggingface/transformers",
            "target": "transformers",
        },
        {"url": "https://github.com/hummingbot/hummingbot", "target": "hummingbot"},
    ]

    try:
        # Get the current working directory
        base_dir = os.getcwd()
        logger.info(f"Starting repository cloning and linting process in {base_dir}")

        # Clone and lint each repository
        for repo in repositories:
            target_path = os.path.join(base_dir, repo["target"])

            # Check if target directory already exists
            if os.path.exists(target_path):
                logger.info(
                    f"Target directory {target_path} already exists. Skipping clone..."
                )
            else:
                if not clone_repository(repo["url"], target_path):
                    logger.warning(
                        f"Skipping linting for {repo['target']} due to clone failure"
                    )
                    continue

            # Run flake8 on the repository
            logger.info(f"Running flake8 on {target_path}...")
            lint_results = run_flake8(target_path)

            # Save lint results to a separate JSON file for each repository
            output_file = f"{repo['target']}_lint.json"
            if len(lint_results) > 0:
                with open(output_file, "w") as f:
                    json.dump(lint_results, f, indent=2)
                logger.info(
                    f"Flake8 results for {repo['target']} saved to {output_file}"
                )
            else:
                logger.warning(
                    f"No linting violations found for {repo['target']} or failed to parse flake8 output"
                )

    except Exception as e:
        logger.error(f"Script execution failed: {str(e)}")
        raise


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.critical(f"Fatal error occurred: {str(e)}")
        exit(1)
