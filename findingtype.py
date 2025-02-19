import json


def extract_error_types(json_file):
    """
    Extracts all unique 'type' values from a JSON file.

    Args:
        json_file (str): Path to the JSON file.

    Returns:
        set: A set of unique error types.
    """
    try:
        with open(json_file, "r") as file:
            data = json.load(file)
            # Extract all 'type' fields from the JSON objects
            error_types = {item.get("type") for item in data if "type" in item}
            return error_types
    except FileNotFoundError:
        print(f"Error: File '{json_file}' not found.")
        return set()
    except json.JSONDecodeError:
        print(f"Error: Failed to decode JSON from file '{json_file}'.")
        return set()


def main():
    # Paths to the JSON files
    file_a = "hummingbot_lint.json"
    file_b = "transformers_lint.json"

    # Extract error types from both files
    error_types_a = extract_error_types(file_a)
    error_types_b = extract_error_types(file_b)

    # Combine the error types from both files into a single set
    all_error_types = error_types_a.union(error_types_b)

    # Convert the set to a sorted list for readability
    sorted_error_types = sorted(all_error_types)

    # Print the result
    print("List of all unique error types:")
    for error_type in sorted_error_types:
        print(error_type)


if __name__ == "__main__":
    main()
