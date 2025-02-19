import json
from typing import Dict, List
import re


def normalize_code_snippet(snippet: str) -> str:
    """Remove extra whitespace and normalize indentation."""
    lines = snippet.splitlines()
    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()

    if not lines:
        return ""

    min_indent = float("inf")
    for line in lines:
        if line.strip():
            indent = len(line) - len(line.lstrip())
            min_indent = min(min_indent, indent)

    normalized_lines = [line[min_indent:] if line.strip() else "" for line in lines]
    return "\n".join(normalized_lines)


def fix_code_snippet(snippet: str, error_type: str, line_num: int, column: int) -> str:
    """Apply fixes based on the error type."""
    lines = snippet.splitlines()
    line_index = line_num - 1

    # Check if line_index is valid
    if line_index < 0 or line_index >= len(lines):
        return snippet

    # Common flake8 errors and their fixes
    if error_type in ["F401", "F402", "F403", "F811", "F822", "F841"]:  # Import and variable related errors
        line = lines[line_index]
        if "import" in line:
            # Handle multi-line import statements
            if "(" in line:
                # Find the specific import to remove
                import_name = line.strip().strip(",")
                # Remove the specific import line while preserving the structure
                if import_name:
                    lines[line_index] = ""
            else:
                # Single line import - remove the whole line
                lines.pop(line_index)

    elif error_type == "E501":  # Line too long
        long_line = lines[line_index]
        if "lambda" in long_line:
            parts = long_line.split(": ", 1)
            if len(parts) == 2:
                indent = len(long_line) - len(long_line.lstrip())
                fixed_lines = [parts[0] + ":", " " * (indent + 4) + parts[1]]
                lines[line_index] = "\n".join(fixed_lines)
        else:
            # Add general line splitting for E501
            if len(long_line) > 120:
                # Try to split at commas, spaces, or other logical break points
                for char in [", ", " + ", " and ", " or ", ": "]:
                    if char in long_line[80:]:
                        pos = long_line.find(char, 80)
                        if pos != -1:
                            indent = len(long_line) - len(long_line.lstrip())
                            fixed_lines = [
                                long_line[:pos + len(char) - 1],
                                " " * (indent + 4) + long_line[pos + len(char) - 1:]
                            ]
                            lines[line_index] = fixed_lines[0]
                            lines.insert(line_index + 1, fixed_lines[1])
                            break

    # Indentation errors
    elif error_type in ["E101", "E116", "E117", "E122", "E124", "E127", "E128", "E131"]:
        line = lines[line_index]
        indent = len(line) - len(line.lstrip())
        if indent % 4 != 0:  # Fix indentation to be multiple of 4
            correct_indent = (indent // 4) * 4
            lines[line_index] = " " * correct_indent + line.lstrip()

    # Whitespace errors
    elif error_type in ["E201", "E202", "E203"]:  # Whitespace around parentheses/brackets
        line = lines[line_index]
        line = re.sub(r"\(\s+", "(", line)  # Remove space after (
        line = re.sub(r"\s+\)", ")", line)  # Remove space before )
        line = re.sub(r"\s+:\s+", ": ", line)  # Fix space around colons
        lines[line_index] = line

    elif error_type in ["E221", "E222", "E225", "E251", "E252"]:  # Whitespace around operators
        line = lines[line_index]
        line = re.sub(r"\s*=\s*", "=", line)  # Fix spaces around =
        line = re.sub(r"\s*,\s*", ", ", line)  # Fix spaces around ,
        line = re.sub(r"\s*\+\s*", " + ", line)  # Fix spaces around +
        lines[line_index] = line

    elif error_type in ["E261", "E262", "E266"]:  # Comment formatting
        line = lines[line_index]
        if "#" in line:
            code, comment = line.split("#", 1)
            lines[line_index] = f"{code.rstrip()}  # {comment.lstrip()}"

    elif error_type in ["E272", "E275"]:  # Spacing around keywords
        line = lines[line_index]
        line = re.sub(r"\s{2,}(\w+)\b", r" \1", line)  # Fix multiple spaces before keywords
        lines[line_index] = line

    # Blank line errors
    elif error_type in ["E302", "E303", "E304", "E305"]:  # Blank lines
        if error_type in ["E302", "E305"]:  # Need more blank lines
            for _ in range(2):
                if error_type == "E302":
                    lines.insert(line_index, "")
                else:  # E305
                    if line_index + 1 < len(lines):
                        lines.insert(line_index + 1, "")
        elif error_type == "E303":  # Too many blank lines
            while (line_index > 0 and
                   line_index < len(lines) and
                   not lines[line_index - 1].strip() and
                   not lines[line_index - 2].strip() and
                   not lines[line_index - 3].strip()):
                lines.pop(line_index - 1)
                line_index -= 1

    elif error_type == "E402":  # Module level import not at top of file
        # Move import to top of file
        import_line = lines.pop(line_index)
        lines.insert(0, import_line)

    elif error_type in ["E701", "E702"]:  # Multiple statements on one line
        line = lines[line_index]
        if ";" in line:
            statements = line.split(";")
            indent = len(line) - len(line.lstrip())
            lines[line_index:line_index + 1] = [" " * indent + stmt.strip() for stmt in statements if stmt.strip()]

    elif error_type == "E721":  # Using type() instead of isinstance()
        line = lines[line_index]
        if "type(" in line:
            # This is a complex fix that might need manual intervention
            # Just add a comment suggesting the change
            lines[line_index] = line.rstrip() + "  # TODO: Consider using isinstance() instead of type()"

    elif error_type == "E741":  # Ambiguous variable name
        # Add a comment suggesting better variable naming
        lines[line_index] = lines[line_index].rstrip() + "  # TODO: Consider using a more descriptive variable name"

    elif error_type == "W191":  # Indentation contains tabs
        line = lines[line_index]
        indent = len(line) - len(line.lstrip())
        lines[line_index] = " " * indent + line.lstrip()

    elif error_type == "W391":  # Blank line at end of file
        while lines and not lines[-1].strip():
            lines.pop()

    elif error_type == "W605":  # Invalid escape sequence
        line = lines[line_index]
        # Add a comment about fixing the escape sequence
        lines[line_index] = line.rstrip() + "  # TODO: Fix invalid escape sequence"

    return "\n".join(lines)


def create_natural_language_description(error_type: str, message: str) -> str:
    """Convert flake8 error messages to natural language descriptions."""
    descriptions = {
        "F401": "There is an unused import in the file. The import should be removed to improve code readability and performance.",
        "E501": "The line exceeds the maximum length limit. It should be split into multiple lines for better readability.",
        "E251": "There are unnecessary spaces around the equals sign in a keyword parameter assignment. These spaces should be removed.",
        "E201": "There is extra whitespace after an opening parenthesis. The whitespace should be removed.",
        "E202": "There is extra whitespace before a closing parenthesis. The whitespace should be removed.",
        "E231": "A comma is not followed by a space. Add a space after the comma.",
        "E261": "There aren't enough spaces before an inline comment. At least two spaces are required.",
        "E271": "There are multiple spaces after a keyword. Only one space is allowed.",
        "E272": "There are multiple spaces before a keyword. Only one space is allowed.",
        "E302": "There aren't enough blank lines before this definition. Two blank lines are required.",
        "E303": "There are too many blank lines. Remove the excess blank lines.",
        "E305": "There aren't enough blank lines after the class/function definition. Two blank lines are required.",
        "W291": "The line contains trailing whitespace. Remove the extra spaces at the end.",
        "W293": "A blank line contains whitespace characters. The line should be completely empty.",
    }

    base_description = descriptions.get(error_type, message)
    return f"{base_description} (Error code: {error_type})"


def process_flake8_errors(input_data: List[Dict]) -> List[Dict]:
    """Process flake8 errors and create a clean dataset."""
    processed_data = []

    for error in input_data:
        if not error.get("code_snippet"):
            continue

        if len(error["code_snippet"].splitlines()) > 15:
            continue

        processed_entry = {
            "error_type": error["type"],
            "file_path": error["path"],
            "line_number": error["line"],
            "column": error["column"],
            "original_message": error["message"],
            "natural_language_description": create_natural_language_description(
                error["type"], error["message"]
            ),
            "original_code": normalize_code_snippet(error["code_snippet"]),
            "fixed_code": fix_code_snippet(
                error["code_snippet"], error["type"], error["line"], error["column"]
            ),
        }

        processed_data.append(processed_entry)

    return processed_data


def main():
    input_files = ["hummingbot_lint.json", "transformers_lint.json"]
    all_processed_data = []

    for input_file in input_files:
        try:
            with open(input_file, "r") as f:
                input_data = json.load(f)
            processed_data = process_flake8_errors(input_data)
            all_processed_data.extend(processed_data)
        except FileNotFoundError:
            print(f"Warning: Could not find {input_file}")
        except json.JSONDecodeError:
            print(f"Warning: Could not parse {input_file} as JSON")

    with open("processed_flake8_dataset.json", "w") as f:
        json.dump(all_processed_data, f, indent=2)

if __name__ == "__main__":
    main()
