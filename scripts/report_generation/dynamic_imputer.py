import pandas as pd
import numpy as np
import os
from linkbase_parser import parse_calculation_linkbase

def apply_dynamic_imputation(df, taxonomy_path=None):
    """
    Applies dynamic XBRL calculations to the DataFrame using the calculation linkbase.
    Fallback to a default taxonomy path if none is provided.
    """
    if taxonomy_path is None:
        taxonomy_path = os.path.join(
            os.path.dirname(__file__), '..', '..', 'data', 'taxonomy', 'in-capmkt-cal.xml'
        )
        
    calculations = parse_calculation_linkbase(taxonomy_path)
    
    if not calculations:
        return df

    for target, items in calculations.items():
        # First, ensure we have the items to sum
        for item, weight in items:
            if item not in df.columns:
                df[item] = 0.0
                
        # Calculate the sum
        computed_vals = pd.Series(0.0, index=df.index)
        for item, weight in items:
            # Ensure numeric type and fill NA with 0
            series = pd.to_numeric(df[item], errors='coerce').fillna(0.0)
            computed_vals += series * weight
            
        # Assign back to target if target is NA or 0
        if target not in df.columns:
            df[target] = computed_vals
        else:
            df[target] = pd.to_numeric(df[target], errors='coerce')
            df[target] = np.where(
                df[target].isna() | (df[target] == 0),
                computed_vals,
                df[target]
            )
            
        # Handle Previous Year data
        prev_target = f"{target} - Previous Year"
        computed_prev = pd.Series(0.0, index=df.index)
        
        has_prev = False
        for item, weight in items:
            prev_item = f"{item} - Previous Year"
            if prev_item in df.columns:
                has_prev = True
                series_prev = pd.to_numeric(df[prev_item], errors='coerce').fillna(0.0)
                computed_prev += series_prev * weight
                
        if has_prev:
            if prev_target not in df.columns:
                df[prev_target] = computed_prev
            else:
                df[prev_target] = pd.to_numeric(df[prev_target], errors='coerce')
                df[prev_target] = np.where(
                    df[prev_target].isna() | (df[prev_target] == 0),
                    computed_prev,
                    df[prev_target]
                )

    return df

if __name__ == "__main__":
    # Test script
    test_df = pd.DataFrame({
        'WaterDischargeToSurfaceWater': [10.5, np.nan],
        'WaterDischargeToGroundwater': [5.0, 3.0],
        'WaterDischargeToSurfaceWater - Previous Year': [8.0, 2.0],
        'WaterDischargeToGroundwater - Previous Year': [4.0, 1.0]
    })
    print("Before:\n", test_df)
    res_df = apply_dynamic_imputation(test_df)
    print("After:\n", res_df[['TotalWaterDischargedInKilolitres', 'TotalWaterDischargedInKilolitres - Previous Year']])
