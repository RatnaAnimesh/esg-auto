import pandas as pd
import argparse
import os
import json

def load_json_arg(arg_value):
    """
    Helper function to load JSON data.
    It can accept either a direct JSON string (useful for quick testing or API integration)
    or a file path to a .json file.
    """
    # Check if the argument looks like a JSON string (starts with '{' or '[')
    if arg_value.strip().startswith('{') or arg_value.strip().startswith('['):
        return json.loads(arg_value)
    else:
        # Otherwise, treat it as a file path and load the JSON from the file
        with open(arg_value, 'r') as f:
            return json.load(f)

def map_questions(brsr_file, questions_json_arg, mapping_json_arg, output_file):
    """
    Main function to process the BRSR dataset and map the specified questions
    to their corresponding columns based on the provided JSON mappings.
    """
    print(f"Loading BRSR data from {brsr_file}...")
    # Try-except block to handle potential errors when loading the BRSR CSV file.
    # This ensures the script exits gracefully if the file is missing or corrupted.
    try:
        df = pd.read_csv(brsr_file, low_memory=False)
    except Exception as e:
        print(f"Error loading BRSR file: {e}")
        return

    # Try-except block to load the questions JSON configuration safely.
    # If the JSON format is invalid or the file is not found, the script will stop and report the error.
    try:
        print("Loading questions JSON...")
        questions = load_json_arg(questions_json_arg)
    except Exception as e:
        print(f"Error loading questions JSON: {e}")
        return

    # Try-except block to load the mapping JSON configuration safely.
    # This catches errors in parsing or locating the mapping file.
    try:
        print("Loading mapping JSON...")
        mapping = load_json_arg(mapping_json_arg)
    except Exception as e:
        print(f"Error loading mapping JSON: {e}")
        return

    # Initialize a list to hold the processed data for each company
    results = []

    # Iterate row-by-row through the BRSR dataset (each row represents a company)
    for idx, row in df.iterrows():
        # Attempt to retrieve the company name using common column headers found in BRSR reports.
        # Fallback to a generic "Company <idx>" if the name isn't found.
        company_name = row.get("Company Name", row.get("Name Of The Listed Entity", f"Company {idx}"))
        
        # Initialize a dictionary to store the extracted data for the current company
        company_data = {"Company": company_name}
        
        # Iterate over the mapping JSON to extract the value for each question
        for key, column_name in mapping.items():
            # Determine the actual question text. 
            # If the questions JSON is a dictionary, fetch the text using the key.
            # If the text is missing or the questions JSON is just a list, default to using the key itself.
            if isinstance(questions, dict):
                question_text = questions.get(key, key)
            else:
                question_text = key
            
            # Map the question to the value in the BRSR CSV using the specified column name.
            # If the column name isn't found in the BRSR file, pandas will return pd.NA (Not Available).
            value = row.get(column_name, pd.NA)
            
            # Assign the extracted value to the corresponding question in the company's data dictionary
            company_data[question_text] = value
            
        # Append the processed company data to the results list
        results.append(company_data)

    # Try to create the output directory if it doesn't already exist
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    # Convert the processed results back into a pandas DataFrame and save it as a CSV file
    out_df = pd.DataFrame(results)
    out_df.to_csv(output_file, index=False)
    print(f"Mapping completed. Results saved to {output_file}")


if __name__ == "__main__":
    # Set up command-line argument parsing
    parser = argparse.ArgumentParser(description="Map questions to BRSR consolidated file based on JSON configurations")
    parser.add_argument("--brsr_file", type=str, required=True, help="Path to BRSR consolidated CSV")
    parser.add_argument("--questions_json", type=str, required=True, help="Path to JSON file or JSON string containing questions (e.g. {'q1': 'What is ...'})")
    parser.add_argument("--mapping_json", type=str, required=True, help="Path to JSON file or JSON string containing the mapping to Excel columns (e.g. {'q1': 'BRSR Column Name'})")
    parser.add_argument("--output_file", type=str, required=True, help="Path to output CSV")
    
    # Parse the arguments and trigger the mapping function
    args = parser.parse_args()
    map_questions(args.brsr_file, args.questions_json, args.mapping_json, args.output_file)
