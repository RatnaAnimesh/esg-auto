import pandas as pd
import numpy as np
import sys

def main():
    print("Loading datasets...")
    try:
        q_df = pd.read_csv('testing/synthetic/proxy_questionnaire.csv', index_col=0)
        brsr_df = pd.read_csv('testing/synthetic/mock_brsr_data.csv')
    except FileNotFoundError as e:
        print(f"Error loading files: {e}")
        sys.exit(1)

    # Extract the metadata formula row (it's the first row in q_df)
    metadata_row = q_df.iloc[0]
    
    # We will build a list of dictionaries to construct the final filled questionnaire
    filled_data = []

    print("\nExecuting Data Extraction Pipeline...")
    for idx, company_row in brsr_df.iterrows():
        company_name = company_row.get('Company_Name', f"Company_{idx+1}")
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
            if pd.isna(formula) or formula.strip() == "NONE":
                company_answers[question_col] = ""
                continue
            
            # Stage 2: Metadata Formula Fallback
            try:
                # Replace null/None values with np.nan to explicitly trigger math failures
                for k, v in context.items():
                    if pd.isna(v) or v is None:
                        context[k] = np.nan
                
                # Evaluate the string formula using the context dictionary
                result = pd.eval(formula, local_dict=context)
                
                # Check for NaNs or Inf (e.g. dividing by zero or adding a null)
                if pd.isna(result) or np.isinf(result):
                    raise ValueError("Missing or invalid data in BRSR calculation.")
                    
                company_answers[question_col] = round(result, 2)
                print(f"  [SUCCESS] {question_col}: {result:.2f}")
                
            except Exception as e:
                # Stage 3: Missing Data Handling (Terminal)
                company_answers[question_col] = "Undisclosed/Missing"
                print(f"  [FALLBACK TRIGGERED] {question_col}: Undisclosed/Missing")
                
        filled_data.append(company_answers)

    # Construct the final dataframe and merge it with the original questionnaire structure
    final_df = pd.DataFrame(filled_data)
    
    # Keep the metadata row at the top, then append the filled companies
    output_df = pd.concat([q_df.iloc[[0]], final_df.set_index('Question')])
    
    output_path = 'testing/synthetic/filled_questionnaire.csv'
    output_df.to_csv(output_path)
    print(f"\nSuccessfully executed pipeline and saved to {output_path}")

if __name__ == "__main__":
    main()
