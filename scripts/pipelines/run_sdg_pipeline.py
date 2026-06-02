import pandas as pd
import numpy as np
import sys
import argparse

def main():
    parser = argparse.ArgumentParser(description="Deterministic Math Extraction Engine")
    parser.add_argument("--questionnaire", type=str, required=True, help="Path to the questionnaire CSV template with Metadata formula row")
    parser.add_argument("--brsr_data", type=str, required=True, help="Path to the BRSR data CSV (consolidated or single company)")
    parser.add_argument("--output", type=str, default="data/processed/metadata/filled_questionnaire.csv", help="Path to save the output CSV")
    args = parser.parse_args()

    print("Loading datasets...")
    try:
        q_df = pd.read_csv(args.questionnaire, index_col=0)
        brsr_df = pd.read_csv(args.brsr_data)
    except FileNotFoundError as e:
        print(f"Error loading files: {e}")
        sys.exit(1)

    # If the BRSR data has 'Metric' as index and one column 'Value' (like individual company CSVs), 
    # we need to transpose it so columns are metrics.
    if 'Metric' in brsr_df.columns and 'Value' in brsr_df.columns:
        company_name = brsr_df[brsr_df['Metric'] == 'CompanyName']['Value'].values[0]
        brsr_df = brsr_df.set_index('Metric').T
        brsr_df['Company_Name'] = company_name

    # Extract the metadata formula row (it's the first row in q_df)
    metadata_row = q_df.iloc[0]
    
    # We will build a list of dictionaries to construct the final filled questionnaire
    filled_data = []

    print("\nExecuting Data Extraction Pipeline...")
    for idx, company_row in brsr_df.iterrows():
        company_name = company_row.get('Company_Name', company_row.get('CompanyName', f"Company_{str(idx)}"))
        print(f"\nProcessing {company_name}...")
        
        # Prepare a context dictionary for pandas.eval containing the company's BRSR data
        context = company_row.to_dict()
        
        # This will hold the answers for this specific company
        company_answers = {"Question": company_name, "Company_Name": company_name}
        
        # Iterate over all the actual ESG questions in the questionnaire
        # Skip the first column (Company_Name) since it's just the label
        for question_col in q_df.columns[1:]:
            formula = metadata_row[question_col]
            
            # Simulated Logic Tree
            if pd.isna(formula) or str(formula).strip() == "NONE":
                company_answers[question_col] = ""
                continue
            
            formula_str = str(formula)
            
                # Stage 2: Metadata Formula Fallback
            try:
                eval_str = formula_str
                # Sort keys by length descending to prevent partial string matches
                for k in sorted(context.keys(), key=lambda x: len(str(x)), reverse=True):
                    k_str = str(k)
                    if k_str in eval_str:
                        val = context[k]
                        if pd.isna(val) or val is None:
                            eval_str = eval_str.replace(k_str, 'np.nan')
                        else:
                            try:
                                # Try to treat as float for math operations
                                val_num = float(val)
                                eval_str = eval_str.replace(k_str, str(val_num))
                            except ValueError:
                                # Wrap strings in quotes for eval
                                # Escape internal quotes
                                safe_val = str(val).replace("'", "\\'")
                                eval_str = eval_str.replace(k_str, f"'{safe_val}'")
                
                # Evaluate the string formula using python's built-in eval
                # We provide an empty globals dict for safety, but allow np and str methods
                result = eval(eval_str, {"np": np, "pd": pd}, {})
                
                # If the result is a number, format it
                if isinstance(result, (int, float)):
                    if pd.isna(result) or np.isinf(result):
                        raise ValueError("Missing or invalid data in BRSR calculation.")
                    company_answers[question_col] = round(result, 2)
                    print(f"  [SUCCESS] {question_col}: {result:.2f}")
                else:
                    # It's a string or boolean
                    company_answers[question_col] = str(result)
                    print(f"  [SUCCESS] {question_col}: {result}")
                    
            except Exception as e:
                # Stage 3: Missing Data Handling (Terminal)
                company_answers[question_col] = "Undisclosed/Missing"
                print(f"  [FALLBACK TRIGGERED] {question_col}: Undisclosed/Missing (Error: {e})")
                
        filled_data.append(company_answers)

    # Construct the final dataframe and merge it with the original questionnaire structure
    final_df = pd.DataFrame(filled_data)
    
    # Keep the metadata row at the top, then append the filled companies
    output_df = pd.concat([q_df.iloc[[0]], final_df.set_index('Question')])
    
    output_df.to_csv(args.output)
    print(f"\nSuccessfully executed pipeline and saved to {args.output}")

if __name__ == "__main__":
    main()
