import re

# Dictionary mapping a derived metric to its formula.
# You can use standard Python math operators (+, -, *, /).
# Enclose exact column names in curly braces {}.
# Note: For PPP, we're using a standard factor (e.g., 22.9 INR to PPP USD for 2022).
IMPUTATION_RULES = {
    "Total Scope1 And Scope2 Emissions Intensity Per Rupee Of Turnover": 
        "({Total Scope1 Emissions} + {Total Scope2 Emissions}) / {Revenue From Operations}",
        
    "Total Scope1 And Scope2 Emissions Intensity Per Rupee Of Turnover Adjusted For Purchasing Power Parity":
        "(({Total Scope1 Emissions} + {Total Scope2 Emissions}) / {Revenue From Operations}) * 22.9",
    "Number Of Locations - Plant Member - National Member": "0",
    "Number Of Locations - Office Member - National Member": "0",
    "Number Of Locations - Location Member - National Member":
        "{Number Of Locations - Plant Member - National Member} + {Number Of Locations - Office Member - National Member}",
    "Number Of Locations - Plant Member - International Member": "0",
    "Number Of Locations - Office Member - International Member": "0",
    "Number Of Locations - Location Member - International Member":
        "{Number Of Locations - Plant Member - International Member} + {Number Of Locations - Office Member - International Member}",
    "Number Of States Where Market Served By The Entity": "0",
    "Number Of Countries Where Market Served By The Entity": "0",
    "Percentage Of Contribution Of Exports In The Total Turnover Of The Entity": "0",
    "Number Of Employees Or Workers Including Differently Abled - Gender Member - Permanent Employees Member":
        "{Number Of Employees Or Workers Including Differently Abled - Male Member - Permanent Employees Member} + {Number Of Employees Or Workers Including Differently Abled - Female Member - Permanent Employees Member} + {Number Of Employees Or Workers Including Differently Abled - Other Gender Member - Permanent Employees Member}",
    "Number Of Employees Or Workers Including Differently Abled - Male Member - Permanent Employees Member":
        "{Number Of Employees Or Workers Including Differently Abled - Gender Member - Permanent Employees Member} - {Number Of Employees Or Workers Including Differently Abled - Female Member - Permanent Employees Member} - {Number Of Employees Or Workers Including Differently Abled - Other Gender Member - Permanent Employees Member}",
    "Percentage Of Employees Or Workers Including Differently Abled - Male Member - Permanent Employees Member":
        "({Number Of Employees Or Workers Including Differently Abled - Male Member - Permanent Employees Member} / {Number Of Employees Or Workers Including Differently Abled - Gender Member - Permanent Employees Member}) * 100",
    "Number Of Employees Or Workers Including Differently Abled - Female Member - Permanent Employees Member":
        "{Number Of Employees Or Workers Including Differently Abled - Gender Member - Permanent Employees Member} - {Number Of Employees Or Workers Including Differently Abled - Male Member - Permanent Employees Member} - {Number Of Employees Or Workers Including Differently Abled - Other Gender Member - Permanent Employees Member}",
    "Percentage Of Employees Or Workers Including Differently Abled - Female Member - Permanent Employees Member":
        "({Number Of Employees Or Workers Including Differently Abled - Female Member - Permanent Employees Member} / {Number Of Employees Or Workers Including Differently Abled - Gender Member - Permanent Employees Member}) * 100",
    "Number Of Employees Or Workers Including Differently Abled - Other Gender Member - Permanent Employees Member":
        "{Number Of Employees Or Workers Including Differently Abled - Gender Member - Permanent Employees Member} - {Number Of Employees Or Workers Including Differently Abled - Male Member - Permanent Employees Member} - {Number Of Employees Or Workers Including Differently Abled - Female Member - Permanent Employees Member}",
    "Percentage Of Employees Or Workers Including Differently Abled - Other Gender Member - Permanent Employees Member":
        "({Number Of Employees Or Workers Including Differently Abled - Other Gender Member - Permanent Employees Member} / {Number Of Employees Or Workers Including Differently Abled - Gender Member - Permanent Employees Member}) * 100",
    "Number Of Employees Or Workers Including Differently Abled - Gender Member - Other Than Permanent Employees Member":
        "{Number Of Employees Or Workers Including Differently Abled - Male Member - Other Than Permanent Employees Member} + {Number Of Employees Or Workers Including Differently Abled - Female Member - Other Than Permanent Employees Member} + {Number Of Employees Or Workers Including Differently Abled - Other Gender Member - Other Than Permanent Employees Member}",
    "Number Of Employees Or Workers Including Differently Abled - Male Member - Other Than Permanent Employees Member":
        "{Number Of Employees Or Workers Including Differently Abled - Gender Member - Other Than Permanent Employees Member} - {Number Of Employees Or Workers Including Differently Abled - Female Member - Other Than Permanent Employees Member} - {Number Of Employees Or Workers Including Differently Abled - Other Gender Member - Other Than Permanent Employees Member}",
    "Percentage Of Employees Or Workers Including Differently Abled - Male Member - Other Than Permanent Employees Member":
        "({Number Of Employees Or Workers Including Differently Abled - Male Member - Other Than Permanent Employees Member} / {Number Of Employees Or Workers Including Differently Abled - Gender Member - Other Than Permanent Employees Member}) * 100",
    "Number Of Employees Or Workers Including Differently Abled - Female Member - Other Than Permanent Employees Member":
        "{Number Of Employees Or Workers Including Differently Abled - Gender Member - Other Than Permanent Employees Member} - {Number Of Employees Or Workers Including Differently Abled - Male Member - Other Than Permanent Employees Member} - {Number Of Employees Or Workers Including Differently Abled - Other Gender Member - Other Than Permanent Employees Member}",
    "Percentage Of Employees Or Workers Including Differently Abled - Female Member - Other Than Permanent Employees Member":
        "({Number Of Employees Or Workers Including Differently Abled - Female Member - Other Than Permanent Employees Member} / {Number Of Employees Or Workers Including Differently Abled - Gender Member - Other Than Permanent Employees Member}) * 100",
    "Number Of Employees Or Workers Including Differently Abled - Other Gender Member - Other Than Permanent Employees Member":
        "{Number Of Employees Or Workers Including Differently Abled - Gender Member - Other Than Permanent Employees Member} - {Number Of Employees Or Workers Including Differently Abled - Male Member - Other Than Permanent Employees Member} - {Number Of Employees Or Workers Including Differently Abled - Female Member - Other Than Permanent Employees Member}",
    "Percentage Of Employees Or Workers Including Differently Abled - Other Gender Member - Other Than Permanent Employees Member":
        "({Number Of Employees Or Workers Including Differently Abled - Other Gender Member - Other Than Permanent Employees Member} / {Number Of Employees Or Workers Including Differently Abled - Gender Member - Other Than Permanent Employees Member}) * 100",
    "Number Of Employees Or Workers Including Differently Abled - Gender Member - Employees Member":
        "{Number Of Employees Or Workers Including Differently Abled - Male Member - Employees Member} + {Number Of Employees Or Workers Including Differently Abled - Female Member - Employees Member} + {Number Of Employees Or Workers Including Differently Abled - Other Gender Member - Employees Member}",
    "Number Of Employees Or Workers Including Differently Abled - Male Member - Employees Member":
        "{Number Of Employees Or Workers Including Differently Abled - Gender Member - Employees Member} - {Number Of Employees Or Workers Including Differently Abled - Female Member - Employees Member} - {Number Of Employees Or Workers Including Differently Abled - Other Gender Member - Employees Member}",
    "Percentage Of Employees Or Workers Including Differently Abled - Male Member - Employees Member":
        "({Number Of Employees Or Workers Including Differently Abled - Male Member - Employees Member} / {Number Of Employees Or Workers Including Differently Abled - Gender Member - Employees Member}) * 100",
    "Number Of Employees Or Workers Including Differently Abled - Female Member - Employees Member":
        "{Number Of Employees Or Workers Including Differently Abled - Gender Member - Employees Member} - {Number Of Employees Or Workers Including Differently Abled - Male Member - Employees Member} - {Number Of Employees Or Workers Including Differently Abled - Other Gender Member - Employees Member}",
    "Percentage Of Employees Or Workers Including Differently Abled - Female Member - Employees Member":
        "({Number Of Employees Or Workers Including Differently Abled - Female Member - Employees Member} / {Number Of Employees Or Workers Including Differently Abled - Gender Member - Employees Member}) * 100",
    "Number Of Employees Or Workers Including Differently Abled - Other Gender Member - Employees Member":
        "{Number Of Employees Or Workers Including Differently Abled - Gender Member - Employees Member} - {Number Of Employees Or Workers Including Differently Abled - Male Member - Employees Member} - {Number Of Employees Or Workers Including Differently Abled - Female Member - Employees Member}",
    "Percentage Of Employees Or Workers Including Differently Abled - Other Gender Member - Employees Member":
        "({Number Of Employees Or Workers Including Differently Abled - Other Gender Member - Employees Member} / {Number Of Employees Or Workers Including Differently Abled - Gender Member - Employees Member}) * 100",
    "Number Of Employees Or Workers Including Differently Abled - Gender Member - Permanent Workers Member":
        "{Number Of Employees Or Workers Including Differently Abled - Male Member - Permanent Workers Member} + {Number Of Employees Or Workers Including Differently Abled - Female Member - Permanent Workers Member} + {Number Of Employees Or Workers Including Differently Abled - Other Gender Member - Permanent Workers Member}",
    "Number Of Employees Or Workers Including Differently Abled - Male Member - Permanent Workers Member":
        "{Number Of Employees Or Workers Including Differently Abled - Gender Member - Permanent Workers Member} - {Number Of Employees Or Workers Including Differently Abled - Female Member - Permanent Workers Member} - {Number Of Employees Or Workers Including Differently Abled - Other Gender Member - Permanent Workers Member}",
    "Percentage Of Employees Or Workers Including Differently Abled - Male Member - Permanent Workers Member":
        "({Number Of Employees Or Workers Including Differently Abled - Male Member - Permanent Workers Member} / {Number Of Employees Or Workers Including Differently Abled - Gender Member - Permanent Workers Member}) * 100",
    "Number Of Employees Or Workers Including Differently Abled - Female Member - Permanent Workers Member":
        "{Number Of Employees Or Workers Including Differently Abled - Gender Member - Permanent Workers Member} - {Number Of Employees Or Workers Including Differently Abled - Male Member - Permanent Workers Member} - {Number Of Employees Or Workers Including Differently Abled - Other Gender Member - Permanent Workers Member}",
    "Percentage Of Employees Or Workers Including Differently Abled - Female Member - Permanent Workers Member":
        "({Number Of Employees Or Workers Including Differently Abled - Female Member - Permanent Workers Member} / {Number Of Employees Or Workers Including Differently Abled - Gender Member - Permanent Workers Member}) * 100",
    "Number Of Employees Or Workers Including Differently Abled - Other Gender Member - Permanent Workers Member":
        "{Number Of Employees Or Workers Including Differently Abled - Gender Member - Permanent Workers Member} - {Number Of Employees Or Workers Including Differently Abled - Male Member - Permanent Workers Member} - {Number Of Employees Or Workers Including Differently Abled - Female Member - Permanent Workers Member}",
    "Percentage Of Employees Or Workers Including Differently Abled - Other Gender Member - Permanent Workers Member":
        "({Number Of Employees Or Workers Including Differently Abled - Other Gender Member - Permanent Workers Member} / {Number Of Employees Or Workers Including Differently Abled - Gender Member - Permanent Workers Member}) * 100",
    "Number Of Employees Or Workers Including Differently Abled - Gender Member - Other Than Permanent Workers Member":
        "{Number Of Employees Or Workers Including Differently Abled - Male Member - Other Than Permanent Workers Member} + {Number Of Employees Or Workers Including Differently Abled - Female Member - Other Than Permanent Workers Member} + {Number Of Employees Or Workers Including Differently Abled - Other Gender Member - Other Than Permanent Workers Member}",
    "Number Of Employees Or Workers Including Differently Abled - Male Member - Other Than Permanent Workers Member":
        "{Number Of Employees Or Workers Including Differently Abled - Gender Member - Other Than Permanent Workers Member} - {Number Of Employees Or Workers Including Differently Abled - Female Member - Other Than Permanent Workers Member} - {Number Of Employees Or Workers Including Differently Abled - Other Gender Member - Other Than Permanent Workers Member}",
    "Percentage Of Employees Or Workers Including Differently Abled - Male Member - Other Than Permanent Workers Member":
        "({Number Of Employees Or Workers Including Differently Abled - Male Member - Other Than Permanent Workers Member} / {Number Of Employees Or Workers Including Differently Abled - Gender Member - Other Than Permanent Workers Member}) * 100",
    "Number Of Employees Or Workers Including Differently Abled - Female Member - Other Than Permanent Workers Member":
        "{Number Of Employees Or Workers Including Differently Abled - Gender Member - Other Than Permanent Workers Member} - {Number Of Employees Or Workers Including Differently Abled - Male Member - Other Than Permanent Workers Member} - {Number Of Employees Or Workers Including Differently Abled - Other Gender Member - Other Than Permanent Workers Member}",
    "Percentage Of Employees Or Workers Including Differently Abled - Female Member - Other Than Permanent Workers Member":
        "({Number Of Employees Or Workers Including Differently Abled - Female Member - Other Than Permanent Workers Member} / {Number Of Employees Or Workers Including Differently Abled - Gender Member - Other Than Permanent Workers Member}) * 100",
    "Number Of Employees Or Workers Including Differently Abled - Other Gender Member - Other Than Permanent Workers Member":
        "{Number Of Employees Or Workers Including Differently Abled - Gender Member - Other Than Permanent Workers Member} - {Number Of Employees Or Workers Including Differently Abled - Male Member - Other Than Permanent Workers Member} - {Number Of Employees Or Workers Including Differently Abled - Female Member - Other Than Permanent Workers Member}",
    "Percentage Of Employees Or Workers Including Differently Abled - Other Gender Member - Other Than Permanent Workers Member":
        "({Number Of Employees Or Workers Including Differently Abled - Other Gender Member - Other Than Permanent Workers Member} / {Number Of Employees Or Workers Including Differently Abled - Gender Member - Other Than Permanent Workers Member}) * 100",
    "Number Of Employees Or Workers Including Differently Abled - Gender Member - Workers Member":
        "{Number Of Employees Or Workers Including Differently Abled - Male Member - Workers Member} + {Number Of Employees Or Workers Including Differently Abled - Female Member - Workers Member} + {Number Of Employees Or Workers Including Differently Abled - Other Gender Member - Workers Member}",
    "Number Of Employees Or Workers Including Differently Abled - Male Member - Workers Member":
        "{Number Of Employees Or Workers Including Differently Abled - Gender Member - Workers Member} - {Number Of Employees Or Workers Including Differently Abled - Female Member - Workers Member} - {Number Of Employees Or Workers Including Differently Abled - Other Gender Member - Workers Member}",
    "Percentage Of Employees Or Workers Including Differently Abled - Male Member - Workers Member":
        "({Number Of Employees Or Workers Including Differently Abled - Male Member - Workers Member} / {Number Of Employees Or Workers Including Differently Abled - Gender Member - Workers Member}) * 100",
    "Number Of Employees Or Workers Including Differently Abled - Female Member - Workers Member":
        "{Number Of Employees Or Workers Including Differently Abled - Gender Member - Workers Member} - {Number Of Employees Or Workers Including Differently Abled - Male Member - Workers Member} - {Number Of Employees Or Workers Including Differently Abled - Other Gender Member - Workers Member}",
    "Percentage Of Employees Or Workers Including Differently Abled - Female Member - Workers Member":
        "({Number Of Employees Or Workers Including Differently Abled - Female Member - Workers Member} / {Number Of Employees Or Workers Including Differently Abled - Gender Member - Workers Member}) * 100",
    "Number Of Employees Or Workers Including Differently Abled - Other Gender Member - Workers Member":
        "{Number Of Employees Or Workers Including Differently Abled - Gender Member - Workers Member} - {Number Of Employees Or Workers Including Differently Abled - Male Member - Workers Member} - {Number Of Employees Or Workers Including Differently Abled - Female Member - Workers Member}",
    "Percentage Of Employees Or Workers Including Differently Abled - Other Gender Member - Workers Member":
        "({Number Of Employees Or Workers Including Differently Abled - Other Gender Member - Workers Member} / {Number Of Employees Or Workers Including Differently Abled - Gender Member - Workers Member}) * 100",
    "Number Of Differently Abled Employees Or Workers - Gender Member - Permanent Employees Member":
        "{Number Of Differently Abled Employees Or Workers - Male Member - Permanent Employees Member} + {Number Of Differently Abled Employees Or Workers - Female Member - Permanent Employees Member} + {Number Of Differently Abled Employees Or Workers - Other Gender Member - Permanent Employees Member}",
    "Number Of Differently Abled Employees Or Workers - Male Member - Permanent Employees Member":
        "{Number Of Differently Abled Employees Or Workers - Gender Member - Permanent Employees Member} - {Number Of Differently Abled Employees Or Workers - Female Member - Permanent Employees Member} - {Number Of Differently Abled Employees Or Workers - Other Gender Member - Permanent Employees Member}",
    "Percentage Of Differently Abled Employees Or Workers - Male Member - Permanent Employees Member":
        "({Number Of Differently Abled Employees Or Workers - Male Member - Permanent Employees Member} / {Number Of Differently Abled Employees Or Workers - Gender Member - Permanent Employees Member}) * 100",
    "Number Of Differently Abled Employees Or Workers - Female Member - Permanent Employees Member":
        "{Number Of Differently Abled Employees Or Workers - Gender Member - Permanent Employees Member} - {Number Of Differently Abled Employees Or Workers - Male Member - Permanent Employees Member} - {Number Of Differently Abled Employees Or Workers - Other Gender Member - Permanent Employees Member}",
    "Percentage Of Differently Abled Employees Or Workers - Female Member - Permanent Employees Member":
        "({Number Of Differently Abled Employees Or Workers - Female Member - Permanent Employees Member} / {Number Of Differently Abled Employees Or Workers - Gender Member - Permanent Employees Member}) * 100",
    "Number Of Differently Abled Employees Or Workers - Other Gender Member - Permanent Employees Member":
        "{Number Of Differently Abled Employees Or Workers - Gender Member - Permanent Employees Member} - {Number Of Differently Abled Employees Or Workers - Male Member - Permanent Employees Member} - {Number Of Differently Abled Employees Or Workers - Female Member - Permanent Employees Member}",
    "Percentage Of Differently Abled Employees Or Workers - Other Gender Member - Permanent Employees Member":
        "({Number Of Differently Abled Employees Or Workers - Other Gender Member - Permanent Employees Member} / {Number Of Differently Abled Employees Or Workers - Gender Member - Permanent Employees Member}) * 100",
    "Number Of Differently Abled Employees Or Workers - Gender Member - Other Than Permanent Employees Member":
        "{Number Of Differently Abled Employees Or Workers - Male Member - Other Than Permanent Employees Member} + {Number Of Differently Abled Employees Or Workers - Female Member - Other Than Permanent Employees Member} + {Number Of Differently Abled Employees Or Workers - Other Gender Member - Other Than Permanent Employees Member}",
    "Number Of Differently Abled Employees Or Workers - Male Member - Other Than Permanent Employees Member":
        "{Number Of Differently Abled Employees Or Workers - Gender Member - Other Than Permanent Employees Member} - {Number Of Differently Abled Employees Or Workers - Female Member - Other Than Permanent Employees Member} - {Number Of Differently Abled Employees Or Workers - Other Gender Member - Other Than Permanent Employees Member}",
    "Percentage Of Differently Abled Employees Or Workers - Male Member - Other Than Permanent Employees Member":
        "({Number Of Differently Abled Employees Or Workers - Male Member - Other Than Permanent Employees Member} / {Number Of Differently Abled Employees Or Workers - Gender Member - Other Than Permanent Employees Member}) * 100",
    "Number Of Differently Abled Employees Or Workers - Female Member - Other Than Permanent Employees Member":
        "{Number Of Differently Abled Employees Or Workers - Gender Member - Other Than Permanent Employees Member} - {Number Of Differently Abled Employees Or Workers - Male Member - Other Than Permanent Employees Member} - {Number Of Differently Abled Employees Or Workers - Other Gender Member - Other Than Permanent Employees Member}",
    "Percentage Of Differently Abled Employees Or Workers - Female Member - Other Than Permanent Employees Member":
        "({Number Of Differently Abled Employees Or Workers - Female Member - Other Than Permanent Employees Member} / {Number Of Differently Abled Employees Or Workers - Gender Member - Other Than Permanent Employees Member}) * 100",
    "Number Of Differently Abled Employees Or Workers - Other Gender Member - Other Than Permanent Employees Member":
        "{Number Of Differently Abled Employees Or Workers - Gender Member - Other Than Permanent Employees Member} - {Number Of Differently Abled Employees Or Workers - Male Member - Other Than Permanent Employees Member} - {Number Of Differently Abled Employees Or Workers - Female Member - Other Than Permanent Employees Member}",
    "Percentage Of Differently Abled Employees Or Workers - Other Gender Member - Other Than Permanent Employees Member":
        "({Number Of Differently Abled Employees Or Workers - Other Gender Member - Other Than Permanent Employees Member} / {Number Of Differently Abled Employees Or Workers - Gender Member - Other Than Permanent Employees Member}) * 100",
    "Number Of Differently Abled Employees Or Workers - Gender Member - Employees Member":
        "{Number Of Differently Abled Employees Or Workers - Male Member - Employees Member} + {Number Of Differently Abled Employees Or Workers - Female Member - Employees Member} + {Number Of Differently Abled Employees Or Workers - Other Gender Member - Employees Member}",
    "Number Of Differently Abled Employees Or Workers - Male Member - Employees Member":
        "{Number Of Differently Abled Employees Or Workers - Gender Member - Employees Member} - {Number Of Differently Abled Employees Or Workers - Female Member - Employees Member} - {Number Of Differently Abled Employees Or Workers - Other Gender Member - Employees Member}",
    "Percentage Of Differently Abled Employees Or Workers - Male Member - Employees Member":
        "({Number Of Differently Abled Employees Or Workers - Male Member - Employees Member} / {Number Of Differently Abled Employees Or Workers - Gender Member - Employees Member}) * 100",
    "Number Of Differently Abled Employees Or Workers - Female Member - Employees Member":
        "{Number Of Differently Abled Employees Or Workers - Gender Member - Employees Member} - {Number Of Differently Abled Employees Or Workers - Male Member - Employees Member} - {Number Of Differently Abled Employees Or Workers - Other Gender Member - Employees Member}",
    "Percentage Of Differently Abled Employees Or Workers - Female Member - Employees Member":
        "({Number Of Differently Abled Employees Or Workers - Female Member - Employees Member} / {Number Of Differently Abled Employees Or Workers - Gender Member - Employees Member}) * 100",
    "Number Of Differently Abled Employees Or Workers - Other Gender Member - Employees Member":
        "{Number Of Differently Abled Employees Or Workers - Gender Member - Employees Member} - {Number Of Differently Abled Employees Or Workers - Male Member - Employees Member} - {Number Of Differently Abled Employees Or Workers - Female Member - Employees Member}",
    "Percentage Of Differently Abled Employees Or Workers - Other Gender Member - Employees Member":
        "({Number Of Differently Abled Employees Or Workers - Other Gender Member - Employees Member} / {Number Of Differently Abled Employees Or Workers - Gender Member - Employees Member}) * 100",
    "Number Of Differently Abled Employees Or Workers - Gender Member - Permanent Workers Member":
        "{Number Of Differently Abled Employees Or Workers - Male Member - Permanent Workers Member} + {Number Of Differently Abled Employees Or Workers - Female Member - Permanent Workers Member} + {Number Of Differently Abled Employees Or Workers - Other Gender Member - Permanent Workers Member}",
    "Number Of Differently Abled Employees Or Workers - Male Member - Permanent Workers Member":
        "{Number Of Differently Abled Employees Or Workers - Gender Member - Permanent Workers Member} - {Number Of Differently Abled Employees Or Workers - Female Member - Permanent Workers Member} - {Number Of Differently Abled Employees Or Workers - Other Gender Member - Permanent Workers Member}",
    "Percentage Of Differently Abled Employees Or Workers - Male Member - Permanent Workers Member":
        "({Number Of Differently Abled Employees Or Workers - Male Member - Permanent Workers Member} / {Number Of Differently Abled Employees Or Workers - Gender Member - Permanent Workers Member}) * 100",
    "Number Of Differently Abled Employees Or Workers - Female Member - Permanent Workers Member":
        "{Number Of Differently Abled Employees Or Workers - Gender Member - Permanent Workers Member} - {Number Of Differently Abled Employees Or Workers - Male Member - Permanent Workers Member} - {Number Of Differently Abled Employees Or Workers - Other Gender Member - Permanent Workers Member}",
    "Percentage Of Differently Abled Employees Or Workers - Female Member - Permanent Workers Member":
        "({Number Of Differently Abled Employees Or Workers - Female Member - Permanent Workers Member} / {Number Of Differently Abled Employees Or Workers - Gender Member - Permanent Workers Member}) * 100",
    "Number Of Differently Abled Employees Or Workers - Other Gender Member - Permanent Workers Member":
        "{Number Of Differently Abled Employees Or Workers - Gender Member - Permanent Workers Member} - {Number Of Differently Abled Employees Or Workers - Male Member - Permanent Workers Member} - {Number Of Differently Abled Employees Or Workers - Female Member - Permanent Workers Member}",
    "Percentage Of Differently Abled Employees Or Workers - Other Gender Member - Permanent Workers Member":
        "({Number Of Differently Abled Employees Or Workers - Other Gender Member - Permanent Workers Member} / {Number Of Differently Abled Employees Or Workers - Gender Member - Permanent Workers Member}) * 100",
    "Number Of Differently Abled Employees Or Workers - Gender Member - Other Than Permanent Workers Member":
        "{Number Of Differently Abled Employees Or Workers - Male Member - Other Than Permanent Workers Member} + {Number Of Differently Abled Employees Or Workers - Female Member - Other Than Permanent Workers Member} + {Number Of Differently Abled Employees Or Workers - Other Gender Member - Other Than Permanent Workers Member}",
    "Number Of Differently Abled Employees Or Workers - Male Member - Other Than Permanent Workers Member":
        "{Number Of Differently Abled Employees Or Workers - Gender Member - Other Than Permanent Workers Member} - {Number Of Differently Abled Employees Or Workers - Female Member - Other Than Permanent Workers Member} - {Number Of Differently Abled Employees Or Workers - Other Gender Member - Other Than Permanent Workers Member}",
    "Percentage Of Differently Abled Employees Or Workers - Male Member - Other Than Permanent Workers Member":
        "({Number Of Differently Abled Employees Or Workers - Male Member - Other Than Permanent Workers Member} / {Number Of Differently Abled Employees Or Workers - Gender Member - Other Than Permanent Workers Member}) * 100",
    "Number Of Differently Abled Employees Or Workers - Female Member - Other Than Permanent Workers Member":
        "{Number Of Differently Abled Employees Or Workers - Gender Member - Other Than Permanent Workers Member} - {Number Of Differently Abled Employees Or Workers - Male Member - Other Than Permanent Workers Member} - {Number Of Differently Abled Employees Or Workers - Other Gender Member - Other Than Permanent Workers Member}",
    "Percentage Of Differently Abled Employees Or Workers - Female Member - Other Than Permanent Workers Member":
        "({Number Of Differently Abled Employees Or Workers - Female Member - Other Than Permanent Workers Member} / {Number Of Differently Abled Employees Or Workers - Gender Member - Other Than Permanent Workers Member}) * 100",
    "Number Of Differently Abled Employees Or Workers - Other Gender Member - Other Than Permanent Workers Member":
        "{Number Of Differently Abled Employees Or Workers - Gender Member - Other Than Permanent Workers Member} - {Number Of Differently Abled Employees Or Workers - Male Member - Other Than Permanent Workers Member} - {Number Of Differently Abled Employees Or Workers - Female Member - Other Than Permanent Workers Member}",
    "Percentage Of Differently Abled Employees Or Workers - Other Gender Member - Other Than Permanent Workers Member":
        "({Number Of Differently Abled Employees Or Workers - Other Gender Member - Other Than Permanent Workers Member} / {Number Of Differently Abled Employees Or Workers - Gender Member - Other Than Permanent Workers Member}) * 100",
    "Number Of Differently Abled Employees Or Workers - Gender Member - Workers Member":
        "{Number Of Differently Abled Employees Or Workers - Male Member - Workers Member} + {Number Of Differently Abled Employees Or Workers - Female Member - Workers Member} + {Number Of Differently Abled Employees Or Workers - Other Gender Member - Workers Member}",
    "Number Of Differently Abled Employees Or Workers - Male Member - Workers Member":
        "{Number Of Differently Abled Employees Or Workers - Gender Member - Workers Member} - {Number Of Differently Abled Employees Or Workers - Female Member - Workers Member} - {Number Of Differently Abled Employees Or Workers - Other Gender Member - Workers Member}",
    "Percentage Of Differently Abled Employees Or Workers - Male Member - Workers Member":
        "({Number Of Differently Abled Employees Or Workers - Male Member - Workers Member} / {Number Of Differently Abled Employees Or Workers - Gender Member - Workers Member}) * 100",
    "Number Of Differently Abled Employees Or Workers - Female Member - Workers Member":
        "{Number Of Differently Abled Employees Or Workers - Gender Member - Workers Member} - {Number Of Differently Abled Employees Or Workers - Male Member - Workers Member} - {Number Of Differently Abled Employees Or Workers - Other Gender Member - Workers Member}",
    "Percentage Of Differently Abled Employees Or Workers - Female Member - Workers Member":
        "({Number Of Differently Abled Employees Or Workers - Female Member - Workers Member} / {Number Of Differently Abled Employees Or Workers - Gender Member - Workers Member}) * 100",
    "Number Of Differently Abled Employees Or Workers - Other Gender Member - Workers Member":
        "{Number Of Differently Abled Employees Or Workers - Gender Member - Workers Member} - {Number Of Differently Abled Employees Or Workers - Male Member - Workers Member} - {Number Of Differently Abled Employees Or Workers - Female Member - Workers Member}",
    "Percentage Of Differently Abled Employees Or Workers - Other Gender Member - Workers Member":
        "({Number Of Differently Abled Employees Or Workers - Other Gender Member - Workers Member} / {Number Of Differently Abled Employees Or Workers - Gender Member - Workers Member}) * 100",
    "Number Of Female Board Of Directors": "0",
    "Percentage Of Female Board Of Directors": "0",
    "Total Number Of Key Management Personnel": "0",
    "Number Of Female Key Management Personnel": "0",
    "Percentage Of Female Key Management Personnel": "0",
    "Turnover Rate - Male Member - Permanent Employees Member": "0",
    "Turnover Rate - Female Member - Permanent Employees Member": "0",
    "Turnover Rate - Other Gender Member - Permanent Employees Member": "0",
    "Turnover Rate - Gender Member - Permanent Employees Member": "0",
    "Turnover Rate - Male Member - Permanent Employees Member - Previous Year": "0",
    "Turnover Rate - Female Member - Permanent Employees Member - Previous Year": "0",
    "Turnover Rate - Other Gender Member - Permanent Employees Member - Previous Year": "0",
    "Turnover Rate - Gender Member - Permanent Employees Member - Previous Year": "0",
    "Turnover Rate - Male Member - Permanent Employees Member - Prior Previous Year": "0",
    "Turnover Rate - Female Member - Permanent Employees Member - Prior Previous Year": "0",
    "Turnover Rate - Other Gender Member - Permanent Employees Member - Prior Previous Year": "0",
    "Turnover Rate - Gender Member - Permanent Employees Member - Prior Previous Year": "0",
    "Turnover Rate - Male Member - Permanent Workers Member": "0",
    "Turnover Rate - Female Member - Permanent Workers Member": "0",
    "Turnover Rate - Other Gender Member - Permanent Workers Member": "0",
    "Turnover Rate - Gender Member - Permanent Workers Member": "0",
    "Turnover Rate - Male Member - Permanent Workers Member - Previous Year": "0",
    "Turnover Rate - Female Member - Permanent Workers Member - Previous Year": "0",
    "Turnover Rate - Other Gender Member - Permanent Workers Member - Previous Year": "0",
    "Turnover Rate - Gender Member - Permanent Workers Member - Previous Year": "0",
    "Turnover Rate - Male Member - Permanent Workers Member - Prior Previous Year": "0",
    "Turnover Rate - Female Member - Permanent Workers Member - Prior Previous Year": "0",
    "Turnover Rate - Other Gender Member - Permanent Workers Member - Prior Previous Year": "0",
    "Turnover Rate - Gender Member - Permanent Workers Member - Prior Previous Year": "0",
    "Turnover": "0",
    "Net Worth": "0",
    "Number Of Complaints Filed From Stake Holder Group During The Year - Complaint Received From Communities Member": "0",
    "Number Of Complaints Pending From Stake Holder Group Resolution At The End Of Year - Complaint Received From Communities Member": "0",
    "Number Of Complaints Filed From Stake Holder Group During The Year - Complaint Received From Communities Member - Previous Year": "0",
    "Number Of Complaints Pending From Stake Holder Group Resolution At The End Of Year - Complaint Received From Communities Member - Previous Year": "0",
    "Number Of Complaints Filed From Stake Holder Group During The Year - Complaint Received From Investors Member": "0",
    "Number Of Complaints Pending From Stake Holder Group Resolution At The End Of Year - Complaint Received From Investors Member": "0",
    "Number Of Complaints Filed From Stake Holder Group During The Year - Complaint Received From Investors Member - Previous Year": "0",
    "Number Of Complaints Pending From Stake Holder Group Resolution At The End Of Year - Complaint Received From Investors Member - Previous Year": "0",
    "Number Of Complaints Filed From Stake Holder Group During The Year - Complaint Received From Shareholders Member": "0",
    "Number Of Complaints Pending From Stake Holder Group Resolution At The End Of Year - Complaint Received From Shareholders Member": "0",
    "Number Of Complaints Filed From Stake Holder Group During The Year - Complaint Received From Shareholders Member - Previous Year": "0",
    "Number Of Complaints Pending From Stake Holder Group Resolution At The End Of Year - Complaint Received From Shareholders Member - Previous Year": "0",
    "Number Of Complaints Filed From Stake Holder Group During The Year - Complaint Received From Employees And Workers Member": "0",
    "Number Of Complaints Pending From Stake Holder Group Resolution At The End Of Year - Complaint Received From Employees And Workers Member": "0",
    "Number Of Complaints Filed From Stake Holder Group During The Year - Complaint Received From Employees And Workers Member - Previous Year": "0",
    "Number Of Complaints Pending From Stake Holder Group Resolution At The End Of Year - Complaint Received From Employees And Workers Member - Previous Year": "0",
    "Number Of Complaints Filed From Stake Holder Group During The Year - Complaint Received From Customers Member": "0",
    "Number Of Complaints Pending From Stake Holder Group Resolution At The End Of Year - Complaint Received From Customers Member": "0",
    "Number Of Complaints Filed From Stake Holder Group During The Year - Complaint Received From Customers Member - Previous Year": "0",
    "Number Of Complaints Pending From Stake Holder Group Resolution At The End Of Year - Complaint Received From Customers Member - Previous Year": "0",
    "Number Of Complaints Filed From Stake Holder Group During The Year - Complaint Received From Value Chain Partners Member": "0",
    "Number Of Complaints Pending From Stake Holder Group Resolution At The End Of Year - Complaint Received From Value Chain Partners Member": "0",
    "Number Of Complaints Filed From Stake Holder Group During The Year - Complaint Received From Value Chain Partners Member - Previous Year": "0",
    "Number Of Complaints Pending From Stake Holder Group Resolution At The End Of Year - Complaint Received From Value Chain Partners Member - Previous Year": "0",
    "Has The Entity Carried Out Independent Assessment Evaluation Of The Working Of Its Policies By An External Agency - Principle1 Member": "0",
    "Has The Entity Carried Out Independent Assessment Evaluation Of The Working Of Its Policies By An External Agency - Principle2 Member": "0",
    "Has The Entity Carried Out Independent Assessment Evaluation Of The Working Of Its Policies By An External Agency - Principle3 Member": "0",
    "Has The Entity Carried Out Independent Assessment Evaluation Of The Working Of Its Policies By An External Agency - Principle4 Member": "0",
    "Has The Entity Carried Out Independent Assessment Evaluation Of The Working Of Its Policies By An External Agency - Principle5 Member": "0",
    "Has The Entity Carried Out Independent Assessment Evaluation Of The Working Of Its Policies By An External Agency - Principle6 Member": "0",
    "Has The Entity Carried Out Independent Assessment Evaluation Of The Working Of Its Policies By An External Agency - Principle7 Member": "0",
    "Has The Entity Carried Out Independent Assessment Evaluation Of The Working Of Its Policies By An External Agency - Principle8 Member": "0",
    "Has The Entity Carried Out Independent Assessment Evaluation Of The Working Of Its Policies By An External Agency - Principle9 Member": "0",
    "Total Number Of Training And Awareness Programs Held - Board Of Directors Segment Member": "0",
    "Percentage Of Persons In Respective Category Covered By The Awareness Programmes - Board Of Directors Segment Member": "0",
    "Total Number Of Training And Awareness Programs Held - Key Managerial Personnel Segment Member": "0",
    "Percentage Of Persons In Respective Category Covered By The Awareness Programmes - Key Managerial Personnel Segment Member": "0",
    "Total Number Of Training And Awareness Programs Held - Employees Other Than Bo DAnd KMPs Segment Member": "0",
    "Percentage Of Persons In Respective Category Covered By The Awareness Programmes - Employees Other Than Bo DAnd KMPs Segment Member": "0",
    "Total Number Of Training And Awareness Programs Held - Workers Segment Member": "0",
    "Percentage Of Persons In Respective Category Covered By The Awareness Programmes - Workers Segment Member": "0",
    "Number Of Directors Against Whom Disciplinary Action Was Taken": "0",
    "Number Of Directors Against Whom Disciplinary Action Was Taken - Previous Year": "0",
    "Number Of KMPs Against Whom Disciplinary Action Was Taken": "0",
    "Number Of KMPs Against Whom Disciplinary Action Was Taken - Previous Year": "0",
    "Number Of Employees Against Whom Disciplinary Action Was Taken": "0",
    "Number Of Employees Against Whom Disciplinary Action Was Taken - Previous Year": "0",
    "Number Of Workers Against Whom Disciplinary Action Was Taken": "0",
    "Number Of Workers Against Whom Disciplinary Action Was Taken - Previous Year": "0",
    "Number Of Complaints Received In Relation To Issues Of Conflict Of Interest Of The Directors": "0",
    "Number Of Complaints Received In Relation To Issues Of Conflict Of Interest Of The Directors - Previous Year": "0",
    "Number Of Complaints Received In Relation To Issues Of Conflict Of Interest Of The KMPs": "0",
    "Number Of Complaints Received In Relation To Issues Of Conflict Of Interest Of The KMPs - Previous Year": "0",
    "Amount Of Accounts Payable During The Year": "0",
    "Amount Of Accounts Payable During The Year - Previous Year": "0",
    "Cost Of Goods Or Services Procured During The Year": "0",
    "Cost Of Goods Or Services Procured During The Year - Previous Year": "0",
    "Amount Of Purchases From Trading Houses": "0",
    "Amount Of Purchases From Trading Houses - Previous Year": "0",
    "Amount Of Total Purchases": "0",
    "Amount Of Total Purchases - Previous Year": "0",
    "Percentage Of Purchases From Trading Houses In Total Purchases For Concentration Of Purchases": "0",
    "Percentage Of Purchases From Trading Houses In Total Purchases For Concentration Of Purchases - Previous Year": "0",
    "Number Of Trading Houses Where Purchases Are Made": "0",
    "Number Of Trading Houses Where Purchases Are Made - Previous Year": "0",
    "Amount Of Purchases From Top Ten Trading Houses": "0",
    "Amount Of Purchases From Top Ten Trading Houses - Previous Year": "0",
    "Amount Of Total Purchases From Trading Houses": "0",
    "Amount Of Total Purchases From Trading Houses - Previous Year": "0",
    "Percentage Of Purchases From Top Ten Trading Houses In Total Purchases From Trading Houses": "0",
    "Percentage Of Purchases From Top Ten Trading Houses In Total Purchases From Trading Houses - Previous Year": "0",
    "Amount Of Sales To Dealers Or Distributors": "0",
    "Amount Of Sales To Dealers Or Distributors - Previous Year": "0",
    "Amount Of Total Sales": "0",
    "Amount Of Total Sales - Previous Year": "0",
    "Percentage Of Sales To Dealers Or Distributors In Total Sales": "0",
    "Percentage Of Sales To Dealers Or Distributors In Total Sales - Previous Year": "0",
    "Number Of Dealers Or Distributors To Whom Sales Are Made": "0",
    "Number Of Dealers Or Distributors To Whom Sales Are Made - Previous Year": "0",
    "Amount Of Sales To Top Ten Dealers Or Distributors": "0",
    "Amount Of Sales To Top Ten Dealers Or Distributors - Previous Year": "0",
    "Amount Of Total Sales To Dealers Or Distributors": "0",
    "Amount Of Total Sales To Dealers Or Distributors - Previous Year": "0",
    "Percentage Of Sales To Top Ten Dealers Or Distributors In Total Sales To Dealers Or Distributors": "0",
    "Percentage Of Sales To Top Ten Dealers Or Distributors In Total Sales To Dealers Or Distributors - Previous Year": "0",
    "Amount Of Purchases From Related Parties": "0",
    "Amount Of Purchases From Related Parties - Previous Year": "0",
    "Amount Of Total Purchases For Share Of Related Party Transactions": "0",
    "Amount Of Total Purchases For Share Of Related Party Transactions - Previous Year": "0",
    "Percentage Of Purchases From Related Parties In Total Purchases For Share Of Related Party Transactions": "0",
    "Percentage Of Purchases From Related Parties In Total Purchases For Share Of Related Party Transactions - Previous Year": "0",
    "Amount Of Sales To Related Parties": "0",
    "Amount Of Sales To Related Parties - Previous Year": "0",
    "Amount Of Total Sales For Share Of Related Party Transactions": "0",
    "Amount Of Total Sales For Share Of Related Party Transactions - Previous Year": "0",
    "Percentage Of Sales To Related Parties In Total Sales For Share Of Related Party Transactions": "0",
    "Percentage Of Sales To Related Parties In Total Sales For Share Of Related Party Transactions - Previous Year": "0",
    "Amount Of Loans And Advances Given To Related Parties": "0",
    "Amount Of Loans And Advances Given To Related Parties - Previous Year": "0",
    "Amount Of Total Loans And Advances": "0",
    "Amount Of Total Loans And Advances - Previous Year": "0",
    "Percentage Of Loans And Advances Given To Related Parties In Total Loans And Advances": "0",
    "Percentage Of Loans And Advances Given To Related Parties In Total Loans And Advances - Previous Year": "0",
    "Amount Of Investments In Related Parties": "0",
    "Amount Of Investments In Related Parties - Previous Year": "0",
    "Amount Of Total Investments": "0",
    "Amount Of Total Investments - Previous Year": "0",
    "Percentage Of Investments In Related Parties In Total Investments": "0",
    "Percentage Of Investments In Related Parties In Total Investments - Previous Year": "0",
    "Percentage Of RAnd D": "0",
    "Percentage Of RAnd D - Previous Year": "0",
    "Percentage Of Capex": "0",
    "Percentage Of Capex - Previous Year": "0",
    "Does The Entity Have Procedures In Place For Sustainable Sourcing": "0",
    "Percentage Of Inputs Were Sourced Sustainably": "0",
    "Whether Extended Producer Responsibility Is Applicable To The Entity SActivities": "0",
    "Whether The Waste Collection Plan Is In Line With The Extended Producer Responsibility Plan Submitted To Pollution Control Boards": "0",
    "Number Of Well Being Of Employees Or Workers - Male Member - Total Employee Benefits Member - Permanent Employees Member": "0",
    "Number Of Well Being Of Employees Or Workers - Male Member - Health Insurance Member - Permanent Employees Member":
        "{Number Of Well Being Of Employees Or Workers - Gender Member - Health Insurance Member - Permanent Employees Member} - {Number Of Well Being Of Employees Or Workers - Female Member - Health Insurance Member - Permanent Employees Member} - {Number Of Well Being Of Employees Or Workers - Other Gender Member - Health Insurance Member - Permanent Employees Member}",
    "Percentage Of Well Being Of Employees Or Workers - Male Member - Health Insurance Member - Permanent Employees Member": "0",
    "Number Of Well Being Of Employees Or Workers - Male Member - Accident Insurance Member - Permanent Employees Member":
        "{Number Of Well Being Of Employees Or Workers - Gender Member - Accident Insurance Member - Permanent Employees Member} - {Number Of Well Being Of Employees Or Workers - Female Member - Accident Insurance Member - Permanent Employees Member} - {Number Of Well Being Of Employees Or Workers - Other Gender Member - Accident Insurance Member - Permanent Employees Member}",
    "Percentage Of Well Being Of Employees Or Workers - Male Member - Accident Insurance Member - Permanent Employees Member": "0",
    "Number Of Well Being Of Employees Or Workers - Male Member - Paternity Benefits Member - Permanent Employees Member": "0",
    "Percentage Of Well Being Of Employees Or Workers - Male Member - Paternity Benefits Member - Permanent Employees Member": "0",
    "Number Of Well Being Of Employees Or Workers - Male Member - Day Care Facilities Member - Permanent Employees Member":
        "{Number Of Well Being Of Employees Or Workers - Gender Member - Day Care Facilities Member - Permanent Employees Member} - {Number Of Well Being Of Employees Or Workers - Female Member - Day Care Facilities Member - Permanent Employees Member} - {Number Of Well Being Of Employees Or Workers - Other Gender Member - Day Care Facilities Member - Permanent Employees Member}",
    "Percentage Of Well Being Of Employees Or Workers - Male Member - Day Care Facilities Member - Permanent Employees Member": "0",
    "Number Of Well Being Of Employees Or Workers - Female Member - Total Employee Benefits Member - Permanent Employees Member": "0",
    "Number Of Well Being Of Employees Or Workers - Female Member - Health Insurance Member - Permanent Employees Member":
        "{Number Of Well Being Of Employees Or Workers - Gender Member - Health Insurance Member - Permanent Employees Member} - {Number Of Well Being Of Employees Or Workers - Male Member - Health Insurance Member - Permanent Employees Member} - {Number Of Well Being Of Employees Or Workers - Other Gender Member - Health Insurance Member - Permanent Employees Member}",
    "Percentage Of Well Being Of Employees Or Workers - Female Member - Health Insurance Member - Permanent Employees Member": "0",
    "Number Of Well Being Of Employees Or Workers - Female Member - Accident Insurance Member - Permanent Employees Member":
        "{Number Of Well Being Of Employees Or Workers - Gender Member - Accident Insurance Member - Permanent Employees Member} - {Number Of Well Being Of Employees Or Workers - Male Member - Accident Insurance Member - Permanent Employees Member} - {Number Of Well Being Of Employees Or Workers - Other Gender Member - Accident Insurance Member - Permanent Employees Member}",
    "Percentage Of Well Being Of Employees Or Workers - Female Member - Accident Insurance Member - Permanent Employees Member": "0",
    "Number Of Well Being Of Employees Or Workers - Female Member - Maternity Benefits Member - Permanent Employees Member": "0",
    "Percentage Of Well Being Of Employees Or Workers - Female Member - Maternity Benefits Member - Permanent Employees Member": "0",
    "Number Of Well Being Of Employees Or Workers - Female Member - Day Care Facilities Member - Permanent Employees Member":
        "{Number Of Well Being Of Employees Or Workers - Gender Member - Day Care Facilities Member - Permanent Employees Member} - {Number Of Well Being Of Employees Or Workers - Male Member - Day Care Facilities Member - Permanent Employees Member} - {Number Of Well Being Of Employees Or Workers - Other Gender Member - Day Care Facilities Member - Permanent Employees Member}",
    "Percentage Of Well Being Of Employees Or Workers - Female Member - Day Care Facilities Member - Permanent Employees Member": "0",
    "Number Of Well Being Of Employees Or Workers - Other Gender Member - Total Employee Benefits Member - Permanent Employees Member": "0",
    "Number Of Well Being Of Employees Or Workers - Other Gender Member - Health Insurance Member - Permanent Employees Member":
        "{Number Of Well Being Of Employees Or Workers - Gender Member - Health Insurance Member - Permanent Employees Member} - {Number Of Well Being Of Employees Or Workers - Male Member - Health Insurance Member - Permanent Employees Member} - {Number Of Well Being Of Employees Or Workers - Female Member - Health Insurance Member - Permanent Employees Member}",
    "Percentage Of Well Being Of Employees Or Workers - Other Gender Member - Health Insurance Member - Permanent Employees Member": "0",
    "Number Of Well Being Of Employees Or Workers - Other Gender Member - Accident Insurance Member - Permanent Employees Member":
        "{Number Of Well Being Of Employees Or Workers - Gender Member - Accident Insurance Member - Permanent Employees Member} - {Number Of Well Being Of Employees Or Workers - Male Member - Accident Insurance Member - Permanent Employees Member} - {Number Of Well Being Of Employees Or Workers - Female Member - Accident Insurance Member - Permanent Employees Member}",
    "Percentage Of Well Being Of Employees Or Workers - Other Gender Member - Accident Insurance Member - Permanent Employees Member": "0",
    "Number Of Well Being Of Employees Or Workers - Other Gender Member - Maternity Benefits Member - Permanent Employees Member": "0",
    "Percentage Of Well Being Of Employees Or Workers - Other Gender Member - Maternity Benefits Member - Permanent Employees Member": "0",
    "Number Of Well Being Of Employees Or Workers - Other Gender Member - Paternity Benefits Member - Permanent Employees Member": "0",
    "Percentage Of Well Being Of Employees Or Workers - Other Gender Member - Paternity Benefits Member - Permanent Employees Member": "0",
    "Number Of Well Being Of Employees Or Workers - Other Gender Member - Day Care Facilities Member - Permanent Employees Member":
        "{Number Of Well Being Of Employees Or Workers - Gender Member - Day Care Facilities Member - Permanent Employees Member} - {Number Of Well Being Of Employees Or Workers - Male Member - Day Care Facilities Member - Permanent Employees Member} - {Number Of Well Being Of Employees Or Workers - Female Member - Day Care Facilities Member - Permanent Employees Member}",
    "Percentage Of Well Being Of Employees Or Workers - Other Gender Member - Day Care Facilities Member - Permanent Employees Member": "0",
    "Number Of Well Being Of Employees Or Workers - Gender Member - Benefits Member - Permanent Employees Member": "0",
    "Number Of Well Being Of Employees Or Workers - Gender Member - Health Insurance Member - Permanent Employees Member":
        "{Number Of Well Being Of Employees Or Workers - Male Member - Health Insurance Member - Permanent Employees Member} + {Number Of Well Being Of Employees Or Workers - Female Member - Health Insurance Member - Permanent Employees Member} + {Number Of Well Being Of Employees Or Workers - Other Gender Member - Health Insurance Member - Permanent Employees Member}",
    "Percentage Of Well Being Of Employees Or Workers - Gender Member - Health Insurance Member - Permanent Employees Member": "0",
    "Number Of Well Being Of Employees Or Workers - Gender Member - Accident Insurance Member - Permanent Employees Member":
        "{Number Of Well Being Of Employees Or Workers - Male Member - Accident Insurance Member - Permanent Employees Member} + {Number Of Well Being Of Employees Or Workers - Female Member - Accident Insurance Member - Permanent Employees Member} + {Number Of Well Being Of Employees Or Workers - Other Gender Member - Accident Insurance Member - Permanent Employees Member}",
    "Percentage Of Well Being Of Employees Or Workers - Gender Member - Accident Insurance Member - Permanent Employees Member": "0",
    "Number Of Well Being Of Employees Or Workers - Gender Member - Maternity Benefits Member - Permanent Employees Member":
        "{Number Of Well Being Of Employees Or Workers - Female Member - Maternity Benefits Member - Permanent Employees Member} + {Number Of Well Being Of Employees Or Workers - Other Gender Member - Maternity Benefits Member - Permanent Employees Member}",
    "Percentage Of Well Being Of Employees Or Workers - Gender Member - Maternity Benefits Member - Permanent Employees Member": "0",
    "Number Of Well Being Of Employees Or Workers - Gender Member - Paternity Benefits Member - Permanent Employees Member":
        "{Number Of Well Being Of Employees Or Workers - Male Member - Paternity Benefits Member - Permanent Employees Member} + {Number Of Well Being Of Employees Or Workers - Other Gender Member - Paternity Benefits Member - Permanent Employees Member}",
    "Percentage Of Well Being Of Employees Or Workers - Gender Member - Paternity Benefits Member - Permanent Employees Member": "0",
    "Number Of Well Being Of Employees Or Workers - Gender Member - Day Care Facilities Member - Permanent Employees Member":
        "{Number Of Well Being Of Employees Or Workers - Male Member - Day Care Facilities Member - Permanent Employees Member} + {Number Of Well Being Of Employees Or Workers - Female Member - Day Care Facilities Member - Permanent Employees Member} + {Number Of Well Being Of Employees Or Workers - Other Gender Member - Day Care Facilities Member - Permanent Employees Member}",
    "Percentage Of Well Being Of Employees Or Workers - Gender Member - Day Care Facilities Member - Permanent Employees Member": "0",
    "Number Of Well Being Of Employees Or Workers - Male Member - Total Employee Benefits Member - Other Than Permanent Employees Member": "0",
    "Number Of Well Being Of Employees Or Workers - Male Member - Health Insurance Member - Other Than Permanent Employees Member":
        "{Number Of Well Being Of Employees Or Workers - Gender Member - Health Insurance Member - Other Than Permanent Employees Member} - {Number Of Well Being Of Employees Or Workers - Female Member - Health Insurance Member - Other Than Permanent Employees Member} - {Number Of Well Being Of Employees Or Workers - Other Gender Member - Health Insurance Member - Other Than Permanent Employees Member}",
    "Percentage Of Well Being Of Employees Or Workers - Male Member - Health Insurance Member - Other Than Permanent Employees Member":
        "{Percentage Of Well Being Of Employees Or Workers - Gender Member - Health Insurance Member - Other Than Permanent Employees Member} - {Percentage Of Well Being Of Employees Or Workers - Female Member - Health Insurance Member - Other Than Permanent Employees Member} - {Percentage Of Well Being Of Employees Or Workers - Other Gender Member - Health Insurance Member - Other Than Permanent Employees Member}",
    "Number Of Well Being Of Employees Or Workers - Male Member - Accident Insurance Member - Other Than Permanent Employees Member":
        "{Number Of Well Being Of Employees Or Workers - Gender Member - Accident Insurance Member - Other Than Permanent Employees Member} - {Number Of Well Being Of Employees Or Workers - Female Member - Accident Insurance Member - Other Than Permanent Employees Member} - {Number Of Well Being Of Employees Or Workers - Other Gender Member - Accident Insurance Member - Other Than Permanent Employees Member}",
    "Percentage Of Well Being Of Employees Or Workers - Male Member - Accident Insurance Member - Other Than Permanent Employees Member": "0",
    "Number Of Well Being Of Employees Or Workers - Male Member - Paternity Benefits Member - Other Than Permanent Employees Member": "0",
    "Percentage Of Well Being Of Employees Or Workers - Male Member - Paternity Benefits Member - Other Than Permanent Employees Member": "0",
    "Number Of Well Being Of Employees Or Workers - Male Member - Day Care Facilities Member - Other Than Permanent Employees Member":
        "{Number Of Well Being Of Employees Or Workers - Gender Member - Day Care Facilities Member - Other Than Permanent Employees Member} - {Number Of Well Being Of Employees Or Workers - Female Member - Day Care Facilities Member - Other Than Permanent Employees Member} - {Number Of Well Being Of Employees Or Workers - Other Gender Member - Day Care Facilities Member - Other Than Permanent Employees Member}",
    "Percentage Of Well Being Of Employees Or Workers - Male Member - Day Care Facilities Member - Other Than Permanent Employees Member": "0",
    "Number Of Well Being Of Employees Or Workers - Female Member - Total Employee Benefits Member - Other Than Permanent Employees Member": "0",
    "Number Of Well Being Of Employees Or Workers - Female Member - Health Insurance Member - Other Than Permanent Employees Member":
        "{Number Of Well Being Of Employees Or Workers - Gender Member - Health Insurance Member - Other Than Permanent Employees Member} - {Number Of Well Being Of Employees Or Workers - Male Member - Health Insurance Member - Other Than Permanent Employees Member} - {Number Of Well Being Of Employees Or Workers - Other Gender Member - Health Insurance Member - Other Than Permanent Employees Member}",
    "Percentage Of Well Being Of Employees Or Workers - Female Member - Health Insurance Member - Other Than Permanent Employees Member": "0",
    "Number Of Well Being Of Employees Or Workers - Female Member - Accident Insurance Member - Other Than Permanent Employees Member":
        "{Number Of Well Being Of Employees Or Workers - Gender Member - Accident Insurance Member - Other Than Permanent Employees Member} - {Number Of Well Being Of Employees Or Workers - Male Member - Accident Insurance Member - Other Than Permanent Employees Member} - {Number Of Well Being Of Employees Or Workers - Other Gender Member - Accident Insurance Member - Other Than Permanent Employees Member}",
    "Percentage Of Well Being Of Employees Or Workers - Female Member - Accident Insurance Member - Other Than Permanent Employees Member": "0",
    "Number Of Well Being Of Employees Or Workers - Female Member - Maternity Benefits Member - Other Than Permanent Employees Member": "0",
    "Percentage Of Well Being Of Employees Or Workers - Female Member - Maternity Benefits Member - Other Than Permanent Employees Member": "0",
    "Number Of Well Being Of Employees Or Workers - Female Member - Day Care Facilities Member - Other Than Permanent Employees Member":
        "{Number Of Well Being Of Employees Or Workers - Gender Member - Day Care Facilities Member - Other Than Permanent Employees Member} - {Number Of Well Being Of Employees Or Workers - Male Member - Day Care Facilities Member - Other Than Permanent Employees Member} - {Number Of Well Being Of Employees Or Workers - Other Gender Member - Day Care Facilities Member - Other Than Permanent Employees Member}",
    "Percentage Of Well Being Of Employees Or Workers - Female Member - Day Care Facilities Member - Other Than Permanent Employees Member": "0",
    "Number Of Well Being Of Employees Or Workers - Other Gender Member - Total Employee Benefits Member - Other Than Permanent Employees Member": "0",
    "Number Of Well Being Of Employees Or Workers - Other Gender Member - Health Insurance Member - Other Than Permanent Employees Member":
        "{Number Of Well Being Of Employees Or Workers - Gender Member - Health Insurance Member - Other Than Permanent Employees Member} - {Number Of Well Being Of Employees Or Workers - Male Member - Health Insurance Member - Other Than Permanent Employees Member} - {Number Of Well Being Of Employees Or Workers - Female Member - Health Insurance Member - Other Than Permanent Employees Member}",
    "Percentage Of Well Being Of Employees Or Workers - Other Gender Member - Health Insurance Member - Other Than Permanent Employees Member": "0",
    "Number Of Well Being Of Employees Or Workers - Other Gender Member - Accident Insurance Member - Other Than Permanent Employees Member":
        "{Number Of Well Being Of Employees Or Workers - Gender Member - Accident Insurance Member - Other Than Permanent Employees Member} - {Number Of Well Being Of Employees Or Workers - Male Member - Accident Insurance Member - Other Than Permanent Employees Member} - {Number Of Well Being Of Employees Or Workers - Female Member - Accident Insurance Member - Other Than Permanent Employees Member}",
    "Percentage Of Well Being Of Employees Or Workers - Other Gender Member - Accident Insurance Member - Other Than Permanent Employees Member": "0",
    "Number Of Well Being Of Employees Or Workers - Other Gender Member - Maternity Benefits Member - Other Than Permanent Employees Member": "0",
    "Percentage Of Well Being Of Employees Or Workers - Other Gender Member - Maternity Benefits Member - Other Than Permanent Employees Member": "0",
    "Number Of Well Being Of Employees Or Workers - Other Gender Member - Paternity Benefits Member - Other Than Permanent Employees Member": "0",
    "Percentage Of Well Being Of Employees Or Workers - Other Gender Member - Paternity Benefits Member - Other Than Permanent Employees Member": "0",
    "Number Of Well Being Of Employees Or Workers - Other Gender Member - Day Care Facilities Member - Other Than Permanent Employees Member":
        "{Number Of Well Being Of Employees Or Workers - Gender Member - Day Care Facilities Member - Other Than Permanent Employees Member} - {Number Of Well Being Of Employees Or Workers - Male Member - Day Care Facilities Member - Other Than Permanent Employees Member} - {Number Of Well Being Of Employees Or Workers - Female Member - Day Care Facilities Member - Other Than Permanent Employees Member}",
    "Percentage Of Well Being Of Employees Or Workers - Other Gender Member - Day Care Facilities Member - Other Than Permanent Employees Member": "0",
    "Number Of Well Being Of Employees Or Workers - Gender Member - Benefits Member - Other Than Permanent Employees Member": "0",
    "Number Of Well Being Of Employees Or Workers - Gender Member - Health Insurance Member - Other Than Permanent Employees Member":
        "{Number Of Well Being Of Employees Or Workers - Male Member - Health Insurance Member - Other Than Permanent Employees Member} + {Number Of Well Being Of Employees Or Workers - Female Member - Health Insurance Member - Other Than Permanent Employees Member} + {Number Of Well Being Of Employees Or Workers - Other Gender Member - Health Insurance Member - Other Than Permanent Employees Member}",
    "Percentage Of Well Being Of Employees Or Workers - Gender Member - Health Insurance Member - Other Than Permanent Employees Member": "0",
    "Number Of Well Being Of Employees Or Workers - Gender Member - Accident Insurance Member - Other Than Permanent Employees Member":
        "{Number Of Well Being Of Employees Or Workers - Male Member - Accident Insurance Member - Other Than Permanent Employees Member} + {Number Of Well Being Of Employees Or Workers - Female Member - Accident Insurance Member - Other Than Permanent Employees Member} + {Number Of Well Being Of Employees Or Workers - Other Gender Member - Accident Insurance Member - Other Than Permanent Employees Member}",
    "Percentage Of Well Being Of Employees Or Workers - Gender Member - Accident Insurance Member - Other Than Permanent Employees Member": "0",
    "Number Of Well Being Of Employees Or Workers - Gender Member - Maternity Benefits Member - Other Than Permanent Employees Member":
        "{Number Of Well Being Of Employees Or Workers - Female Member - Maternity Benefits Member - Other Than Permanent Employees Member} + {Number Of Well Being Of Employees Or Workers - Other Gender Member - Maternity Benefits Member - Other Than Permanent Employees Member}",
    "Percentage Of Well Being Of Employees Or Workers - Gender Member - Maternity Benefits Member - Other Than Permanent Employees Member": "0",
    "Number Of Well Being Of Employees Or Workers - Gender Member - Paternity Benefits Member - Other Than Permanent Employees Member":
        "{Number Of Well Being Of Employees Or Workers - Male Member - Paternity Benefits Member - Other Than Permanent Employees Member} + {Number Of Well Being Of Employees Or Workers - Other Gender Member - Paternity Benefits Member - Other Than Permanent Employees Member}",
    "Percentage Of Well Being Of Employees Or Workers - Gender Member - Paternity Benefits Member - Other Than Permanent Employees Member": "0",
    "Number Of Well Being Of Employees Or Workers - Gender Member - Day Care Facilities Member - Other Than Permanent Employees Member":
        "{Number Of Well Being Of Employees Or Workers - Male Member - Day Care Facilities Member - Other Than Permanent Employees Member} + {Number Of Well Being Of Employees Or Workers - Female Member - Day Care Facilities Member - Other Than Permanent Employees Member} + {Number Of Well Being Of Employees Or Workers - Other Gender Member - Day Care Facilities Member - Other Than Permanent Employees Member}",
    "Percentage Of Well Being Of Employees Or Workers - Gender Member - Day Care Facilities Member - Other Than Permanent Employees Member": "0",
    "Number Of Well Being Of Employees Or Workers - Male Member - Total Employee Benefits Member - Permanent Workers Member": "0",
    "Number Of Well Being Of Employees Or Workers - Male Member - Health Insurance Member - Permanent Workers Member":
        "{Number Of Well Being Of Employees Or Workers - Gender Member - Health Insurance Member - Permanent Workers Member} - {Number Of Well Being Of Employees Or Workers - Female Member - Health Insurance Member - Permanent Workers Member} - {Number Of Well Being Of Employees Or Workers - Other Gender Member - Health Insurance Member - Permanent Workers Member}",
    "Percentage Of Well Being Of Employees Or Workers - Male Member - Health Insurance Member - Permanent Workers Member": "0",
    "Number Of Well Being Of Employees Or Workers - Male Member - Accident Insurance Member - Permanent Workers Member":
        "{Number Of Well Being Of Employees Or Workers - Gender Member - Accident Insurance Member - Permanent Workers Member} - {Number Of Well Being Of Employees Or Workers - Female Member - Accident Insurance Member - Permanent Workers Member} - {Number Of Well Being Of Employees Or Workers - Other Gender Member - Accident Insurance Member - Permanent Workers Member}",
    "Percentage Of Well Being Of Employees Or Workers - Male Member - Accident Insurance Member - Permanent Workers Member": "0",
    "Number Of Well Being Of Employees Or Workers - Male Member - Paternity Benefits Member - Permanent Workers Member": "0",
    "Percentage Of Well Being Of Employees Or Workers - Male Member - Paternity Benefits Member - Permanent Workers Member": "0",
    "Number Of Well Being Of Employees Or Workers - Male Member - Day Care Facilities Member - Permanent Workers Member":
        "{Number Of Well Being Of Employees Or Workers - Gender Member - Day Care Facilities Member - Permanent Workers Member} - {Number Of Well Being Of Employees Or Workers - Female Member - Day Care Facilities Member - Permanent Workers Member} - {Number Of Well Being Of Employees Or Workers - Other Gender Member - Day Care Facilities Member - Permanent Workers Member}",
    "Percentage Of Well Being Of Employees Or Workers - Male Member - Day Care Facilities Member - Permanent Workers Member": "0",
    "Number Of Well Being Of Employees Or Workers - Female Member - Total Employee Benefits Member - Permanent Workers Member": "0",
    "Number Of Well Being Of Employees Or Workers - Female Member - Health Insurance Member - Permanent Workers Member":
        "{Number Of Well Being Of Employees Or Workers - Gender Member - Health Insurance Member - Permanent Workers Member} - {Number Of Well Being Of Employees Or Workers - Male Member - Health Insurance Member - Permanent Workers Member} - {Number Of Well Being Of Employees Or Workers - Other Gender Member - Health Insurance Member - Permanent Workers Member}",
    "Percentage Of Well Being Of Employees Or Workers - Female Member - Health Insurance Member - Permanent Workers Member": "0",
    "Number Of Well Being Of Employees Or Workers - Female Member - Accident Insurance Member - Permanent Workers Member":
        "{Number Of Well Being Of Employees Or Workers - Gender Member - Accident Insurance Member - Permanent Workers Member} - {Number Of Well Being Of Employees Or Workers - Male Member - Accident Insurance Member - Permanent Workers Member} - {Number Of Well Being Of Employees Or Workers - Other Gender Member - Accident Insurance Member - Permanent Workers Member}",
    "Percentage Of Well Being Of Employees Or Workers - Female Member - Accident Insurance Member - Permanent Workers Member": "0",
    "Number Of Well Being Of Employees Or Workers - Female Member - Maternity Benefits Member - Permanent Workers Member": "0",
    "Percentage Of Well Being Of Employees Or Workers - Female Member - Maternity Benefits Member - Permanent Workers Member": "0",
    "Number Of Well Being Of Employees Or Workers - Female Member - Day Care Facilities Member - Permanent Workers Member":
        "{Number Of Well Being Of Employees Or Workers - Gender Member - Day Care Facilities Member - Permanent Workers Member} - {Number Of Well Being Of Employees Or Workers - Male Member - Day Care Facilities Member - Permanent Workers Member} - {Number Of Well Being Of Employees Or Workers - Other Gender Member - Day Care Facilities Member - Permanent Workers Member}",
    "Percentage Of Well Being Of Employees Or Workers - Female Member - Day Care Facilities Member - Permanent Workers Member": "0",
    "Number Of Well Being Of Employees Or Workers - Other Gender Member - Total Employee Benefits Member - Permanent Workers Member": "0",
    "Number Of Well Being Of Employees Or Workers - Other Gender Member - Health Insurance Member - Permanent Workers Member":
        "{Number Of Well Being Of Employees Or Workers - Gender Member - Health Insurance Member - Permanent Workers Member} - {Number Of Well Being Of Employees Or Workers - Male Member - Health Insurance Member - Permanent Workers Member} - {Number Of Well Being Of Employees Or Workers - Female Member - Health Insurance Member - Permanent Workers Member}",
    "Percentage Of Well Being Of Employees Or Workers - Other Gender Member - Health Insurance Member - Permanent Workers Member": "0",
    "Number Of Well Being Of Employees Or Workers - Other Gender Member - Accident Insurance Member - Permanent Workers Member":
        "{Number Of Well Being Of Employees Or Workers - Gender Member - Accident Insurance Member - Permanent Workers Member} - {Number Of Well Being Of Employees Or Workers - Male Member - Accident Insurance Member - Permanent Workers Member} - {Number Of Well Being Of Employees Or Workers - Female Member - Accident Insurance Member - Permanent Workers Member}",
    "Percentage Of Well Being Of Employees Or Workers - Other Gender Member - Accident Insurance Member - Permanent Workers Member": "0",
    "Number Of Well Being Of Employees Or Workers - Other Gender Member - Maternity Benefits Member - Permanent Workers Member": "0",
    "Percentage Of Well Being Of Employees Or Workers - Other Gender Member - Maternity Benefits Member - Permanent Workers Member": "0",
    "Number Of Well Being Of Employees Or Workers - Other Gender Member - Paternity Benefits Member - Permanent Workers Member": "0",
    "Percentage Of Well Being Of Employees Or Workers - Other Gender Member - Paternity Benefits Member - Permanent Workers Member": "0",
    "Number Of Well Being Of Employees Or Workers - Other Gender Member - Day Care Facilities Member - Permanent Workers Member":
        "{Number Of Well Being Of Employees Or Workers - Gender Member - Day Care Facilities Member - Permanent Workers Member} - {Number Of Well Being Of Employees Or Workers - Male Member - Day Care Facilities Member - Permanent Workers Member} - {Number Of Well Being Of Employees Or Workers - Female Member - Day Care Facilities Member - Permanent Workers Member}",
    "Percentage Of Well Being Of Employees Or Workers - Other Gender Member - Day Care Facilities Member - Permanent Workers Member": "0",
    "Number Of Well Being Of Employees Or Workers - Gender Member - Benefits Member - Permanent Workers Member": "0",
    "Number Of Well Being Of Employees Or Workers - Gender Member - Health Insurance Member - Permanent Workers Member":
        "{Number Of Well Being Of Employees Or Workers - Male Member - Health Insurance Member - Permanent Workers Member} + {Number Of Well Being Of Employees Or Workers - Female Member - Health Insurance Member - Permanent Workers Member} + {Number Of Well Being Of Employees Or Workers - Other Gender Member - Health Insurance Member - Permanent Workers Member}",
    "Percentage Of Well Being Of Employees Or Workers - Gender Member - Health Insurance Member - Permanent Workers Member": "0",
    "Number Of Well Being Of Employees Or Workers - Gender Member - Accident Insurance Member - Permanent Workers Member":
        "{Number Of Well Being Of Employees Or Workers - Male Member - Accident Insurance Member - Permanent Workers Member} + {Number Of Well Being Of Employees Or Workers - Female Member - Accident Insurance Member - Permanent Workers Member} + {Number Of Well Being Of Employees Or Workers - Other Gender Member - Accident Insurance Member - Permanent Workers Member}",
    "Percentage Of Well Being Of Employees Or Workers - Gender Member - Accident Insurance Member - Permanent Workers Member": "0",
    "Number Of Well Being Of Employees Or Workers - Gender Member - Maternity Benefits Member - Permanent Workers Member":
        "{Number Of Well Being Of Employees Or Workers - Female Member - Maternity Benefits Member - Permanent Workers Member} + {Number Of Well Being Of Employees Or Workers - Other Gender Member - Maternity Benefits Member - Permanent Workers Member}",
    "Percentage Of Well Being Of Employees Or Workers - Gender Member - Maternity Benefits Member - Permanent Workers Member": "0",
    "Number Of Well Being Of Employees Or Workers - Gender Member - Paternity Benefits Member - Permanent Workers Member":
        "{Number Of Well Being Of Employees Or Workers - Male Member - Paternity Benefits Member - Permanent Workers Member} + {Number Of Well Being Of Employees Or Workers - Other Gender Member - Paternity Benefits Member - Permanent Workers Member}",
    "Percentage Of Well Being Of Employees Or Workers - Gender Member - Paternity Benefits Member - Permanent Workers Member": "0",
    "Number Of Well Being Of Employees Or Workers - Gender Member - Day Care Facilities Member - Permanent Workers Member":
        "{Number Of Well Being Of Employees Or Workers - Male Member - Day Care Facilities Member - Permanent Workers Member} + {Number Of Well Being Of Employees Or Workers - Female Member - Day Care Facilities Member - Permanent Workers Member} + {Number Of Well Being Of Employees Or Workers - Other Gender Member - Day Care Facilities Member - Permanent Workers Member}",
    "Percentage Of Well Being Of Employees Or Workers - Gender Member - Day Care Facilities Member - Permanent Workers Member": "0",
    "Number Of Well Being Of Employees Or Workers - Male Member - Total Employee Benefits Member - Other Than Permanent Workers Member": "0",
    "Number Of Well Being Of Employees Or Workers - Male Member - Health Insurance Member - Other Than Permanent Workers Member":
        "{Number Of Well Being Of Employees Or Workers - Gender Member - Health Insurance Member - Other Than Permanent Workers Member} - {Number Of Well Being Of Employees Or Workers - Female Member - Health Insurance Member - Other Than Permanent Workers Member} - {Number Of Well Being Of Employees Or Workers - Other Gender Member - Health Insurance Member - Other Than Permanent Workers Member}",
    "Percentage Of Well Being Of Employees Or Workers - Male Member - Health Insurance Member - Other Than Permanent Workers Member": "0",
    "Number Of Well Being Of Employees Or Workers - Male Member - Accident Insurance Member - Other Than Permanent Workers Member":
        "{Number Of Well Being Of Employees Or Workers - Gender Member - Accident Insurance Member - Other Than Permanent Workers Member} - {Number Of Well Being Of Employees Or Workers - Female Member - Accident Insurance Member - Other Than Permanent Workers Member} - {Number Of Well Being Of Employees Or Workers - Other Gender Member - Accident Insurance Member - Other Than Permanent Workers Member}",
    "Percentage Of Well Being Of Employees Or Workers - Male Member - Accident Insurance Member - Other Than Permanent Workers Member": "0",
    "Number Of Well Being Of Employees Or Workers - Male Member - Paternity Benefits Member - Other Than Permanent Workers Member": "0",
    "Percentage Of Well Being Of Employees Or Workers - Male Member - Paternity Benefits Member - Other Than Permanent Workers Member": "0",
    "Number Of Well Being Of Employees Or Workers - Male Member - Day Care Facilities Member - Other Than Permanent Workers Member":
        "{Number Of Well Being Of Employees Or Workers - Gender Member - Day Care Facilities Member - Other Than Permanent Workers Member} - {Number Of Well Being Of Employees Or Workers - Female Member - Day Care Facilities Member - Other Than Permanent Workers Member} - {Number Of Well Being Of Employees Or Workers - Other Gender Member - Day Care Facilities Member - Other Than Permanent Workers Member}",
    "Percentage Of Well Being Of Employees Or Workers - Male Member - Day Care Facilities Member - Other Than Permanent Workers Member": "0",
    "Number Of Well Being Of Employees Or Workers - Female Member - Total Employee Benefits Member - Other Than Permanent Workers Member": "0",
    "Number Of Well Being Of Employees Or Workers - Female Member - Health Insurance Member - Other Than Permanent Workers Member":
        "{Number Of Well Being Of Employees Or Workers - Gender Member - Health Insurance Member - Other Than Permanent Workers Member} - {Number Of Well Being Of Employees Or Workers - Male Member - Health Insurance Member - Other Than Permanent Workers Member} - {Number Of Well Being Of Employees Or Workers - Other Gender Member - Health Insurance Member - Other Than Permanent Workers Member}",
    "Percentage Of Well Being Of Employees Or Workers - Female Member - Health Insurance Member - Other Than Permanent Workers Member": "0",
    "Number Of Well Being Of Employees Or Workers - Female Member - Accident Insurance Member - Other Than Permanent Workers Member":
        "{Number Of Well Being Of Employees Or Workers - Gender Member - Accident Insurance Member - Other Than Permanent Workers Member} - {Number Of Well Being Of Employees Or Workers - Male Member - Accident Insurance Member - Other Than Permanent Workers Member} - {Number Of Well Being Of Employees Or Workers - Other Gender Member - Accident Insurance Member - Other Than Permanent Workers Member}",
    "Percentage Of Well Being Of Employees Or Workers - Female Member - Accident Insurance Member - Other Than Permanent Workers Member": "0",
    "Number Of Well Being Of Employees Or Workers - Female Member - Maternity Benefits Member - Other Than Permanent Workers Member": "0",
    "Percentage Of Well Being Of Employees Or Workers - Female Member - Maternity Benefits Member - Other Than Permanent Workers Member": "0",
    "Number Of Well Being Of Employees Or Workers - Female Member - Day Care Facilities Member - Other Than Permanent Workers Member":
        "{Number Of Well Being Of Employees Or Workers - Gender Member - Day Care Facilities Member - Other Than Permanent Workers Member} - {Number Of Well Being Of Employees Or Workers - Male Member - Day Care Facilities Member - Other Than Permanent Workers Member} - {Number Of Well Being Of Employees Or Workers - Other Gender Member - Day Care Facilities Member - Other Than Permanent Workers Member}",
    "Percentage Of Well Being Of Employees Or Workers - Female Member - Day Care Facilities Member - Other Than Permanent Workers Member": "0",
    "Number Of Well Being Of Employees Or Workers - Other Gender Member - Total Employee Benefits Member - Other Than Permanent Workers Member": "0",
    "Number Of Well Being Of Employees Or Workers - Other Gender Member - Health Insurance Member - Other Than Permanent Workers Member":
        "{Number Of Well Being Of Employees Or Workers - Gender Member - Health Insurance Member - Other Than Permanent Workers Member} - {Number Of Well Being Of Employees Or Workers - Male Member - Health Insurance Member - Other Than Permanent Workers Member} - {Number Of Well Being Of Employees Or Workers - Female Member - Health Insurance Member - Other Than Permanent Workers Member}",
    "Percentage Of Well Being Of Employees Or Workers - Other Gender Member - Health Insurance Member - Other Than Permanent Workers Member": "0",
    "Number Of Well Being Of Employees Or Workers - Other Gender Member - Accident Insurance Member - Other Than Permanent Workers Member":
        "{Number Of Well Being Of Employees Or Workers - Gender Member - Accident Insurance Member - Other Than Permanent Workers Member} - {Number Of Well Being Of Employees Or Workers - Male Member - Accident Insurance Member - Other Than Permanent Workers Member} - {Number Of Well Being Of Employees Or Workers - Female Member - Accident Insurance Member - Other Than Permanent Workers Member}",
    "Percentage Of Well Being Of Employees Or Workers - Other Gender Member - Accident Insurance Member - Other Than Permanent Workers Member": "0",
    "Number Of Well Being Of Employees Or Workers - Other Gender Member - Maternity Benefits Member - Other Than Permanent Workers Member": "0",
    "Percentage Of Well Being Of Employees Or Workers - Other Gender Member - Maternity Benefits Member - Other Than Permanent Workers Member": "0",
    "Number Of Well Being Of Employees Or Workers - Other Gender Member - Paternity Benefits Member - Other Than Permanent Workers Member": "0",
    "Percentage Of Well Being Of Employees Or Workers - Other Gender Member - Paternity Benefits Member - Other Than Permanent Workers Member": "0",
    "Number Of Well Being Of Employees Or Workers - Other Gender Member - Day Care Facilities Member - Other Than Permanent Workers Member":
        "{Number Of Well Being Of Employees Or Workers - Gender Member - Day Care Facilities Member - Other Than Permanent Workers Member} - {Number Of Well Being Of Employees Or Workers - Male Member - Day Care Facilities Member - Other Than Permanent Workers Member} - {Number Of Well Being Of Employees Or Workers - Female Member - Day Care Facilities Member - Other Than Permanent Workers Member}",
    "Percentage Of Well Being Of Employees Or Workers - Other Gender Member - Day Care Facilities Member - Other Than Permanent Workers Member": "0",
    "Number Of Well Being Of Employees Or Workers - Gender Member - Benefits Member - Other Than Permanent Workers Member": "0",
    "Number Of Well Being Of Employees Or Workers - Gender Member - Health Insurance Member - Other Than Permanent Workers Member":
        "{Number Of Well Being Of Employees Or Workers - Male Member - Health Insurance Member - Other Than Permanent Workers Member} + {Number Of Well Being Of Employees Or Workers - Female Member - Health Insurance Member - Other Than Permanent Workers Member} + {Number Of Well Being Of Employees Or Workers - Other Gender Member - Health Insurance Member - Other Than Permanent Workers Member}",
    "Percentage Of Well Being Of Employees Or Workers - Gender Member - Health Insurance Member - Other Than Permanent Workers Member": "0",
    "Number Of Well Being Of Employees Or Workers - Gender Member - Accident Insurance Member - Other Than Permanent Workers Member":
        "{Number Of Well Being Of Employees Or Workers - Male Member - Accident Insurance Member - Other Than Permanent Workers Member} + {Number Of Well Being Of Employees Or Workers - Female Member - Accident Insurance Member - Other Than Permanent Workers Member} + {Number Of Well Being Of Employees Or Workers - Other Gender Member - Accident Insurance Member - Other Than Permanent Workers Member}",
    "Percentage Of Well Being Of Employees Or Workers - Gender Member - Accident Insurance Member - Other Than Permanent Workers Member": "0",
    "Number Of Well Being Of Employees Or Workers - Gender Member - Maternity Benefits Member - Other Than Permanent Workers Member":
        "{Number Of Well Being Of Employees Or Workers - Female Member - Maternity Benefits Member - Other Than Permanent Workers Member} + {Number Of Well Being Of Employees Or Workers - Other Gender Member - Maternity Benefits Member - Other Than Permanent Workers Member}",
    "Percentage Of Well Being Of Employees Or Workers - Gender Member - Maternity Benefits Member - Other Than Permanent Workers Member": "0",
    "Number Of Well Being Of Employees Or Workers - Gender Member - Paternity Benefits Member - Other Than Permanent Workers Member":
        "{Number Of Well Being Of Employees Or Workers - Male Member - Paternity Benefits Member - Other Than Permanent Workers Member} + {Number Of Well Being Of Employees Or Workers - Other Gender Member - Paternity Benefits Member - Other Than Permanent Workers Member}",
    "Percentage Of Well Being Of Employees Or Workers - Gender Member - Paternity Benefits Member - Other Than Permanent Workers Member": "0",
    "Number Of Well Being Of Employees Or Workers - Gender Member - Day Care Facilities Member - Other Than Permanent Workers Member":
        "{Number Of Well Being Of Employees Or Workers - Male Member - Day Care Facilities Member - Other Than Permanent Workers Member} + {Number Of Well Being Of Employees Or Workers - Female Member - Day Care Facilities Member - Other Than Permanent Workers Member} + {Number Of Well Being Of Employees Or Workers - Other Gender Member - Day Care Facilities Member - Other Than Permanent Workers Member}",
    "Percentage Of Well Being Of Employees Or Workers - Gender Member - Day Care Facilities Member - Other Than Permanent Workers Member": "0",
    "Amount Of Cost Incurred On Well Being Measures": "0",
    "Amount Of Cost Incurred On Well Being Measures - Previous Year": "0",
    "Total Revenue Of The Company": "0",
    "Total Revenue Of The Company - Previous Year": "0",
    "Percentage Of Cost Incurred On Well Being Measures With Respect To Total Revenue Of The Company": "0",
    "Percentage Of Cost Incurred On Well Being Measures With Respect To Total Revenue Of The Company - Previous Year": "0",
    "Number Of Employees Covered As Percentage Of Total Employees - Provident Fund Member": "0",
    "Number Of Employees Covered As Percentage Of Total Worker - Provident Fund Member": "0",
    "Number Of Employees Covered As Percentage Of Total Employees - Provident Fund Member - Previous Year": "0",
    "Number Of Employees Covered As Percentage Of Total Worker - Provident Fund Member - Previous Year": "0",
    "Number Of Employees Covered As Percentage Of Total Employees - Gratuity Member": "0",
    "Number Of Employees Covered As Percentage Of Total Worker - Gratuity Member": "0",
    "Number Of Employees Covered As Percentage Of Total Employees - Gratuity Member - Previous Year": "0",
    "Number Of Employees Covered As Percentage Of Total Worker - Gratuity Member - Previous Year": "0",
    "Number Of Employees Covered As Percentage Of Total Employees - ESIMember": "0",
    "Number Of Employees Covered As Percentage Of Total Worker - ESIMember": "0",
    "Number Of Employees Covered As Percentage Of Total Employees - ESIMember - Previous Year": "0",
    "Number Of Employees Covered As Percentage Of Total Worker - ESIMember - Previous Year": "0",
    "Is There AMechanism Available To Receive And Redress Grievances For The Following Categories Of Employees And Worker": "0",
    "Is There AMechanism Available To Receive And Redress Grievances For Permanent Workers": "0",
    "Is There AMechanism Available To Receive And Redress Grievances For Other Than Permanent Workers": "0",
    "Is There AMechanism Available To Receive And Redress Grievances For Permanent Employees": "0",
    "Is There AMechanism Available To Receive And Redress Grievances For Other Than Permanent Employees": "0",
    "Return To Work Rate Permanent Employees That Took Parental Leave - Male Member": "0",
    "Retention Rates Permanent Employees That Took Parental Leave - Male Member": "0",
    "Return To Work Rate Permanent Workers That Took Parental Leave - Male Member": "0",
    "Retention Rates Permanent Workers That Took Parental Leave - Male Member": "0",
    "Return To Work Rate Permanent Employees That Took Parental Leave - Female Member":
        "{Return To Work Rate Permanent Employees That Took Parental Leave - Gender Member} - {Return To Work Rate Permanent Employees That Took Parental Leave - Male Member} - {Return To Work Rate Permanent Employees That Took Parental Leave - Other Gender Member}",
    "Retention Rates Permanent Employees That Took Parental Leave - Female Member":
        "{Retention Rates Permanent Employees That Took Parental Leave - Gender Member} - {Retention Rates Permanent Employees That Took Parental Leave - Male Member} - {Retention Rates Permanent Employees That Took Parental Leave - Other Gender Member}",
    "Return To Work Rate Permanent Workers That Took Parental Leave - Female Member":
        "{Return To Work Rate Permanent Workers That Took Parental Leave - Gender Member} - {Return To Work Rate Permanent Workers That Took Parental Leave - Male Member} - {Return To Work Rate Permanent Workers That Took Parental Leave - Other Gender Member}",
    "Retention Rates Permanent Workers That Took Parental Leave - Female Member":
        "{Retention Rates Permanent Workers That Took Parental Leave - Gender Member} - {Retention Rates Permanent Workers That Took Parental Leave - Male Member} - {Retention Rates Permanent Workers That Took Parental Leave - Other Gender Member}",
    "Return To Work Rate Permanent Employees That Took Parental Leave - Other Gender Member":
        "{Return To Work Rate Permanent Employees That Took Parental Leave - Gender Member} - {Return To Work Rate Permanent Employees That Took Parental Leave - Male Member} - {Return To Work Rate Permanent Employees That Took Parental Leave - Female Member}",
    "Retention Rates Permanent Employees That Took Parental Leave - Other Gender Member":
        "{Retention Rates Permanent Employees That Took Parental Leave - Gender Member} - {Retention Rates Permanent Employees That Took Parental Leave - Male Member} - {Retention Rates Permanent Employees That Took Parental Leave - Female Member}",
    "Return To Work Rate Permanent Workers That Took Parental Leave - Other Gender Member":
        "{Return To Work Rate Permanent Workers That Took Parental Leave - Gender Member} - {Return To Work Rate Permanent Workers That Took Parental Leave - Male Member} - {Return To Work Rate Permanent Workers That Took Parental Leave - Female Member}",
    "Retention Rates Permanent Workers That Took Parental Leave - Other Gender Member":
        "{Retention Rates Permanent Workers That Took Parental Leave - Gender Member} - {Retention Rates Permanent Workers That Took Parental Leave - Male Member} - {Retention Rates Permanent Workers That Took Parental Leave - Female Member}",
    "Return To Work Rate Permanent Employees That Took Parental Leave - Gender Member": "0",
    "Retention Rates Permanent Employees That Took Parental Leave - Gender Member": "0",
    "Return To Work Rate Permanent Workers That Took Parental Leave - Gender Member": "0",
    "Retention Rates Permanent Workers That Took Parental Leave - Gender Member": "0",
    "Total Number Of Employees Or Workers For Membership - Gender Member - Permanent Employees Member": "0",
    "Number Of Employees Or Workers Are Part Of Associations Or Union - Gender Member - Permanent Employees Member":
        "{Number Of Employees Or Workers Are Part Of Associations Or Union - Male Member - Permanent Employees Member} + {Number Of Employees Or Workers Are Part Of Associations Or Union - Female Member - Permanent Employees Member} + {Number Of Employees Or Workers Are Part Of Associations Or Union - Other Gender Member - Permanent Employees Member}",
    "Percentage Of Employees Or Workers Are Part Of Associations Or Union Of Total Number Of Employee - Gender Member - Permanent Employees Member": "0",
    "Total Number Of Employees Or Workers For Membership - Gender Member - Permanent Employees Member - Previous Year": "0",
    "Number Of Employees Or Workers Are Part Of Associations Or Union - Gender Member - Permanent Employees Member - Previous Year":
        "{Number Of Employees Or Workers Are Part Of Associations Or Union - Male Member - Permanent Employees Member - Previous Year} + {Number Of Employees Or Workers Are Part Of Associations Or Union - Female Member - Permanent Employees Member - Previous Year} + {Number Of Employees Or Workers Are Part Of Associations Or Union - Other Gender Member - Permanent Employees Member - Previous Year}",
    "Percentage Of Employees Or Workers Are Part Of Associations Or Union Of Total Number Of Employee - Gender Member - Permanent Employees Member - Previous Year": "0",
    "Total Number Of Employees Or Workers For Membership - Male Member - Permanent Employees Member":
        "{Total Number Of Employees Or Workers For Membership - Gender Member - Permanent Employees Member} - {Total Number Of Employees Or Workers For Membership - Female Member - Permanent Employees Member} - {Total Number Of Employees Or Workers For Membership - Other Gender Member - Permanent Employees Member}",
    "Number Of Employees Or Workers Are Part Of Associations Or Union - Male Member - Permanent Employees Member":
        "{Number Of Employees Or Workers Are Part Of Associations Or Union - Gender Member - Permanent Employees Member} - {Number Of Employees Or Workers Are Part Of Associations Or Union - Female Member - Permanent Employees Member} - {Number Of Employees Or Workers Are Part Of Associations Or Union - Other Gender Member - Permanent Employees Member}",
    "Percentage Of Employees Or Workers Are Part Of Associations Or Union Of Total Number Of Employee - Male Member - Permanent Employees Member": "0",
    "Total Number Of Employees Or Workers For Membership - Male Member - Permanent Employees Member - Previous Year":
        "{Total Number Of Employees Or Workers For Membership - Gender Member - Permanent Employees Member - Previous Year} - {Total Number Of Employees Or Workers For Membership - Female Member - Permanent Employees Member - Previous Year} - {Total Number Of Employees Or Workers For Membership - Other Gender Member - Permanent Employees Member - Previous Year}",
    "Number Of Employees Or Workers Are Part Of Associations Or Union - Male Member - Permanent Employees Member - Previous Year":
        "{Number Of Employees Or Workers Are Part Of Associations Or Union - Gender Member - Permanent Employees Member - Previous Year} - {Number Of Employees Or Workers Are Part Of Associations Or Union - Female Member - Permanent Employees Member - Previous Year} - {Number Of Employees Or Workers Are Part Of Associations Or Union - Other Gender Member - Permanent Employees Member - Previous Year}",
    "Percentage Of Employees Or Workers Are Part Of Associations Or Union Of Total Number Of Employee - Male Member - Permanent Employees Member - Previous Year": "0",
    "Total Number Of Employees Or Workers For Membership - Female Member - Permanent Employees Member":
        "{Total Number Of Employees Or Workers For Membership - Gender Member - Permanent Employees Member} - {Total Number Of Employees Or Workers For Membership - Male Member - Permanent Employees Member} - {Total Number Of Employees Or Workers For Membership - Other Gender Member - Permanent Employees Member}",
    "Number Of Employees Or Workers Are Part Of Associations Or Union - Female Member - Permanent Employees Member":
        "{Number Of Employees Or Workers Are Part Of Associations Or Union - Gender Member - Permanent Employees Member} - {Number Of Employees Or Workers Are Part Of Associations Or Union - Male Member - Permanent Employees Member} - {Number Of Employees Or Workers Are Part Of Associations Or Union - Other Gender Member - Permanent Employees Member}",
    "Percentage Of Employees Or Workers Are Part Of Associations Or Union Of Total Number Of Employee - Female Member - Permanent Employees Member": "0",
    "Total Number Of Employees Or Workers For Membership - Female Member - Permanent Employees Member - Previous Year":
        "{Total Number Of Employees Or Workers For Membership - Gender Member - Permanent Employees Member - Previous Year} - {Total Number Of Employees Or Workers For Membership - Male Member - Permanent Employees Member - Previous Year} - {Total Number Of Employees Or Workers For Membership - Other Gender Member - Permanent Employees Member - Previous Year}",
    "Number Of Employees Or Workers Are Part Of Associations Or Union - Female Member - Permanent Employees Member - Previous Year":
        "{Number Of Employees Or Workers Are Part Of Associations Or Union - Gender Member - Permanent Employees Member - Previous Year} - {Number Of Employees Or Workers Are Part Of Associations Or Union - Male Member - Permanent Employees Member - Previous Year} - {Number Of Employees Or Workers Are Part Of Associations Or Union - Other Gender Member - Permanent Employees Member - Previous Year}",
    "Percentage Of Employees Or Workers Are Part Of Associations Or Union Of Total Number Of Employee - Female Member - Permanent Employees Member - Previous Year": "0",
    "Total Number Of Employees Or Workers For Membership - Other Gender Member - Permanent Employees Member":
        "{Total Number Of Employees Or Workers For Membership - Gender Member - Permanent Employees Member} - {Total Number Of Employees Or Workers For Membership - Male Member - Permanent Employees Member} - {Total Number Of Employees Or Workers For Membership - Female Member - Permanent Employees Member}",
    "Number Of Employees Or Workers Are Part Of Associations Or Union - Other Gender Member - Permanent Employees Member":
        "{Number Of Employees Or Workers Are Part Of Associations Or Union - Gender Member - Permanent Employees Member} - {Number Of Employees Or Workers Are Part Of Associations Or Union - Male Member - Permanent Employees Member} - {Number Of Employees Or Workers Are Part Of Associations Or Union - Female Member - Permanent Employees Member}",
    "Percentage Of Employees Or Workers Are Part Of Associations Or Union Of Total Number Of Employee - Other Gender Member - Permanent Employees Member": "0",
    "Total Number Of Employees Or Workers For Membership - Other Gender Member - Permanent Employees Member - Previous Year":
        "{Total Number Of Employees Or Workers For Membership - Gender Member - Permanent Employees Member - Previous Year} - {Total Number Of Employees Or Workers For Membership - Male Member - Permanent Employees Member - Previous Year} - {Total Number Of Employees Or Workers For Membership - Female Member - Permanent Employees Member - Previous Year}",
    "Number Of Employees Or Workers Are Part Of Associations Or Union - Other Gender Member - Permanent Employees Member - Previous Year":
        "{Number Of Employees Or Workers Are Part Of Associations Or Union - Gender Member - Permanent Employees Member - Previous Year} - {Number Of Employees Or Workers Are Part Of Associations Or Union - Male Member - Permanent Employees Member - Previous Year} - {Number Of Employees Or Workers Are Part Of Associations Or Union - Female Member - Permanent Employees Member - Previous Year}",
    "Percentage Of Employees Or Workers Are Part Of Associations Or Union Of Total Number Of Employee - Other Gender Member - Permanent Employees Member - Previous Year":
        "{Percentage Of Employees Or Workers Are Part Of Associations Or Union Of Total Number Of Employee - Gender Member - Permanent Employees Member - Previous Year} - {Percentage Of Employees Or Workers Are Part Of Associations Or Union Of Total Number Of Employee - Male Member - Permanent Employees Member - Previous Year} - {Percentage Of Employees Or Workers Are Part Of Associations Or Union Of Total Number Of Employee - Female Member - Permanent Employees Member - Previous Year}",
    "Total Number Of Employees Or Workers For Membership - Gender Member - Permanent Workers Member": "0",
    "Number Of Employees Or Workers Are Part Of Associations Or Union - Gender Member - Permanent Workers Member":
        "{Number Of Employees Or Workers Are Part Of Associations Or Union - Male Member - Permanent Workers Member} + {Number Of Employees Or Workers Are Part Of Associations Or Union - Female Member - Permanent Workers Member} + {Number Of Employees Or Workers Are Part Of Associations Or Union - Other Gender Member - Permanent Workers Member}",
    "Percentage Of Employees Or Workers Are Part Of Associations Or Union Of Total Number Of Employee - Gender Member - Permanent Workers Member": "0",
    "Total Number Of Employees Or Workers For Membership - Gender Member - Permanent Workers Member - Previous Year": "0",
    "Number Of Employees Or Workers Are Part Of Associations Or Union - Gender Member - Permanent Workers Member - Previous Year":
        "{Number Of Employees Or Workers Are Part Of Associations Or Union - Male Member - Permanent Workers Member - Previous Year} + {Number Of Employees Or Workers Are Part Of Associations Or Union - Female Member - Permanent Workers Member - Previous Year} + {Number Of Employees Or Workers Are Part Of Associations Or Union - Other Gender Member - Permanent Workers Member - Previous Year}",
    "Percentage Of Employees Or Workers Are Part Of Associations Or Union Of Total Number Of Employee - Gender Member - Permanent Workers Member - Previous Year": "0",
    "Total Number Of Employees Or Workers For Membership - Male Member - Permanent Workers Member":
        "{Total Number Of Employees Or Workers For Membership - Gender Member - Permanent Workers Member} - {Total Number Of Employees Or Workers For Membership - Female Member - Permanent Workers Member} - {Total Number Of Employees Or Workers For Membership - Other Gender Member - Permanent Workers Member}",
    "Number Of Employees Or Workers Are Part Of Associations Or Union - Male Member - Permanent Workers Member":
        "{Number Of Employees Or Workers Are Part Of Associations Or Union - Gender Member - Permanent Workers Member} - {Number Of Employees Or Workers Are Part Of Associations Or Union - Female Member - Permanent Workers Member} - {Number Of Employees Or Workers Are Part Of Associations Or Union - Other Gender Member - Permanent Workers Member}",
    "Percentage Of Employees Or Workers Are Part Of Associations Or Union Of Total Number Of Employee - Male Member - Permanent Workers Member": "0",
    "Total Number Of Employees Or Workers For Membership - Male Member - Permanent Workers Member - Previous Year":
        "{Total Number Of Employees Or Workers For Membership - Gender Member - Permanent Workers Member - Previous Year} - {Total Number Of Employees Or Workers For Membership - Female Member - Permanent Workers Member - Previous Year} - {Total Number Of Employees Or Workers For Membership - Other Gender Member - Permanent Workers Member - Previous Year}",
    "Number Of Employees Or Workers Are Part Of Associations Or Union - Male Member - Permanent Workers Member - Previous Year":
        "{Number Of Employees Or Workers Are Part Of Associations Or Union - Gender Member - Permanent Workers Member - Previous Year} - {Number Of Employees Or Workers Are Part Of Associations Or Union - Female Member - Permanent Workers Member - Previous Year} - {Number Of Employees Or Workers Are Part Of Associations Or Union - Other Gender Member - Permanent Workers Member - Previous Year}",
    "Percentage Of Employees Or Workers Are Part Of Associations Or Union Of Total Number Of Employee - Male Member - Permanent Workers Member - Previous Year": "0",
    "Total Number Of Employees Or Workers For Membership - Female Member - Permanent Workers Member":
        "{Total Number Of Employees Or Workers For Membership - Gender Member - Permanent Workers Member} - {Total Number Of Employees Or Workers For Membership - Male Member - Permanent Workers Member} - {Total Number Of Employees Or Workers For Membership - Other Gender Member - Permanent Workers Member}",
    "Number Of Employees Or Workers Are Part Of Associations Or Union - Female Member - Permanent Workers Member":
        "{Number Of Employees Or Workers Are Part Of Associations Or Union - Gender Member - Permanent Workers Member} - {Number Of Employees Or Workers Are Part Of Associations Or Union - Male Member - Permanent Workers Member} - {Number Of Employees Or Workers Are Part Of Associations Or Union - Other Gender Member - Permanent Workers Member}",
    "Percentage Of Employees Or Workers Are Part Of Associations Or Union Of Total Number Of Employee - Female Member - Permanent Workers Member": "0",
    "Total Number Of Employees Or Workers For Membership - Female Member - Permanent Workers Member - Previous Year":
        "{Total Number Of Employees Or Workers For Membership - Gender Member - Permanent Workers Member - Previous Year} - {Total Number Of Employees Or Workers For Membership - Male Member - Permanent Workers Member - Previous Year} - {Total Number Of Employees Or Workers For Membership - Other Gender Member - Permanent Workers Member - Previous Year}",
    "Number Of Employees Or Workers Are Part Of Associations Or Union - Female Member - Permanent Workers Member - Previous Year":
        "{Number Of Employees Or Workers Are Part Of Associations Or Union - Gender Member - Permanent Workers Member - Previous Year} - {Number Of Employees Or Workers Are Part Of Associations Or Union - Male Member - Permanent Workers Member - Previous Year} - {Number Of Employees Or Workers Are Part Of Associations Or Union - Other Gender Member - Permanent Workers Member - Previous Year}",
    "Percentage Of Employees Or Workers Are Part Of Associations Or Union Of Total Number Of Employee - Female Member - Permanent Workers Member - Previous Year": "0",
    "Total Number Of Employees Or Workers For Membership - Other Gender Member - Permanent Workers Member":
        "{Total Number Of Employees Or Workers For Membership - Gender Member - Permanent Workers Member} - {Total Number Of Employees Or Workers For Membership - Male Member - Permanent Workers Member} - {Total Number Of Employees Or Workers For Membership - Female Member - Permanent Workers Member}",
    "Number Of Employees Or Workers Are Part Of Associations Or Union - Other Gender Member - Permanent Workers Member":
        "{Number Of Employees Or Workers Are Part Of Associations Or Union - Gender Member - Permanent Workers Member} - {Number Of Employees Or Workers Are Part Of Associations Or Union - Male Member - Permanent Workers Member} - {Number Of Employees Or Workers Are Part Of Associations Or Union - Female Member - Permanent Workers Member}",
    "Percentage Of Employees Or Workers Are Part Of Associations Or Union Of Total Number Of Employee - Other Gender Member - Permanent Workers Member": "0",
    "Total Number Of Employees Or Workers For Membership - Other Gender Member - Permanent Workers Member - Previous Year":
        "{Total Number Of Employees Or Workers For Membership - Gender Member - Permanent Workers Member - Previous Year} - {Total Number Of Employees Or Workers For Membership - Male Member - Permanent Workers Member - Previous Year} - {Total Number Of Employees Or Workers For Membership - Female Member - Permanent Workers Member - Previous Year}",
    "Number Of Employees Or Workers Are Part Of Associations Or Union - Other Gender Member - Permanent Workers Member - Previous Year":
        "{Number Of Employees Or Workers Are Part Of Associations Or Union - Gender Member - Permanent Workers Member - Previous Year} - {Number Of Employees Or Workers Are Part Of Associations Or Union - Male Member - Permanent Workers Member - Previous Year} - {Number Of Employees Or Workers Are Part Of Associations Or Union - Female Member - Permanent Workers Member - Previous Year}",
    "Percentage Of Employees Or Workers Are Part Of Associations Or Union Of Total Number Of Employee - Other Gender Member - Permanent Workers Member - Previous Year": "0",
    "Number Of Trained Employees Or Workers - Male Member - Total Employees And Workers Member - Employees Member":
        "{Number Of Trained Employees Or Workers - Gender Member - Total Employees And Workers Member - Employees Member} - {Number Of Trained Employees Or Workers - Female Member - Total Employees And Workers Member - Employees Member} - {Number Of Trained Employees Or Workers - Other Gender Member - Total Employees And Workers Member - Employees Member}",
    "Number Of Trained Employees Or Workers - Male Member - On Health And Safety Measures Member - Employees Member":
        "{Number Of Trained Employees Or Workers - Gender Member - On Health And Safety Measures Member - Employees Member} - {Number Of Trained Employees Or Workers - Female Member - On Health And Safety Measures Member - Employees Member} - {Number Of Trained Employees Or Workers - Other Gender Member - On Health And Safety Measures Member - Employees Member}",
    "Percentage Of Trained Employees Or Workers - Male Member - On Health And Safety Measures Member - Employees Member": "0",
    "Number Of Trained Employees Or Workers - Male Member - On Skill Upgradation Member - Employees Member":
        "{Number Of Trained Employees Or Workers - Gender Member - On Skill Upgradation Member - Employees Member} - {Number Of Trained Employees Or Workers - Female Member - On Skill Upgradation Member - Employees Member} - {Number Of Trained Employees Or Workers - Other Gender Member - On Skill Upgradation Member - Employees Member}",
    "Percentage Of Trained Employees Or Workers - Male Member - On Skill Upgradation Member - Employees Member": "0",
    "Number Of Trained Employees Or Workers - Male Member - Total Employees And Workers Member - Employees Member - Previous Year":
        "{Number Of Trained Employees Or Workers - Gender Member - Total Employees And Workers Member - Employees Member - Previous Year} - {Number Of Trained Employees Or Workers - Female Member - Total Employees And Workers Member - Employees Member - Previous Year} - {Number Of Trained Employees Or Workers - Other Gender Member - Total Employees And Workers Member - Employees Member - Previous Year}",
    "Number Of Trained Employees Or Workers - Male Member - On Health And Safety Measures Member - Employees Member - Previous Year":
        "{Number Of Trained Employees Or Workers - Gender Member - On Health And Safety Measures Member - Employees Member - Previous Year} - {Number Of Trained Employees Or Workers - Female Member - On Health And Safety Measures Member - Employees Member - Previous Year} - {Number Of Trained Employees Or Workers - Other Gender Member - On Health And Safety Measures Member - Employees Member - Previous Year}",
    "Percentage Of Trained Employees Or Workers - Male Member - On Health And Safety Measures Member - Employees Member - Previous Year":
        "{Percentage Of Trained Employees Or Workers - Gender Member - On Health And Safety Measures Member - Employees Member - Previous Year} - {Percentage Of Trained Employees Or Workers - Female Member - On Health And Safety Measures Member - Employees Member - Previous Year} - {Percentage Of Trained Employees Or Workers - Other Gender Member - On Health And Safety Measures Member - Employees Member - Previous Year}",
    "Number Of Trained Employees Or Workers - Male Member - On Skill Upgradation Member - Employees Member - Previous Year":
        "{Number Of Trained Employees Or Workers - Gender Member - On Skill Upgradation Member - Employees Member - Previous Year} - {Number Of Trained Employees Or Workers - Female Member - On Skill Upgradation Member - Employees Member - Previous Year} - {Number Of Trained Employees Or Workers - Other Gender Member - On Skill Upgradation Member - Employees Member - Previous Year}",
    "Percentage Of Trained Employees Or Workers - Male Member - On Skill Upgradation Member - Employees Member - Previous Year":
        "{Percentage Of Trained Employees Or Workers - Gender Member - On Skill Upgradation Member - Employees Member - Previous Year} - {Percentage Of Trained Employees Or Workers - Female Member - On Skill Upgradation Member - Employees Member - Previous Year} - {Percentage Of Trained Employees Or Workers - Other Gender Member - On Skill Upgradation Member - Employees Member - Previous Year}",
    "Number Of Trained Employees Or Workers - Female Member - Total Employees And Workers Member - Employees Member":
        "{Number Of Trained Employees Or Workers - Gender Member - Total Employees And Workers Member - Employees Member} - {Number Of Trained Employees Or Workers - Male Member - Total Employees And Workers Member - Employees Member} - {Number Of Trained Employees Or Workers - Other Gender Member - Total Employees And Workers Member - Employees Member}",
    "Number Of Trained Employees Or Workers - Female Member - On Health And Safety Measures Member - Employees Member":
        "{Number Of Trained Employees Or Workers - Gender Member - On Health And Safety Measures Member - Employees Member} - {Number Of Trained Employees Or Workers - Male Member - On Health And Safety Measures Member - Employees Member} - {Number Of Trained Employees Or Workers - Other Gender Member - On Health And Safety Measures Member - Employees Member}",
    "Percentage Of Trained Employees Or Workers - Female Member - On Health And Safety Measures Member - Employees Member": "0",
    "Number Of Trained Employees Or Workers - Female Member - On Skill Upgradation Member - Employees Member":
        "{Number Of Trained Employees Or Workers - Gender Member - On Skill Upgradation Member - Employees Member} - {Number Of Trained Employees Or Workers - Male Member - On Skill Upgradation Member - Employees Member} - {Number Of Trained Employees Or Workers - Other Gender Member - On Skill Upgradation Member - Employees Member}",
    "Percentage Of Trained Employees Or Workers - Female Member - On Skill Upgradation Member - Employees Member": "0",
    "Number Of Trained Employees Or Workers - Female Member - Total Employees And Workers Member - Employees Member - Previous Year":
        "{Number Of Trained Employees Or Workers - Gender Member - Total Employees And Workers Member - Employees Member - Previous Year} - {Number Of Trained Employees Or Workers - Male Member - Total Employees And Workers Member - Employees Member - Previous Year} - {Number Of Trained Employees Or Workers - Other Gender Member - Total Employees And Workers Member - Employees Member - Previous Year}",
    "Number Of Trained Employees Or Workers - Female Member - On Health And Safety Measures Member - Employees Member - Previous Year":
        "{Number Of Trained Employees Or Workers - Gender Member - On Health And Safety Measures Member - Employees Member - Previous Year} - {Number Of Trained Employees Or Workers - Male Member - On Health And Safety Measures Member - Employees Member - Previous Year} - {Number Of Trained Employees Or Workers - Other Gender Member - On Health And Safety Measures Member - Employees Member - Previous Year}",
    "Percentage Of Trained Employees Or Workers - Female Member - On Health And Safety Measures Member - Employees Member - Previous Year": "0",
    "Number Of Trained Employees Or Workers - Female Member - On Skill Upgradation Member - Employees Member - Previous Year":
        "{Number Of Trained Employees Or Workers - Gender Member - On Skill Upgradation Member - Employees Member - Previous Year} - {Number Of Trained Employees Or Workers - Male Member - On Skill Upgradation Member - Employees Member - Previous Year} - {Number Of Trained Employees Or Workers - Other Gender Member - On Skill Upgradation Member - Employees Member - Previous Year}",
    "Percentage Of Trained Employees Or Workers - Female Member - On Skill Upgradation Member - Employees Member - Previous Year": "0",
    "Number Of Trained Employees Or Workers - Other Gender Member - Total Employees And Workers Member - Employees Member":
        "{Number Of Trained Employees Or Workers - Gender Member - Total Employees And Workers Member - Employees Member} - {Number Of Trained Employees Or Workers - Male Member - Total Employees And Workers Member - Employees Member} - {Number Of Trained Employees Or Workers - Female Member - Total Employees And Workers Member - Employees Member}",
    "Number Of Trained Employees Or Workers - Other Gender Member - On Health And Safety Measures Member - Employees Member":
        "{Number Of Trained Employees Or Workers - Gender Member - On Health And Safety Measures Member - Employees Member} - {Number Of Trained Employees Or Workers - Male Member - On Health And Safety Measures Member - Employees Member} - {Number Of Trained Employees Or Workers - Female Member - On Health And Safety Measures Member - Employees Member}",
    "Percentage Of Trained Employees Or Workers - Other Gender Member - On Health And Safety Measures Member - Employees Member": "0",
    "Number Of Trained Employees Or Workers - Other Gender Member - On Skill Upgradation Member - Employees Member":
        "{Number Of Trained Employees Or Workers - Gender Member - On Skill Upgradation Member - Employees Member} - {Number Of Trained Employees Or Workers - Male Member - On Skill Upgradation Member - Employees Member} - {Number Of Trained Employees Or Workers - Female Member - On Skill Upgradation Member - Employees Member}",
    "Percentage Of Trained Employees Or Workers - Other Gender Member - On Skill Upgradation Member - Employees Member": "0",
    "Number Of Trained Employees Or Workers - Other Gender Member - Total Employees And Workers Member - Employees Member - Previous Year":
        "{Number Of Trained Employees Or Workers - Gender Member - Total Employees And Workers Member - Employees Member - Previous Year} - {Number Of Trained Employees Or Workers - Male Member - Total Employees And Workers Member - Employees Member - Previous Year} - {Number Of Trained Employees Or Workers - Female Member - Total Employees And Workers Member - Employees Member - Previous Year}",
    "Number Of Trained Employees Or Workers - Other Gender Member - On Health And Safety Measures Member - Employees Member - Previous Year":
        "{Number Of Trained Employees Or Workers - Gender Member - On Health And Safety Measures Member - Employees Member - Previous Year} - {Number Of Trained Employees Or Workers - Male Member - On Health And Safety Measures Member - Employees Member - Previous Year} - {Number Of Trained Employees Or Workers - Female Member - On Health And Safety Measures Member - Employees Member - Previous Year}",
    "Percentage Of Trained Employees Or Workers - Other Gender Member - On Health And Safety Measures Member - Employees Member - Previous Year": "0",
    "Number Of Trained Employees Or Workers - Other Gender Member - On Skill Upgradation Member - Employees Member - Previous Year":
        "{Number Of Trained Employees Or Workers - Gender Member - On Skill Upgradation Member - Employees Member - Previous Year} - {Number Of Trained Employees Or Workers - Male Member - On Skill Upgradation Member - Employees Member - Previous Year} - {Number Of Trained Employees Or Workers - Female Member - On Skill Upgradation Member - Employees Member - Previous Year}",
    "Percentage Of Trained Employees Or Workers - Other Gender Member - On Skill Upgradation Member - Employees Member - Previous Year": "0",
    "Number Of Trained Employees Or Workers - Gender Member - Total Employees And Workers Member - Employees Member":
        "{Number Of Trained Employees Or Workers - Male Member - Total Employees And Workers Member - Employees Member} + {Number Of Trained Employees Or Workers - Female Member - Total Employees And Workers Member - Employees Member} + {Number Of Trained Employees Or Workers - Other Gender Member - Total Employees And Workers Member - Employees Member}",
    "Number Of Trained Employees Or Workers - Gender Member - On Health And Safety Measures Member - Employees Member":
        "{Number Of Trained Employees Or Workers - Male Member - On Health And Safety Measures Member - Employees Member} + {Number Of Trained Employees Or Workers - Female Member - On Health And Safety Measures Member - Employees Member} + {Number Of Trained Employees Or Workers - Other Gender Member - On Health And Safety Measures Member - Employees Member}",
    "Percentage Of Trained Employees Or Workers - Gender Member - On Health And Safety Measures Member - Employees Member": "0",
    "Number Of Trained Employees Or Workers - Gender Member - On Skill Upgradation Member - Employees Member":
        "{Number Of Trained Employees Or Workers - Male Member - On Skill Upgradation Member - Employees Member} + {Number Of Trained Employees Or Workers - Female Member - On Skill Upgradation Member - Employees Member} + {Number Of Trained Employees Or Workers - Other Gender Member - On Skill Upgradation Member - Employees Member}",
    "Percentage Of Trained Employees Or Workers - Gender Member - On Skill Upgradation Member - Employees Member": "0",
    "Number Of Trained Employees Or Workers - Gender Member - Total Employees And Workers Member - Employees Member - Previous Year":
        "{Number Of Trained Employees Or Workers - Male Member - Total Employees And Workers Member - Employees Member - Previous Year} + {Number Of Trained Employees Or Workers - Female Member - Total Employees And Workers Member - Employees Member - Previous Year} + {Number Of Trained Employees Or Workers - Other Gender Member - Total Employees And Workers Member - Employees Member - Previous Year}",
    "Number Of Trained Employees Or Workers - Gender Member - On Health And Safety Measures Member - Employees Member - Previous Year":
        "{Number Of Trained Employees Or Workers - Male Member - On Health And Safety Measures Member - Employees Member - Previous Year} + {Number Of Trained Employees Or Workers - Female Member - On Health And Safety Measures Member - Employees Member - Previous Year} + {Number Of Trained Employees Or Workers - Other Gender Member - On Health And Safety Measures Member - Employees Member - Previous Year}",
    "Percentage Of Trained Employees Or Workers - Gender Member - On Health And Safety Measures Member - Employees Member - Previous Year": "0",
    "Number Of Trained Employees Or Workers - Gender Member - On Skill Upgradation Member - Employees Member - Previous Year":
        "{Number Of Trained Employees Or Workers - Male Member - On Skill Upgradation Member - Employees Member - Previous Year} + {Number Of Trained Employees Or Workers - Female Member - On Skill Upgradation Member - Employees Member - Previous Year} + {Number Of Trained Employees Or Workers - Other Gender Member - On Skill Upgradation Member - Employees Member - Previous Year}",
    "Percentage Of Trained Employees Or Workers - Gender Member - On Skill Upgradation Member - Employees Member - Previous Year": "0",
    "Number Of Trained Employees Or Workers - Male Member - Total Employees And Workers Member - Workers Member":
        "{Number Of Trained Employees Or Workers - Gender Member - Total Employees And Workers Member - Workers Member} - {Number Of Trained Employees Or Workers - Female Member - Total Employees And Workers Member - Workers Member} - {Number Of Trained Employees Or Workers - Other Gender Member - Total Employees And Workers Member - Workers Member}",
    "Number Of Trained Employees Or Workers - Male Member - On Health And Safety Measures Member - Workers Member":
        "{Number Of Trained Employees Or Workers - Gender Member - On Health And Safety Measures Member - Workers Member} - {Number Of Trained Employees Or Workers - Female Member - On Health And Safety Measures Member - Workers Member} - {Number Of Trained Employees Or Workers - Other Gender Member - On Health And Safety Measures Member - Workers Member}",
    "Percentage Of Trained Employees Or Workers - Male Member - On Health And Safety Measures Member - Workers Member": "0",
    "Number Of Trained Employees Or Workers - Male Member - On Skill Upgradation Member - Workers Member":
        "{Number Of Trained Employees Or Workers - Gender Member - On Skill Upgradation Member - Workers Member} - {Number Of Trained Employees Or Workers - Female Member - On Skill Upgradation Member - Workers Member} - {Number Of Trained Employees Or Workers - Other Gender Member - On Skill Upgradation Member - Workers Member}",
    "Percentage Of Trained Employees Or Workers - Male Member - On Skill Upgradation Member - Workers Member": "0",
    "Number Of Trained Employees Or Workers - Male Member - Total Employees And Workers Member - Workers Member - Previous Year":
        "{Number Of Trained Employees Or Workers - Gender Member - Total Employees And Workers Member - Workers Member - Previous Year} - {Number Of Trained Employees Or Workers - Female Member - Total Employees And Workers Member - Workers Member - Previous Year} - {Number Of Trained Employees Or Workers - Other Gender Member - Total Employees And Workers Member - Workers Member - Previous Year}",
    "Number Of Trained Employees Or Workers - Male Member - On Health And Safety Measures Member - Workers Member - Previous Year":
        "{Number Of Trained Employees Or Workers - Gender Member - On Health And Safety Measures Member - Workers Member - Previous Year} - {Number Of Trained Employees Or Workers - Female Member - On Health And Safety Measures Member - Workers Member - Previous Year} - {Number Of Trained Employees Or Workers - Other Gender Member - On Health And Safety Measures Member - Workers Member - Previous Year}",
    "Percentage Of Trained Employees Or Workers - Male Member - On Health And Safety Measures Member - Workers Member - Previous Year": "0",
    "Number Of Trained Employees Or Workers - Male Member - On Skill Upgradation Member - Workers Member - Previous Year":
        "{Number Of Trained Employees Or Workers - Gender Member - On Skill Upgradation Member - Workers Member - Previous Year} - {Number Of Trained Employees Or Workers - Female Member - On Skill Upgradation Member - Workers Member - Previous Year} - {Number Of Trained Employees Or Workers - Other Gender Member - On Skill Upgradation Member - Workers Member - Previous Year}",
    "Percentage Of Trained Employees Or Workers - Male Member - On Skill Upgradation Member - Workers Member - Previous Year": "0",
    "Number Of Trained Employees Or Workers - Female Member - Total Employees And Workers Member - Workers Member":
        "{Number Of Trained Employees Or Workers - Gender Member - Total Employees And Workers Member - Workers Member} - {Number Of Trained Employees Or Workers - Male Member - Total Employees And Workers Member - Workers Member} - {Number Of Trained Employees Or Workers - Other Gender Member - Total Employees And Workers Member - Workers Member}",
    "Number Of Trained Employees Or Workers - Female Member - On Health And Safety Measures Member - Workers Member":
        "{Number Of Trained Employees Or Workers - Gender Member - On Health And Safety Measures Member - Workers Member} - {Number Of Trained Employees Or Workers - Male Member - On Health And Safety Measures Member - Workers Member} - {Number Of Trained Employees Or Workers - Other Gender Member - On Health And Safety Measures Member - Workers Member}",
    "Percentage Of Trained Employees Or Workers - Female Member - On Health And Safety Measures Member - Workers Member": "0",
    "Number Of Trained Employees Or Workers - Female Member - On Skill Upgradation Member - Workers Member":
        "{Number Of Trained Employees Or Workers - Gender Member - On Skill Upgradation Member - Workers Member} - {Number Of Trained Employees Or Workers - Male Member - On Skill Upgradation Member - Workers Member} - {Number Of Trained Employees Or Workers - Other Gender Member - On Skill Upgradation Member - Workers Member}",
    "Percentage Of Trained Employees Or Workers - Female Member - On Skill Upgradation Member - Workers Member": "0",
    "Number Of Trained Employees Or Workers - Female Member - Total Employees And Workers Member - Workers Member - Previous Year":
        "{Number Of Trained Employees Or Workers - Gender Member - Total Employees And Workers Member - Workers Member - Previous Year} - {Number Of Trained Employees Or Workers - Male Member - Total Employees And Workers Member - Workers Member - Previous Year} - {Number Of Trained Employees Or Workers - Other Gender Member - Total Employees And Workers Member - Workers Member - Previous Year}",
    "Number Of Trained Employees Or Workers - Female Member - On Health And Safety Measures Member - Workers Member - Previous Year":
        "{Number Of Trained Employees Or Workers - Gender Member - On Health And Safety Measures Member - Workers Member - Previous Year} - {Number Of Trained Employees Or Workers - Male Member - On Health And Safety Measures Member - Workers Member - Previous Year} - {Number Of Trained Employees Or Workers - Other Gender Member - On Health And Safety Measures Member - Workers Member - Previous Year}",
    "Percentage Of Trained Employees Or Workers - Female Member - On Health And Safety Measures Member - Workers Member - Previous Year": "0",
    "Number Of Trained Employees Or Workers - Female Member - On Skill Upgradation Member - Workers Member - Previous Year":
        "{Number Of Trained Employees Or Workers - Gender Member - On Skill Upgradation Member - Workers Member - Previous Year} - {Number Of Trained Employees Or Workers - Male Member - On Skill Upgradation Member - Workers Member - Previous Year} - {Number Of Trained Employees Or Workers - Other Gender Member - On Skill Upgradation Member - Workers Member - Previous Year}",
    "Percentage Of Trained Employees Or Workers - Female Member - On Skill Upgradation Member - Workers Member - Previous Year": "0",
    "Number Of Trained Employees Or Workers - Other Gender Member - Total Employees And Workers Member - Workers Member":
        "{Number Of Trained Employees Or Workers - Gender Member - Total Employees And Workers Member - Workers Member} - {Number Of Trained Employees Or Workers - Male Member - Total Employees And Workers Member - Workers Member} - {Number Of Trained Employees Or Workers - Female Member - Total Employees And Workers Member - Workers Member}",
    "Number Of Trained Employees Or Workers - Other Gender Member - On Health And Safety Measures Member - Workers Member":
        "{Number Of Trained Employees Or Workers - Gender Member - On Health And Safety Measures Member - Workers Member} - {Number Of Trained Employees Or Workers - Male Member - On Health And Safety Measures Member - Workers Member} - {Number Of Trained Employees Or Workers - Female Member - On Health And Safety Measures Member - Workers Member}",
    "Percentage Of Trained Employees Or Workers - Other Gender Member - On Health And Safety Measures Member - Workers Member": "0",
    "Number Of Trained Employees Or Workers - Other Gender Member - On Skill Upgradation Member - Workers Member":
        "{Number Of Trained Employees Or Workers - Gender Member - On Skill Upgradation Member - Workers Member} - {Number Of Trained Employees Or Workers - Male Member - On Skill Upgradation Member - Workers Member} - {Number Of Trained Employees Or Workers - Female Member - On Skill Upgradation Member - Workers Member}",
    "Percentage Of Trained Employees Or Workers - Other Gender Member - On Skill Upgradation Member - Workers Member": "0",
    "Number Of Trained Employees Or Workers - Other Gender Member - Total Employees And Workers Member - Workers Member - Previous Year":
        "{Number Of Trained Employees Or Workers - Gender Member - Total Employees And Workers Member - Workers Member - Previous Year} - {Number Of Trained Employees Or Workers - Male Member - Total Employees And Workers Member - Workers Member - Previous Year} - {Number Of Trained Employees Or Workers - Female Member - Total Employees And Workers Member - Workers Member - Previous Year}",
    "Number Of Trained Employees Or Workers - Other Gender Member - On Health And Safety Measures Member - Workers Member - Previous Year":
        "{Number Of Trained Employees Or Workers - Gender Member - On Health And Safety Measures Member - Workers Member - Previous Year} - {Number Of Trained Employees Or Workers - Male Member - On Health And Safety Measures Member - Workers Member - Previous Year} - {Number Of Trained Employees Or Workers - Female Member - On Health And Safety Measures Member - Workers Member - Previous Year}",
    "Percentage Of Trained Employees Or Workers - Other Gender Member - On Health And Safety Measures Member - Workers Member - Previous Year":
        "{Percentage Of Trained Employees Or Workers - Gender Member - On Health And Safety Measures Member - Workers Member - Previous Year} - {Percentage Of Trained Employees Or Workers - Male Member - On Health And Safety Measures Member - Workers Member - Previous Year} - {Percentage Of Trained Employees Or Workers - Female Member - On Health And Safety Measures Member - Workers Member - Previous Year}",
    "Number Of Trained Employees Or Workers - Other Gender Member - On Skill Upgradation Member - Workers Member - Previous Year":
        "{Number Of Trained Employees Or Workers - Gender Member - On Skill Upgradation Member - Workers Member - Previous Year} - {Number Of Trained Employees Or Workers - Male Member - On Skill Upgradation Member - Workers Member - Previous Year} - {Number Of Trained Employees Or Workers - Female Member - On Skill Upgradation Member - Workers Member - Previous Year}",
    "Percentage Of Trained Employees Or Workers - Other Gender Member - On Skill Upgradation Member - Workers Member - Previous Year":
        "{Percentage Of Trained Employees Or Workers - Gender Member - On Skill Upgradation Member - Workers Member - Previous Year} - {Percentage Of Trained Employees Or Workers - Male Member - On Skill Upgradation Member - Workers Member - Previous Year} - {Percentage Of Trained Employees Or Workers - Female Member - On Skill Upgradation Member - Workers Member - Previous Year}",
    "Number Of Trained Employees Or Workers - Gender Member - Total Employees And Workers Member - Workers Member":
        "{Number Of Trained Employees Or Workers - Male Member - Total Employees And Workers Member - Workers Member} + {Number Of Trained Employees Or Workers - Female Member - Total Employees And Workers Member - Workers Member} + {Number Of Trained Employees Or Workers - Other Gender Member - Total Employees And Workers Member - Workers Member}",
    "Number Of Trained Employees Or Workers - Gender Member - On Health And Safety Measures Member - Workers Member":
        "{Number Of Trained Employees Or Workers - Male Member - On Health And Safety Measures Member - Workers Member} + {Number Of Trained Employees Or Workers - Female Member - On Health And Safety Measures Member - Workers Member} + {Number Of Trained Employees Or Workers - Other Gender Member - On Health And Safety Measures Member - Workers Member}",
    "Percentage Of Trained Employees Or Workers - Gender Member - On Health And Safety Measures Member - Workers Member": "0",
    "Number Of Trained Employees Or Workers - Gender Member - On Skill Upgradation Member - Workers Member":
        "{Number Of Trained Employees Or Workers - Male Member - On Skill Upgradation Member - Workers Member} + {Number Of Trained Employees Or Workers - Female Member - On Skill Upgradation Member - Workers Member} + {Number Of Trained Employees Or Workers - Other Gender Member - On Skill Upgradation Member - Workers Member}",
    "Percentage Of Trained Employees Or Workers - Gender Member - On Skill Upgradation Member - Workers Member": "0",
    "Number Of Trained Employees Or Workers - Gender Member - Total Employees And Workers Member - Workers Member - Previous Year":
        "{Number Of Trained Employees Or Workers - Male Member - Total Employees And Workers Member - Workers Member - Previous Year} + {Number Of Trained Employees Or Workers - Female Member - Total Employees And Workers Member - Workers Member - Previous Year} + {Number Of Trained Employees Or Workers - Other Gender Member - Total Employees And Workers Member - Workers Member - Previous Year}",
    "Number Of Trained Employees Or Workers - Gender Member - On Health And Safety Measures Member - Workers Member - Previous Year":
        "{Number Of Trained Employees Or Workers - Male Member - On Health And Safety Measures Member - Workers Member - Previous Year} + {Number Of Trained Employees Or Workers - Female Member - On Health And Safety Measures Member - Workers Member - Previous Year} + {Number Of Trained Employees Or Workers - Other Gender Member - On Health And Safety Measures Member - Workers Member - Previous Year}",
    "Percentage Of Trained Employees Or Workers - Gender Member - On Health And Safety Measures Member - Workers Member - Previous Year": "0",
    "Number Of Trained Employees Or Workers - Gender Member - On Skill Upgradation Member - Workers Member - Previous Year":
        "{Number Of Trained Employees Or Workers - Male Member - On Skill Upgradation Member - Workers Member - Previous Year} + {Number Of Trained Employees Or Workers - Female Member - On Skill Upgradation Member - Workers Member - Previous Year} + {Number Of Trained Employees Or Workers - Other Gender Member - On Skill Upgradation Member - Workers Member - Previous Year}",
    "Percentage Of Trained Employees Or Workers - Gender Member - On Skill Upgradation Member - Workers Member - Previous Year": "0",
    "Total Number Of Employees Or Workers For Performance And Career Development - Male Member - Employees Member":
        "{Total Number Of Employees Or Workers For Performance And Career Development - Gender Member - Employees Member} - {Total Number Of Employees Or Workers For Performance And Career Development - Female Member - Employees Member} - {Total Number Of Employees Or Workers For Performance And Career Development - Other Gender Member - Employees Member}",
    "Number Of Employees Or Worker For Performance And Career Development - Male Member - Employees Member":
        "{Number Of Employees Or Worker For Performance And Career Development - Gender Member - Employees Member} - {Number Of Employees Or Worker For Performance And Career Development - Female Member - Employees Member} - {Number Of Employees Or Worker For Performance And Career Development - Other Gender Member - Employees Member}",
    "Percentage Of Employees Or Worker For Performance And Career Development - Male Member - Employees Member": "0",
    "Total Number Of Employees Or Workers For Performance And Career Development - Male Member - Employees Member - Previous Year":
        "{Total Number Of Employees Or Workers For Performance And Career Development - Gender Member - Employees Member - Previous Year} - {Total Number Of Employees Or Workers For Performance And Career Development - Female Member - Employees Member - Previous Year} - {Total Number Of Employees Or Workers For Performance And Career Development - Other Gender Member - Employees Member - Previous Year}",
    "Number Of Employees Or Worker For Performance And Career Development - Male Member - Employees Member - Previous Year":
        "{Number Of Employees Or Worker For Performance And Career Development - Gender Member - Employees Member - Previous Year} - {Number Of Employees Or Worker For Performance And Career Development - Female Member - Employees Member - Previous Year} - {Number Of Employees Or Worker For Performance And Career Development - Other Gender Member - Employees Member - Previous Year}",
    "Percentage Of Employees Or Worker For Performance And Career Development - Male Member - Employees Member - Previous Year": "0",
    "Total Number Of Employees Or Workers For Performance And Career Development - Female Member - Employees Member":
        "{Total Number Of Employees Or Workers For Performance And Career Development - Gender Member - Employees Member} - {Total Number Of Employees Or Workers For Performance And Career Development - Male Member - Employees Member} - {Total Number Of Employees Or Workers For Performance And Career Development - Other Gender Member - Employees Member}",
    "Number Of Employees Or Worker For Performance And Career Development - Female Member - Employees Member":
        "{Number Of Employees Or Worker For Performance And Career Development - Gender Member - Employees Member} - {Number Of Employees Or Worker For Performance And Career Development - Male Member - Employees Member} - {Number Of Employees Or Worker For Performance And Career Development - Other Gender Member - Employees Member}",
    "Percentage Of Employees Or Worker For Performance And Career Development - Female Member - Employees Member": "0",
    "Total Number Of Employees Or Workers For Performance And Career Development - Female Member - Employees Member - Previous Year":
        "{Total Number Of Employees Or Workers For Performance And Career Development - Gender Member - Employees Member - Previous Year} - {Total Number Of Employees Or Workers For Performance And Career Development - Male Member - Employees Member - Previous Year} - {Total Number Of Employees Or Workers For Performance And Career Development - Other Gender Member - Employees Member - Previous Year}",
    "Number Of Employees Or Worker For Performance And Career Development - Female Member - Employees Member - Previous Year":
        "{Number Of Employees Or Worker For Performance And Career Development - Gender Member - Employees Member - Previous Year} - {Number Of Employees Or Worker For Performance And Career Development - Male Member - Employees Member - Previous Year} - {Number Of Employees Or Worker For Performance And Career Development - Other Gender Member - Employees Member - Previous Year}",
    "Percentage Of Employees Or Worker For Performance And Career Development - Female Member - Employees Member - Previous Year": "0",
    "Total Number Of Employees Or Workers For Performance And Career Development - Other Gender Member - Employees Member":
        "{Total Number Of Employees Or Workers For Performance And Career Development - Gender Member - Employees Member} - {Total Number Of Employees Or Workers For Performance And Career Development - Male Member - Employees Member} - {Total Number Of Employees Or Workers For Performance And Career Development - Female Member - Employees Member}",
    "Number Of Employees Or Worker For Performance And Career Development - Other Gender Member - Employees Member":
        "{Number Of Employees Or Worker For Performance And Career Development - Gender Member - Employees Member} - {Number Of Employees Or Worker For Performance And Career Development - Male Member - Employees Member} - {Number Of Employees Or Worker For Performance And Career Development - Female Member - Employees Member}",
    "Percentage Of Employees Or Worker For Performance And Career Development - Other Gender Member - Employees Member": "0",
    "Total Number Of Employees Or Workers For Performance And Career Development - Other Gender Member - Employees Member - Previous Year":
        "{Total Number Of Employees Or Workers For Performance And Career Development - Gender Member - Employees Member - Previous Year} - {Total Number Of Employees Or Workers For Performance And Career Development - Male Member - Employees Member - Previous Year} - {Total Number Of Employees Or Workers For Performance And Career Development - Female Member - Employees Member - Previous Year}",
    "Number Of Employees Or Worker For Performance And Career Development - Other Gender Member - Employees Member - Previous Year":
        "{Number Of Employees Or Worker For Performance And Career Development - Gender Member - Employees Member - Previous Year} - {Number Of Employees Or Worker For Performance And Career Development - Male Member - Employees Member - Previous Year} - {Number Of Employees Or Worker For Performance And Career Development - Female Member - Employees Member - Previous Year}",
    "Percentage Of Employees Or Worker For Performance And Career Development - Other Gender Member - Employees Member - Previous Year": "0",
    "Total Number Of Employees Or Workers For Performance And Career Development - Gender Member - Employees Member": "0",
    "Number Of Employees Or Worker For Performance And Career Development - Gender Member - Employees Member":
        "{Number Of Employees Or Worker For Performance And Career Development - Male Member - Employees Member} + {Number Of Employees Or Worker For Performance And Career Development - Female Member - Employees Member} + {Number Of Employees Or Worker For Performance And Career Development - Other Gender Member - Employees Member}",
    "Percentage Of Employees Or Worker For Performance And Career Development - Gender Member - Employees Member": "0",
    "Total Number Of Employees Or Workers For Performance And Career Development - Gender Member - Employees Member - Previous Year": "0",
    "Number Of Employees Or Worker For Performance And Career Development - Gender Member - Employees Member - Previous Year":
        "{Number Of Employees Or Worker For Performance And Career Development - Male Member - Employees Member - Previous Year} + {Number Of Employees Or Worker For Performance And Career Development - Female Member - Employees Member - Previous Year} + {Number Of Employees Or Worker For Performance And Career Development - Other Gender Member - Employees Member - Previous Year}",
    "Percentage Of Employees Or Worker For Performance And Career Development - Gender Member - Employees Member - Previous Year": "0",
    "Total Number Of Employees Or Workers For Performance And Career Development - Male Member - Workers Member":
        "{Total Number Of Employees Or Workers For Performance And Career Development - Gender Member - Workers Member} - {Total Number Of Employees Or Workers For Performance And Career Development - Female Member - Workers Member} - {Total Number Of Employees Or Workers For Performance And Career Development - Other Gender Member - Workers Member}",
    "Number Of Employees Or Worker For Performance And Career Development - Male Member - Workers Member":
        "{Number Of Employees Or Worker For Performance And Career Development - Gender Member - Workers Member} - {Number Of Employees Or Worker For Performance And Career Development - Female Member - Workers Member} - {Number Of Employees Or Worker For Performance And Career Development - Other Gender Member - Workers Member}",
    "Percentage Of Employees Or Worker For Performance And Career Development - Male Member - Workers Member": "0",
    "Total Number Of Employees Or Workers For Performance And Career Development - Male Member - Workers Member - Previous Year":
        "{Total Number Of Employees Or Workers For Performance And Career Development - Gender Member - Workers Member - Previous Year} - {Total Number Of Employees Or Workers For Performance And Career Development - Female Member - Workers Member - Previous Year} - {Total Number Of Employees Or Workers For Performance And Career Development - Other Gender Member - Workers Member - Previous Year}",
    "Number Of Employees Or Worker For Performance And Career Development - Male Member - Workers Member - Previous Year":
        "{Number Of Employees Or Worker For Performance And Career Development - Gender Member - Workers Member - Previous Year} - {Number Of Employees Or Worker For Performance And Career Development - Female Member - Workers Member - Previous Year} - {Number Of Employees Or Worker For Performance And Career Development - Other Gender Member - Workers Member - Previous Year}",
    "Percentage Of Employees Or Worker For Performance And Career Development - Male Member - Workers Member - Previous Year": "0",
    "Total Number Of Employees Or Workers For Performance And Career Development - Female Member - Workers Member":
        "{Total Number Of Employees Or Workers For Performance And Career Development - Gender Member - Workers Member} - {Total Number Of Employees Or Workers For Performance And Career Development - Male Member - Workers Member} - {Total Number Of Employees Or Workers For Performance And Career Development - Other Gender Member - Workers Member}",
    "Number Of Employees Or Worker For Performance And Career Development - Female Member - Workers Member":
        "{Number Of Employees Or Worker For Performance And Career Development - Gender Member - Workers Member} - {Number Of Employees Or Worker For Performance And Career Development - Male Member - Workers Member} - {Number Of Employees Or Worker For Performance And Career Development - Other Gender Member - Workers Member}",
    "Percentage Of Employees Or Worker For Performance And Career Development - Female Member - Workers Member": "0",
    "Total Number Of Employees Or Workers For Performance And Career Development - Female Member - Workers Member - Previous Year":
        "{Total Number Of Employees Or Workers For Performance And Career Development - Gender Member - Workers Member - Previous Year} - {Total Number Of Employees Or Workers For Performance And Career Development - Male Member - Workers Member - Previous Year} - {Total Number Of Employees Or Workers For Performance And Career Development - Other Gender Member - Workers Member - Previous Year}",
    "Number Of Employees Or Worker For Performance And Career Development - Female Member - Workers Member - Previous Year":
        "{Number Of Employees Or Worker For Performance And Career Development - Gender Member - Workers Member - Previous Year} - {Number Of Employees Or Worker For Performance And Career Development - Male Member - Workers Member - Previous Year} - {Number Of Employees Or Worker For Performance And Career Development - Other Gender Member - Workers Member - Previous Year}",
    "Percentage Of Employees Or Worker For Performance And Career Development - Female Member - Workers Member - Previous Year": "0",
    "Total Number Of Employees Or Workers For Performance And Career Development - Other Gender Member - Workers Member":
        "{Total Number Of Employees Or Workers For Performance And Career Development - Gender Member - Workers Member} - {Total Number Of Employees Or Workers For Performance And Career Development - Male Member - Workers Member} - {Total Number Of Employees Or Workers For Performance And Career Development - Female Member - Workers Member}",
    "Number Of Employees Or Worker For Performance And Career Development - Other Gender Member - Workers Member":
        "{Number Of Employees Or Worker For Performance And Career Development - Gender Member - Workers Member} - {Number Of Employees Or Worker For Performance And Career Development - Male Member - Workers Member} - {Number Of Employees Or Worker For Performance And Career Development - Female Member - Workers Member}",
    "Percentage Of Employees Or Worker For Performance And Career Development - Other Gender Member - Workers Member": "0",
    "Total Number Of Employees Or Workers For Performance And Career Development - Other Gender Member - Workers Member - Previous Year":
        "{Total Number Of Employees Or Workers For Performance And Career Development - Gender Member - Workers Member - Previous Year} - {Total Number Of Employees Or Workers For Performance And Career Development - Male Member - Workers Member - Previous Year} - {Total Number Of Employees Or Workers For Performance And Career Development - Female Member - Workers Member - Previous Year}",
    "Number Of Employees Or Worker For Performance And Career Development - Other Gender Member - Workers Member - Previous Year":
        "{Number Of Employees Or Worker For Performance And Career Development - Gender Member - Workers Member - Previous Year} - {Number Of Employees Or Worker For Performance And Career Development - Male Member - Workers Member - Previous Year} - {Number Of Employees Or Worker For Performance And Career Development - Female Member - Workers Member - Previous Year}",
    "Percentage Of Employees Or Worker For Performance And Career Development - Other Gender Member - Workers Member - Previous Year": "0",
    "Total Number Of Employees Or Workers For Performance And Career Development - Gender Member - Workers Member": "0",
    "Number Of Employees Or Worker For Performance And Career Development - Gender Member - Workers Member":
        "{Number Of Employees Or Worker For Performance And Career Development - Male Member - Workers Member} + {Number Of Employees Or Worker For Performance And Career Development - Female Member - Workers Member} + {Number Of Employees Or Worker For Performance And Career Development - Other Gender Member - Workers Member}",
    "Percentage Of Employees Or Worker For Performance And Career Development - Gender Member - Workers Member": "0",
    "Total Number Of Employees Or Workers For Performance And Career Development - Gender Member - Workers Member - Previous Year": "0",
    "Number Of Employees Or Worker For Performance And Career Development - Gender Member - Workers Member - Previous Year":
        "{Number Of Employees Or Worker For Performance And Career Development - Male Member - Workers Member - Previous Year} + {Number Of Employees Or Worker For Performance And Career Development - Female Member - Workers Member - Previous Year} + {Number Of Employees Or Worker For Performance And Career Development - Other Gender Member - Workers Member - Previous Year}",
    "Percentage Of Employees Or Worker For Performance And Career Development - Gender Member - Workers Member - Previous Year": "0",
    "Lost Time Injury Frequency Rate Per One Million Person Hours Worked - Employees Member": "0",
    "Lost Time Injury Frequency Rate Per One Million Person Hours Worked - Employees Member - Previous Year": "0",
    "Lost Time Injury Frequency Rate Per One Million Person Hours Worked - Workers Member": "0",
    "Lost Time Injury Frequency Rate Per One Million Person Hours Worked - Workers Member - Previous Year": "0",
    "Total Recordable Work Related Injuries - Employees Member": "0",
    "Total Recordable Work Related Injuries - Employees Member - Previous Year": "0",
    "Total Recordable Work Related Injuries - Workers Member": "0",
    "Total Recordable Work Related Injuries - Workers Member - Previous Year": "0",
    "Number Of Fatalities - Employees Member": "0",
    "Number Of Fatalities - Employees Member - Previous Year": "0",
    "Number Of Fatalities - Workers Member": "0",
    "Number Of Fatalities - Workers Member - Previous Year": "0",
    "High Consequence Work Related Injury Or Ill Health Excluding Fatalities - Employees Member": "0",
    "High Consequence Work Related Injury Or Ill Health Excluding Fatalities - Employees Member - Previous Year": "0",
    "High Consequence Work Related Injury Or Ill Health Excluding Fatalities - Workers Member": "0",
    "High Consequence Work Related Injury Or Ill Health Excluding Fatalities - Workers Member - Previous Year": "0",
    "Number Of Complaints Filed During The Year - Working Conditions Complaints Member": "0",
    "Number Of Complaints Pending Resolution At The End Of Year - Working Conditions Complaints Member": "0",
    "Number Of Complaints Filed During The Year - Working Conditions Complaints Member - Previous Year": "0",
    "Number Of Complaints Pending Resolution At The End Of Year - Working Conditions Complaints Member - Previous Year": "0",
    "Number Of Complaints Filed During The Year - Health Safety Complaints Member": "0",
    "Number Of Complaints Pending Resolution At The End Of Year - Health Safety Complaints Member": "0",
    "Number Of Complaints Filed During The Year - Health Safety Complaints Member - Previous Year": "0",
    "Number Of Complaints Pending Resolution At The End Of Year - Health Safety Complaints Member - Previous Year": "0",
    "Total Number Of Employees Or Workers For Training On Human Rights Issues - Permanent Employees Member": "0",
    "Number Of Employees Or Workers Covered For Provided Training On Human Rights Issues - Permanent Employees Member": "0",
    "Percentage Of Employees Or Workers Covered For Provided Training On Human Rights Issues - Permanent Employees Member": "0",
    "Total Number Of Employees Or Workers For Training On Human Rights Issues - Other Than Permanent Employees Member": "0",
    "Number Of Employees Or Workers Covered For Provided Training On Human Rights Issues - Other Than Permanent Employees Member": "0",
    "Percentage Of Employees Or Workers Covered For Provided Training On Human Rights Issues - Other Than Permanent Employees Member": "0",
    "Total Number Of Employees Or Workers For Training On Human Rights Issues - Employees Member": "0",
    "Number Of Employees Or Workers Covered For Provided Training On Human Rights Issues - Employees Member": "0",
    "Percentage Of Employees Or Workers Covered For Provided Training On Human Rights Issues - Employees Member": "0",
    "Total Number Of Employees Or Workers For Training On Human Rights Issues - Permanent Employees Member - Previous Year": "0",
    "Number Of Employees Or Workers Covered For Provided Training On Human Rights Issues - Permanent Employees Member - Previous Year": "0",
    "Percentage Of Employees Or Workers Covered For Provided Training On Human Rights Issues - Permanent Employees Member - Previous Year": "0",
    "Total Number Of Employees Or Workers For Training On Human Rights Issues - Other Than Permanent Employees Member - Previous Year": "0",
    "Number Of Employees Or Workers Covered For Provided Training On Human Rights Issues - Other Than Permanent Employees Member - Previous Year": "0",
    "Percentage Of Employees Or Workers Covered For Provided Training On Human Rights Issues - Other Than Permanent Employees Member - Previous Year": "0",
    "Total Number Of Employees Or Workers For Training On Human Rights Issues - Employees Member - Previous Year": "0",
    "Number Of Employees Or Workers Covered For Provided Training On Human Rights Issues - Employees Member - Previous Year": "0",
    "Percentage Of Employees Or Workers Covered For Provided Training On Human Rights Issues - Employees Member - Previous Year": "0",
    "Total Number Of Employees Or Workers For Training On Human Rights Issues - Permanent Workers Member": "0",
    "Number Of Employees Or Workers Covered For Provided Training On Human Rights Issues - Permanent Workers Member": "0",
    "Percentage Of Employees Or Workers Covered For Provided Training On Human Rights Issues - Permanent Workers Member": "0",
    "Total Number Of Employees Or Workers For Training On Human Rights Issues - Other Than Permanent Workers Member": "0",
    "Number Of Employees Or Workers Covered For Provided Training On Human Rights Issues - Other Than Permanent Workers Member": "0",
    "Percentage Of Employees Or Workers Covered For Provided Training On Human Rights Issues - Other Than Permanent Workers Member": "0",
    "Total Number Of Employees Or Workers For Training On Human Rights Issues - Workers Member": "0",
    "Number Of Employees Or Workers Covered For Provided Training On Human Rights Issues - Workers Member": "0",
    "Percentage Of Employees Or Workers Covered For Provided Training On Human Rights Issues - Workers Member": "0",
    "Total Number Of Employees Or Workers For Training On Human Rights Issues - Permanent Workers Member - Previous Year": "0",
    "Number Of Employees Or Workers Covered For Provided Training On Human Rights Issues - Permanent Workers Member - Previous Year": "0",
    "Percentage Of Employees Or Workers Covered For Provided Training On Human Rights Issues - Permanent Workers Member - Previous Year": "0",
    "Total Number Of Employees Or Workers For Training On Human Rights Issues - Other Than Permanent Workers Member - Previous Year": "0",
    "Number Of Employees Or Workers Covered For Provided Training On Human Rights Issues - Other Than Permanent Workers Member - Previous Year": "0",
    "Percentage Of Employees Or Workers Covered For Provided Training On Human Rights Issues - Other Than Permanent Workers Member - Previous Year": "0",
    "Total Number Of Employees Or Workers For Training On Human Rights Issues - Workers Member - Previous Year": "0",
    "Number Of Employees Or Workers Covered For Provided Training On Human Rights Issues - Workers Member - Previous Year": "0",
    "Percentage Of Employees Or Workers Covered For Provided Training On Human Rights Issues - Workers Member - Previous Year": "0",
    "Number Of Employees Or Workers Related To Minimum Wages - Total Minimum Wages Member - Gender Member - Permanent Employees Member":
        "{Number Of Employees Or Workers Related To Minimum Wages - Equal To Minimum Wage Member - Gender Member - Permanent Employees Member} + {Number Of Employees Or Workers Related To Minimum Wages - More Than Minimum Wage Member - Gender Member - Permanent Employees Member}",
    "Number Of Employees Or Workers Related To Minimum Wages - Total Minimum Wages Member - Male Member - Permanent Employees Member":
        "{Number Of Employees Or Workers Related To Minimum Wages - Total Minimum Wages Member - Gender Member - Permanent Employees Member} - {Number Of Employees Or Workers Related To Minimum Wages - Total Minimum Wages Member - Female Member - Permanent Employees Member} - {Number Of Employees Or Workers Related To Minimum Wages - Total Minimum Wages Member - Other Gender Member - Permanent Employees Member}",
    "Number Of Employees Or Workers Related To Minimum Wages - Total Minimum Wages Member - Female Member - Permanent Employees Member":
        "{Number Of Employees Or Workers Related To Minimum Wages - Total Minimum Wages Member - Gender Member - Permanent Employees Member} - {Number Of Employees Or Workers Related To Minimum Wages - Total Minimum Wages Member - Male Member - Permanent Employees Member} - {Number Of Employees Or Workers Related To Minimum Wages - Total Minimum Wages Member - Other Gender Member - Permanent Employees Member}",
    "Number Of Employees Or Workers Related To Minimum Wages - Total Minimum Wages Member - Other Gender Member - Permanent Employees Member":
        "{Number Of Employees Or Workers Related To Minimum Wages - Total Minimum Wages Member - Gender Member - Permanent Employees Member} - {Number Of Employees Or Workers Related To Minimum Wages - Total Minimum Wages Member - Male Member - Permanent Employees Member} - {Number Of Employees Or Workers Related To Minimum Wages - Total Minimum Wages Member - Female Member - Permanent Employees Member}",
    "Number Of Employees Or Workers Related To Minimum Wages - Equal To Minimum Wage Member - Gender Member - Permanent Employees Member":
        "{Number Of Employees Or Workers Related To Minimum Wages - Total Minimum Wages Member - Gender Member - Permanent Employees Member} - {Number Of Employees Or Workers Related To Minimum Wages - More Than Minimum Wage Member - Gender Member - Permanent Employees Member}",
    "Percentage Of Employees Or Workers Related To Minimum Wages - Equal To Minimum Wage Member - Gender Member - Permanent Employees Member":
        "({Number Of Employees Or Workers Related To Minimum Wages - Equal To Minimum Wage Member - Gender Member - Permanent Employees Member} / {Number Of Employees Or Workers Related To Minimum Wages - Total Minimum Wages Member - Gender Member - Permanent Employees Member}) * 100",
    "Number Of Employees Or Workers Related To Minimum Wages - Equal To Minimum Wage Member - Male Member - Permanent Employees Member":
        "{Number Of Employees Or Workers Related To Minimum Wages - Equal To Minimum Wage Member - Gender Member - Permanent Employees Member} - {Number Of Employees Or Workers Related To Minimum Wages - Equal To Minimum Wage Member - Female Member - Permanent Employees Member} - {Number Of Employees Or Workers Related To Minimum Wages - Equal To Minimum Wage Member - Other Gender Member - Permanent Employees Member}",
    "Percentage Of Employees Or Workers Related To Minimum Wages - Equal To Minimum Wage Member - Male Member - Permanent Employees Member": "0",
    "Number Of Employees Or Workers Related To Minimum Wages - Equal To Minimum Wage Member - Female Member - Permanent Employees Member":
        "{Number Of Employees Or Workers Related To Minimum Wages - Equal To Minimum Wage Member - Gender Member - Permanent Employees Member} - {Number Of Employees Or Workers Related To Minimum Wages - Equal To Minimum Wage Member - Male Member - Permanent Employees Member} - {Number Of Employees Or Workers Related To Minimum Wages - Equal To Minimum Wage Member - Other Gender Member - Permanent Employees Member}",
    "Percentage Of Employees Or Workers Related To Minimum Wages - Equal To Minimum Wage Member - Female Member - Permanent Employees Member": "0",
    "Number Of Employees Or Workers Related To Minimum Wages - Equal To Minimum Wage Member - Other Gender Member - Permanent Employees Member":
        "{Number Of Employees Or Workers Related To Minimum Wages - Equal To Minimum Wage Member - Gender Member - Permanent Employees Member} - {Number Of Employees Or Workers Related To Minimum Wages - Equal To Minimum Wage Member - Male Member - Permanent Employees Member} - {Number Of Employees Or Workers Related To Minimum Wages - Equal To Minimum Wage Member - Female Member - Permanent Employees Member}",
    "Percentage Of Employees Or Workers Related To Minimum Wages - Equal To Minimum Wage Member - Other Gender Member - Permanent Employees Member": "0",
    "Number Of Employees Or Workers Related To Minimum Wages - More Than Minimum Wage Member - Gender Member - Permanent Employees Member":
        "{Number Of Employees Or Workers Related To Minimum Wages - Total Minimum Wages Member - Gender Member - Permanent Employees Member} - {Number Of Employees Or Workers Related To Minimum Wages - Equal To Minimum Wage Member - Gender Member - Permanent Employees Member}",
    "Percentage Of Employees Or Workers Related To Minimum Wages - More Than Minimum Wage Member - Gender Member - Permanent Employees Member":
        "({Number Of Employees Or Workers Related To Minimum Wages - More Than Minimum Wage Member - Gender Member - Permanent Employees Member} / {Number Of Employees Or Workers Related To Minimum Wages - Total Minimum Wages Member - Gender Member - Permanent Employees Member}) * 100",
    "Number Of Employees Or Workers Related To Minimum Wages - More Than Minimum Wage Member - Male Member - Permanent Employees Member":
        "{Number Of Employees Or Workers Related To Minimum Wages - More Than Minimum Wage Member - Gender Member - Permanent Employees Member} - {Number Of Employees Or Workers Related To Minimum Wages - More Than Minimum Wage Member - Female Member - Permanent Employees Member} - {Number Of Employees Or Workers Related To Minimum Wages - More Than Minimum Wage Member - Other Gender Member - Permanent Employees Member}",
    "Percentage Of Employees Or Workers Related To Minimum Wages - More Than Minimum Wage Member - Male Member - Permanent Employees Member": "0",
    "Number Of Employees Or Workers Related To Minimum Wages - More Than Minimum Wage Member - Female Member - Permanent Employees Member":
        "{Number Of Employees Or Workers Related To Minimum Wages - More Than Minimum Wage Member - Gender Member - Permanent Employees Member} - {Number Of Employees Or Workers Related To Minimum Wages - More Than Minimum Wage Member - Male Member - Permanent Employees Member} - {Number Of Employees Or Workers Related To Minimum Wages - More Than Minimum Wage Member - Other Gender Member - Permanent Employees Member}",
    "Percentage Of Employees Or Workers Related To Minimum Wages - More Than Minimum Wage Member - Female Member - Permanent Employees Member": "0",
    "Number Of Employees Or Workers Related To Minimum Wages - More Than Minimum Wage Member - Other Gender Member - Permanent Employees Member":
        "{Number Of Employees Or Workers Related To Minimum Wages - More Than Minimum Wage Member - Gender Member - Permanent Employees Member} - {Number Of Employees Or Workers Related To Minimum Wages - More Than Minimum Wage Member - Male Member - Permanent Employees Member} - {Number Of Employees Or Workers Related To Minimum Wages - More Than Minimum Wage Member - Female Member - Permanent Employees Member}",
    "Percentage Of Employees Or Workers Related To Minimum Wages - More Than Minimum Wage Member - Other Gender Member - Permanent Employees Member": "0",
    "Number Of Employees Or Workers Related To Minimum Wages - Total Minimum Wages Member - Gender Member - Permanent Employees Member - Previous Year":
        "{Number Of Employees Or Workers Related To Minimum Wages - Equal To Minimum Wage Member - Gender Member - Permanent Employees Member - Previous Year} + {Number Of Employees Or Workers Related To Minimum Wages - More Than Minimum Wage Member - Gender Member - Permanent Employees Member - Previous Year}",
    "Number Of Employees Or Workers Related To Minimum Wages - Total Minimum Wages Member - Male Member - Permanent Employees Member - Previous Year":
        "{Number Of Employees Or Workers Related To Minimum Wages - Total Minimum Wages Member - Gender Member - Permanent Employees Member - Previous Year} - {Number Of Employees Or Workers Related To Minimum Wages - Total Minimum Wages Member - Female Member - Permanent Employees Member - Previous Year} - {Number Of Employees Or Workers Related To Minimum Wages - Total Minimum Wages Member - Other Gender Member - Permanent Employees Member - Previous Year}",
    "Number Of Employees Or Workers Related To Minimum Wages - Total Minimum Wages Member - Female Member - Permanent Employees Member - Previous Year":
        "{Number Of Employees Or Workers Related To Minimum Wages - Total Minimum Wages Member - Gender Member - Permanent Employees Member - Previous Year} - {Number Of Employees Or Workers Related To Minimum Wages - Total Minimum Wages Member - Male Member - Permanent Employees Member - Previous Year} - {Number Of Employees Or Workers Related To Minimum Wages - Total Minimum Wages Member - Other Gender Member - Permanent Employees Member - Previous Year}",
    "Number Of Employees Or Workers Related To Minimum Wages - Total Minimum Wages Member - Other Gender Member - Permanent Employees Member - Previous Year":
        "{Number Of Employees Or Workers Related To Minimum Wages - Total Minimum Wages Member - Gender Member - Permanent Employees Member - Previous Year} - {Number Of Employees Or Workers Related To Minimum Wages - Total Minimum Wages Member - Male Member - Permanent Employees Member - Previous Year} - {Number Of Employees Or Workers Related To Minimum Wages - Total Minimum Wages Member - Female Member - Permanent Employees Member - Previous Year}",
    "Number Of Employees Or Workers Related To Minimum Wages - Equal To Minimum Wage Member - Gender Member - Permanent Employees Member - Previous Year":
        "{Number Of Employees Or Workers Related To Minimum Wages - Total Minimum Wages Member - Gender Member - Permanent Employees Member - Previous Year} - {Number Of Employees Or Workers Related To Minimum Wages - More Than Minimum Wage Member - Gender Member - Permanent Employees Member - Previous Year}",
    "Percentage Of Employees Or Workers Related To Minimum Wages - Equal To Minimum Wage Member - Gender Member - Permanent Employees Member - Previous Year":
        "({Number Of Employees Or Workers Related To Minimum Wages - Equal To Minimum Wage Member - Gender Member - Permanent Employees Member - Previous Year} / {Number Of Employees Or Workers Related To Minimum Wages - Total Minimum Wages Member - Gender Member - Permanent Employees Member - Previous Year}) * 100",
    "Number Of Employees Or Workers Related To Minimum Wages - More Than Minimum Wage Member - Gender Member - Permanent Employees Member - Previous Year":
        "{Number Of Employees Or Workers Related To Minimum Wages - Total Minimum Wages Member - Gender Member - Permanent Employees Member - Previous Year} - {Number Of Employees Or Workers Related To Minimum Wages - Equal To Minimum Wage Member - Gender Member - Permanent Employees Member - Previous Year}",
    "Percentage Of Employees Or Workers Related To Minimum Wages - More Than Minimum Wage Member - Gender Member - Permanent Employees Member - Previous Year":
        "({Number Of Employees Or Workers Related To Minimum Wages - More Than Minimum Wage Member - Gender Member - Permanent Employees Member - Previous Year} / {Number Of Employees Or Workers Related To Minimum Wages - Total Minimum Wages Member - Gender Member - Permanent Employees Member - Previous Year}) * 100",
    "Number Of Employees Or Workers Related To Minimum Wages - Equal To Minimum Wage Member - Male Member - Permanent Employees Member - Previous Year":
        "{Number Of Employees Or Workers Related To Minimum Wages - Equal To Minimum Wage Member - Gender Member - Permanent Employees Member - Previous Year} - {Number Of Employees Or Workers Related To Minimum Wages - Equal To Minimum Wage Member - Female Member - Permanent Employees Member - Previous Year} - {Number Of Employees Or Workers Related To Minimum Wages - Equal To Minimum Wage Member - Other Gender Member - Permanent Employees Member - Previous Year}",
    "Percentage Of Employees Or Workers Related To Minimum Wages - Equal To Minimum Wage Member - Male Member - Permanent Employees Member - Previous Year": "0",
    "Number Of Employees Or Workers Related To Minimum Wages - More Than Minimum Wage Member - Male Member - Permanent Employees Member - Previous Year":
        "{Number Of Employees Or Workers Related To Minimum Wages - More Than Minimum Wage Member - Gender Member - Permanent Employees Member - Previous Year} - {Number Of Employees Or Workers Related To Minimum Wages - More Than Minimum Wage Member - Female Member - Permanent Employees Member - Previous Year} - {Number Of Employees Or Workers Related To Minimum Wages - More Than Minimum Wage Member - Other Gender Member - Permanent Employees Member - Previous Year}",
    "Percentage Of Employees Or Workers Related To Minimum Wages - More Than Minimum Wage Member - Male Member - Permanent Employees Member - Previous Year": "0",
    "Number Of Employees Or Workers Related To Minimum Wages - Equal To Minimum Wage Member - Female Member - Permanent Employees Member - Previous Year":
        "{Number Of Employees Or Workers Related To Minimum Wages - Equal To Minimum Wage Member - Gender Member - Permanent Employees Member - Previous Year} - {Number Of Employees Or Workers Related To Minimum Wages - Equal To Minimum Wage Member - Male Member - Permanent Employees Member - Previous Year} - {Number Of Employees Or Workers Related To Minimum Wages - Equal To Minimum Wage Member - Other Gender Member - Permanent Employees Member - Previous Year}",
    "Percentage Of Employees Or Workers Related To Minimum Wages - Equal To Minimum Wage Member - Female Member - Permanent Employees Member - Previous Year": "0",
    "Number Of Employees Or Workers Related To Minimum Wages - More Than Minimum Wage Member - Female Member - Permanent Employees Member - Previous Year":
        "{Number Of Employees Or Workers Related To Minimum Wages - More Than Minimum Wage Member - Gender Member - Permanent Employees Member - Previous Year} - {Number Of Employees Or Workers Related To Minimum Wages - More Than Minimum Wage Member - Male Member - Permanent Employees Member - Previous Year} - {Number Of Employees Or Workers Related To Minimum Wages - More Than Minimum Wage Member - Other Gender Member - Permanent Employees Member - Previous Year}",
    "Percentage Of Employees Or Workers Related To Minimum Wages - More Than Minimum Wage Member - Female Member - Permanent Employees Member - Previous Year": "0",
    "Number Of Employees Or Workers Related To Minimum Wages - Equal To Minimum Wage Member - Other Gender Member - Permanent Employees Member - Previous Year":
        "{Number Of Employees Or Workers Related To Minimum Wages - Equal To Minimum Wage Member - Gender Member - Permanent Employees Member - Previous Year} - {Number Of Employees Or Workers Related To Minimum Wages - Equal To Minimum Wage Member - Male Member - Permanent Employees Member - Previous Year} - {Number Of Employees Or Workers Related To Minimum Wages - Equal To Minimum Wage Member - Female Member - Permanent Employees Member - Previous Year}",
    "Percentage Of Employees Or Workers Related To Minimum Wages - Equal To Minimum Wage Member - Other Gender Member - Permanent Employees Member - Previous Year": "0",
    "Number Of Employees Or Workers Related To Minimum Wages - More Than Minimum Wage Member - Other Gender Member - Permanent Employees Member - Previous Year":
        "{Number Of Employees Or Workers Related To Minimum Wages - More Than Minimum Wage Member - Gender Member - Permanent Employees Member - Previous Year} - {Number Of Employees Or Workers Related To Minimum Wages - More Than Minimum Wage Member - Male Member - Permanent Employees Member - Previous Year} - {Number Of Employees Or Workers Related To Minimum Wages - More Than Minimum Wage Member - Female Member - Permanent Employees Member - Previous Year}",
    "Percentage Of Employees Or Workers Related To Minimum Wages - More Than Minimum Wage Member - Other Gender Member - Permanent Employees Member - Previous Year": "0",
    "Number Of Employees Or Workers Related To Minimum Wages - Total Minimum Wages Member - Gender Member - Other Than Permanent Employees Member":
        "{Number Of Employees Or Workers Related To Minimum Wages - Equal To Minimum Wage Member - Gender Member - Other Than Permanent Employees Member} + {Number Of Employees Or Workers Related To Minimum Wages - More Than Minimum Wage Member - Gender Member - Other Than Permanent Employees Member}",
    "Number Of Employees Or Workers Related To Minimum Wages - Total Minimum Wages Member - Male Member - Other Than Permanent Employees Member":
        "{Number Of Employees Or Workers Related To Minimum Wages - Total Minimum Wages Member - Gender Member - Other Than Permanent Employees Member} - {Number Of Employees Or Workers Related To Minimum Wages - Total Minimum Wages Member - Female Member - Other Than Permanent Employees Member} - {Number Of Employees Or Workers Related To Minimum Wages - Total Minimum Wages Member - Other Gender Member - Other Than Permanent Employees Member}",
    "Number Of Employees Or Workers Related To Minimum Wages - Total Minimum Wages Member - Female Member - Other Than Permanent Employees Member":
        "{Number Of Employees Or Workers Related To Minimum Wages - Total Minimum Wages Member - Gender Member - Other Than Permanent Employees Member} - {Number Of Employees Or Workers Related To Minimum Wages - Total Minimum Wages Member - Male Member - Other Than Permanent Employees Member} - {Number Of Employees Or Workers Related To Minimum Wages - Total Minimum Wages Member - Other Gender Member - Other Than Permanent Employees Member}",
    "Number Of Employees Or Workers Related To Minimum Wages - Total Minimum Wages Member - Other Gender Member - Other Than Permanent Employees Member":
        "{Number Of Employees Or Workers Related To Minimum Wages - Total Minimum Wages Member - Gender Member - Other Than Permanent Employees Member} - {Number Of Employees Or Workers Related To Minimum Wages - Total Minimum Wages Member - Male Member - Other Than Permanent Employees Member} - {Number Of Employees Or Workers Related To Minimum Wages - Total Minimum Wages Member - Female Member - Other Than Permanent Employees Member}",
    "Number Of Employees Or Workers Related To Minimum Wages - Equal To Minimum Wage Member - Gender Member - Other Than Permanent Employees Member":
        "{Number Of Employees Or Workers Related To Minimum Wages - Total Minimum Wages Member - Gender Member - Other Than Permanent Employees Member} - {Number Of Employees Or Workers Related To Minimum Wages - More Than Minimum Wage Member - Gender Member - Other Than Permanent Employees Member}",
    "Percentage Of Employees Or Workers Related To Minimum Wages - Equal To Minimum Wage Member - Gender Member - Other Than Permanent Employees Member":
        "({Number Of Employees Or Workers Related To Minimum Wages - Equal To Minimum Wage Member - Gender Member - Other Than Permanent Employees Member} / {Number Of Employees Or Workers Related To Minimum Wages - Total Minimum Wages Member - Gender Member - Other Than Permanent Employees Member}) * 100",
    "Number Of Employees Or Workers Related To Minimum Wages - Equal To Minimum Wage Member - Male Member - Other Than Permanent Employees Member":
        "{Number Of Employees Or Workers Related To Minimum Wages - Equal To Minimum Wage Member - Gender Member - Other Than Permanent Employees Member} - {Number Of Employees Or Workers Related To Minimum Wages - Equal To Minimum Wage Member - Female Member - Other Than Permanent Employees Member} - {Number Of Employees Or Workers Related To Minimum Wages - Equal To Minimum Wage Member - Other Gender Member - Other Than Permanent Employees Member}",
    "Percentage Of Employees Or Workers Related To Minimum Wages - Equal To Minimum Wage Member - Male Member - Other Than Permanent Employees Member": "0",
    "Number Of Employees Or Workers Related To Minimum Wages - Equal To Minimum Wage Member - Female Member - Other Than Permanent Employees Member":
        "{Number Of Employees Or Workers Related To Minimum Wages - Equal To Minimum Wage Member - Gender Member - Other Than Permanent Employees Member} - {Number Of Employees Or Workers Related To Minimum Wages - Equal To Minimum Wage Member - Male Member - Other Than Permanent Employees Member} - {Number Of Employees Or Workers Related To Minimum Wages - Equal To Minimum Wage Member - Other Gender Member - Other Than Permanent Employees Member}",
    "Percentage Of Employees Or Workers Related To Minimum Wages - Equal To Minimum Wage Member - Female Member - Other Than Permanent Employees Member": "0",
    "Number Of Employees Or Workers Related To Minimum Wages - Equal To Minimum Wage Member - Other Gender Member - Other Than Permanent Employees Member":
        "{Number Of Employees Or Workers Related To Minimum Wages - Equal To Minimum Wage Member - Gender Member - Other Than Permanent Employees Member} - {Number Of Employees Or Workers Related To Minimum Wages - Equal To Minimum Wage Member - Male Member - Other Than Permanent Employees Member} - {Number Of Employees Or Workers Related To Minimum Wages - Equal To Minimum Wage Member - Female Member - Other Than Permanent Employees Member}",
    "Percentage Of Employees Or Workers Related To Minimum Wages - Equal To Minimum Wage Member - Other Gender Member - Other Than Permanent Employees Member": "0",
    "Number Of Employees Or Workers Related To Minimum Wages - More Than Minimum Wage Member - Gender Member - Other Than Permanent Employees Member":
        "{Number Of Employees Or Workers Related To Minimum Wages - Total Minimum Wages Member - Gender Member - Other Than Permanent Employees Member} - {Number Of Employees Or Workers Related To Minimum Wages - Equal To Minimum Wage Member - Gender Member - Other Than Permanent Employees Member}",
    "Percentage Of Employees Or Workers Related To Minimum Wages - More Than Minimum Wage Member - Gender Member - Other Than Permanent Employees Member":
        "({Number Of Employees Or Workers Related To Minimum Wages - More Than Minimum Wage Member - Gender Member - Other Than Permanent Employees Member} / {Number Of Employees Or Workers Related To Minimum Wages - Total Minimum Wages Member - Gender Member - Other Than Permanent Employees Member}) * 100",
    "Number Of Employees Or Workers Related To Minimum Wages - More Than Minimum Wage Member - Male Member - Other Than Permanent Employees Member":
        "{Number Of Employees Or Workers Related To Minimum Wages - More Than Minimum Wage Member - Gender Member - Other Than Permanent Employees Member} - {Number Of Employees Or Workers Related To Minimum Wages - More Than Minimum Wage Member - Female Member - Other Than Permanent Employees Member} - {Number Of Employees Or Workers Related To Minimum Wages - More Than Minimum Wage Member - Other Gender Member - Other Than Permanent Employees Member}",
    "Percentage Of Employees Or Workers Related To Minimum Wages - More Than Minimum Wage Member - Male Member - Other Than Permanent Employees Member":
        "{Percentage Of Employees Or Workers Related To Minimum Wages - More Than Minimum Wage Member - Gender Member - Other Than Permanent Employees Member} - {Percentage Of Employees Or Workers Related To Minimum Wages - More Than Minimum Wage Member - Female Member - Other Than Permanent Employees Member} - {Percentage Of Employees Or Workers Related To Minimum Wages - More Than Minimum Wage Member - Other Gender Member - Other Than Permanent Employees Member}",
    "Number Of Employees Or Workers Related To Minimum Wages - More Than Minimum Wage Member - Female Member - Other Than Permanent Employees Member":
        "{Number Of Employees Or Workers Related To Minimum Wages - More Than Minimum Wage Member - Gender Member - Other Than Permanent Employees Member} - {Number Of Employees Or Workers Related To Minimum Wages - More Than Minimum Wage Member - Male Member - Other Than Permanent Employees Member} - {Number Of Employees Or Workers Related To Minimum Wages - More Than Minimum Wage Member - Other Gender Member - Other Than Permanent Employees Member}",
    "Percentage Of Employees Or Workers Related To Minimum Wages - More Than Minimum Wage Member - Female Member - Other Than Permanent Employees Member":
        "{Percentage Of Employees Or Workers Related To Minimum Wages - More Than Minimum Wage Member - Gender Member - Other Than Permanent Employees Member} - {Percentage Of Employees Or Workers Related To Minimum Wages - More Than Minimum Wage Member - Male Member - Other Than Permanent Employees Member} - {Percentage Of Employees Or Workers Related To Minimum Wages - More Than Minimum Wage Member - Other Gender Member - Other Than Permanent Employees Member}",
    "Number Of Employees Or Workers Related To Minimum Wages - More Than Minimum Wage Member - Other Gender Member - Other Than Permanent Employees Member":
        "{Number Of Employees Or Workers Related To Minimum Wages - More Than Minimum Wage Member - Gender Member - Other Than Permanent Employees Member} - {Number Of Employees Or Workers Related To Minimum Wages - More Than Minimum Wage Member - Male Member - Other Than Permanent Employees Member} - {Number Of Employees Or Workers Related To Minimum Wages - More Than Minimum Wage Member - Female Member - Other Than Permanent Employees Member}",
    "Percentage Of Employees Or Workers Related To Minimum Wages - More Than Minimum Wage Member - Other Gender Member - Other Than Permanent Employees Member": "0",
    "Number Of Employees Or Workers Related To Minimum Wages - Total Minimum Wages Member - Gender Member - Other Than Permanent Employees Member - Previous Year":
        "{Number Of Employees Or Workers Related To Minimum Wages - Equal To Minimum Wage Member - Gender Member - Other Than Permanent Employees Member - Previous Year} + {Number Of Employees Or Workers Related To Minimum Wages - More Than Minimum Wage Member - Gender Member - Other Than Permanent Employees Member - Previous Year}",
    "Number Of Employees Or Workers Related To Minimum Wages - Total Minimum Wages Member - Male Member - Other Than Permanent Employees Member - Previous Year":
        "{Number Of Employees Or Workers Related To Minimum Wages - Total Minimum Wages Member - Gender Member - Other Than Permanent Employees Member - Previous Year} - {Number Of Employees Or Workers Related To Minimum Wages - Total Minimum Wages Member - Female Member - Other Than Permanent Employees Member - Previous Year} - {Number Of Employees Or Workers Related To Minimum Wages - Total Minimum Wages Member - Other Gender Member - Other Than Permanent Employees Member - Previous Year}",
    "Number Of Employees Or Workers Related To Minimum Wages - Total Minimum Wages Member - Female Member - Other Than Permanent Employees Member - Previous Year":
        "{Number Of Employees Or Workers Related To Minimum Wages - Total Minimum Wages Member - Gender Member - Other Than Permanent Employees Member - Previous Year} - {Number Of Employees Or Workers Related To Minimum Wages - Total Minimum Wages Member - Male Member - Other Than Permanent Employees Member - Previous Year} - {Number Of Employees Or Workers Related To Minimum Wages - Total Minimum Wages Member - Other Gender Member - Other Than Permanent Employees Member - Previous Year}",
    "Number Of Employees Or Workers Related To Minimum Wages - Total Minimum Wages Member - Other Gender Member - Other Than Permanent Employees Member - Previous Year":
        "{Number Of Employees Or Workers Related To Minimum Wages - Total Minimum Wages Member - Gender Member - Other Than Permanent Employees Member - Previous Year} - {Number Of Employees Or Workers Related To Minimum Wages - Total Minimum Wages Member - Male Member - Other Than Permanent Employees Member - Previous Year} - {Number Of Employees Or Workers Related To Minimum Wages - Total Minimum Wages Member - Female Member - Other Than Permanent Employees Member - Previous Year}",
    "Number Of Employees Or Workers Related To Minimum Wages - Equal To Minimum Wage Member - Gender Member - Other Than Permanent Employees Member - Previous Year":
        "{Number Of Employees Or Workers Related To Minimum Wages - Total Minimum Wages Member - Gender Member - Other Than Permanent Employees Member - Previous Year} - {Number Of Employees Or Workers Related To Minimum Wages - More Than Minimum Wage Member - Gender Member - Other Than Permanent Employees Member - Previous Year}",
    "Percentage Of Employees Or Workers Related To Minimum Wages - Equal To Minimum Wage Member - Gender Member - Other Than Permanent Employees Member - Previous Year":
        "({Number Of Employees Or Workers Related To Minimum Wages - Equal To Minimum Wage Member - Gender Member - Other Than Permanent Employees Member - Previous Year} / {Number Of Employees Or Workers Related To Minimum Wages - Total Minimum Wages Member - Gender Member - Other Than Permanent Employees Member - Previous Year}) * 100",
    "Number Of Employees Or Workers Related To Minimum Wages - More Than Minimum Wage Member - Gender Member - Other Than Permanent Employees Member - Previous Year":
        "{Number Of Employees Or Workers Related To Minimum Wages - Total Minimum Wages Member - Gender Member - Other Than Permanent Employees Member - Previous Year} - {Number Of Employees Or Workers Related To Minimum Wages - Equal To Minimum Wage Member - Gender Member - Other Than Permanent Employees Member - Previous Year}",
    "Percentage Of Employees Or Workers Related To Minimum Wages - More Than Minimum Wage Member - Gender Member - Other Than Permanent Employees Member - Previous Year":
        "({Number Of Employees Or Workers Related To Minimum Wages - More Than Minimum Wage Member - Gender Member - Other Than Permanent Employees Member - Previous Year} / {Number Of Employees Or Workers Related To Minimum Wages - Total Minimum Wages Member - Gender Member - Other Than Permanent Employees Member - Previous Year}) * 100",
    "Number Of Employees Or Workers Related To Minimum Wages - Equal To Minimum Wage Member - Male Member - Other Than Permanent Employees Member - Previous Year":
        "{Number Of Employees Or Workers Related To Minimum Wages - Equal To Minimum Wage Member - Gender Member - Other Than Permanent Employees Member - Previous Year} - {Number Of Employees Or Workers Related To Minimum Wages - Equal To Minimum Wage Member - Female Member - Other Than Permanent Employees Member - Previous Year} - {Number Of Employees Or Workers Related To Minimum Wages - Equal To Minimum Wage Member - Other Gender Member - Other Than Permanent Employees Member - Previous Year}",
    "Percentage Of Employees Or Workers Related To Minimum Wages - Equal To Minimum Wage Member - Male Member - Other Than Permanent Employees Member - Previous Year": "0",
    "Number Of Employees Or Workers Related To Minimum Wages - More Than Minimum Wage Member - Male Member - Other Than Permanent Employees Member - Previous Year":
        "{Number Of Employees Or Workers Related To Minimum Wages - More Than Minimum Wage Member - Gender Member - Other Than Permanent Employees Member - Previous Year} - {Number Of Employees Or Workers Related To Minimum Wages - More Than Minimum Wage Member - Female Member - Other Than Permanent Employees Member - Previous Year} - {Number Of Employees Or Workers Related To Minimum Wages - More Than Minimum Wage Member - Other Gender Member - Other Than Permanent Employees Member - Previous Year}",
    "Percentage Of Employees Or Workers Related To Minimum Wages - More Than Minimum Wage Member - Male Member - Other Than Permanent Employees Member - Previous Year": "0",
    "Number Of Employees Or Workers Related To Minimum Wages - Equal To Minimum Wage Member - Female Member - Other Than Permanent Employees Member - Previous Year":
        "{Number Of Employees Or Workers Related To Minimum Wages - Equal To Minimum Wage Member - Gender Member - Other Than Permanent Employees Member - Previous Year} - {Number Of Employees Or Workers Related To Minimum Wages - Equal To Minimum Wage Member - Male Member - Other Than Permanent Employees Member - Previous Year} - {Number Of Employees Or Workers Related To Minimum Wages - Equal To Minimum Wage Member - Other Gender Member - Other Than Permanent Employees Member - Previous Year}",
    "Percentage Of Employees Or Workers Related To Minimum Wages - Equal To Minimum Wage Member - Female Member - Other Than Permanent Employees Member - Previous Year": "0",
    "Number Of Employees Or Workers Related To Minimum Wages - More Than Minimum Wage Member - Female Member - Other Than Permanent Employees Member - Previous Year":
        "{Number Of Employees Or Workers Related To Minimum Wages - More Than Minimum Wage Member - Gender Member - Other Than Permanent Employees Member - Previous Year} - {Number Of Employees Or Workers Related To Minimum Wages - More Than Minimum Wage Member - Male Member - Other Than Permanent Employees Member - Previous Year} - {Number Of Employees Or Workers Related To Minimum Wages - More Than Minimum Wage Member - Other Gender Member - Other Than Permanent Employees Member - Previous Year}",
    "Percentage Of Employees Or Workers Related To Minimum Wages - More Than Minimum Wage Member - Female Member - Other Than Permanent Employees Member - Previous Year": "0",
    "Number Of Employees Or Workers Related To Minimum Wages - Equal To Minimum Wage Member - Other Gender Member - Other Than Permanent Employees Member - Previous Year":
        "{Number Of Employees Or Workers Related To Minimum Wages - Equal To Minimum Wage Member - Gender Member - Other Than Permanent Employees Member - Previous Year} - {Number Of Employees Or Workers Related To Minimum Wages - Equal To Minimum Wage Member - Male Member - Other Than Permanent Employees Member - Previous Year} - {Number Of Employees Or Workers Related To Minimum Wages - Equal To Minimum Wage Member - Female Member - Other Than Permanent Employees Member - Previous Year}",
    "Percentage Of Employees Or Workers Related To Minimum Wages - Equal To Minimum Wage Member - Other Gender Member - Other Than Permanent Employees Member - Previous Year": "0",
    "Number Of Employees Or Workers Related To Minimum Wages - More Than Minimum Wage Member - Other Gender Member - Other Than Permanent Employees Member - Previous Year":
        "{Number Of Employees Or Workers Related To Minimum Wages - More Than Minimum Wage Member - Gender Member - Other Than Permanent Employees Member - Previous Year} - {Number Of Employees Or Workers Related To Minimum Wages - More Than Minimum Wage Member - Male Member - Other Than Permanent Employees Member - Previous Year} - {Number Of Employees Or Workers Related To Minimum Wages - More Than Minimum Wage Member - Female Member - Other Than Permanent Employees Member - Previous Year}",
    "Percentage Of Employees Or Workers Related To Minimum Wages - More Than Minimum Wage Member - Other Gender Member - Other Than Permanent Employees Member - Previous Year": "0",
    "Number Of Employees Or Workers Related To Minimum Wages - Total Minimum Wages Member - Gender Member - Permanent Workers Member":
        "{Number Of Employees Or Workers Related To Minimum Wages - Equal To Minimum Wage Member - Gender Member - Permanent Workers Member} + {Number Of Employees Or Workers Related To Minimum Wages - More Than Minimum Wage Member - Gender Member - Permanent Workers Member}",
    "Number Of Employees Or Workers Related To Minimum Wages - Total Minimum Wages Member - Male Member - Permanent Workers Member":
        "{Number Of Employees Or Workers Related To Minimum Wages - Total Minimum Wages Member - Gender Member - Permanent Workers Member} - {Number Of Employees Or Workers Related To Minimum Wages - Total Minimum Wages Member - Female Member - Permanent Workers Member} - {Number Of Employees Or Workers Related To Minimum Wages - Total Minimum Wages Member - Other Gender Member - Permanent Workers Member}",
    "Number Of Employees Or Workers Related To Minimum Wages - Total Minimum Wages Member - Female Member - Permanent Workers Member":
        "{Number Of Employees Or Workers Related To Minimum Wages - Total Minimum Wages Member - Gender Member - Permanent Workers Member} - {Number Of Employees Or Workers Related To Minimum Wages - Total Minimum Wages Member - Male Member - Permanent Workers Member} - {Number Of Employees Or Workers Related To Minimum Wages - Total Minimum Wages Member - Other Gender Member - Permanent Workers Member}",
    "Number Of Employees Or Workers Related To Minimum Wages - Total Minimum Wages Member - Other Gender Member - Permanent Workers Member":
        "{Number Of Employees Or Workers Related To Minimum Wages - Total Minimum Wages Member - Gender Member - Permanent Workers Member} - {Number Of Employees Or Workers Related To Minimum Wages - Total Minimum Wages Member - Male Member - Permanent Workers Member} - {Number Of Employees Or Workers Related To Minimum Wages - Total Minimum Wages Member - Female Member - Permanent Workers Member}",
    "Number Of Employees Or Workers Related To Minimum Wages - Equal To Minimum Wage Member - Gender Member - Permanent Workers Member":
        "{Number Of Employees Or Workers Related To Minimum Wages - Total Minimum Wages Member - Gender Member - Permanent Workers Member} - {Number Of Employees Or Workers Related To Minimum Wages - More Than Minimum Wage Member - Gender Member - Permanent Workers Member}",
    "Percentage Of Employees Or Workers Related To Minimum Wages - Equal To Minimum Wage Member - Gender Member - Permanent Workers Member":
        "({Number Of Employees Or Workers Related To Minimum Wages - Equal To Minimum Wage Member - Gender Member - Permanent Workers Member} / {Number Of Employees Or Workers Related To Minimum Wages - Total Minimum Wages Member - Gender Member - Permanent Workers Member}) * 100",
    "Number Of Employees Or Workers Related To Minimum Wages - Equal To Minimum Wage Member - Male Member - Permanent Workers Member":
        "{Number Of Employees Or Workers Related To Minimum Wages - Equal To Minimum Wage Member - Gender Member - Permanent Workers Member} - {Number Of Employees Or Workers Related To Minimum Wages - Equal To Minimum Wage Member - Female Member - Permanent Workers Member} - {Number Of Employees Or Workers Related To Minimum Wages - Equal To Minimum Wage Member - Other Gender Member - Permanent Workers Member}",
    "Percentage Of Employees Or Workers Related To Minimum Wages - Equal To Minimum Wage Member - Male Member - Permanent Workers Member": "0",
    "Number Of Employees Or Workers Related To Minimum Wages - Equal To Minimum Wage Member - Female Member - Permanent Workers Member":
        "{Number Of Employees Or Workers Related To Minimum Wages - Equal To Minimum Wage Member - Gender Member - Permanent Workers Member} - {Number Of Employees Or Workers Related To Minimum Wages - Equal To Minimum Wage Member - Male Member - Permanent Workers Member} - {Number Of Employees Or Workers Related To Minimum Wages - Equal To Minimum Wage Member - Other Gender Member - Permanent Workers Member}",
    "Percentage Of Employees Or Workers Related To Minimum Wages - Equal To Minimum Wage Member - Female Member - Permanent Workers Member": "0",
    "Number Of Employees Or Workers Related To Minimum Wages - Equal To Minimum Wage Member - Other Gender Member - Permanent Workers Member":
        "{Number Of Employees Or Workers Related To Minimum Wages - Equal To Minimum Wage Member - Gender Member - Permanent Workers Member} - {Number Of Employees Or Workers Related To Minimum Wages - Equal To Minimum Wage Member - Male Member - Permanent Workers Member} - {Number Of Employees Or Workers Related To Minimum Wages - Equal To Minimum Wage Member - Female Member - Permanent Workers Member}",
    "Percentage Of Employees Or Workers Related To Minimum Wages - Equal To Minimum Wage Member - Other Gender Member - Permanent Workers Member": "0",
    "Number Of Employees Or Workers Related To Minimum Wages - More Than Minimum Wage Member - Gender Member - Permanent Workers Member":
        "{Number Of Employees Or Workers Related To Minimum Wages - Total Minimum Wages Member - Gender Member - Permanent Workers Member} - {Number Of Employees Or Workers Related To Minimum Wages - Equal To Minimum Wage Member - Gender Member - Permanent Workers Member}",
    "Percentage Of Employees Or Workers Related To Minimum Wages - More Than Minimum Wage Member - Gender Member - Permanent Workers Member":
        "({Number Of Employees Or Workers Related To Minimum Wages - More Than Minimum Wage Member - Gender Member - Permanent Workers Member} / {Number Of Employees Or Workers Related To Minimum Wages - Total Minimum Wages Member - Gender Member - Permanent Workers Member}) * 100",
    "Number Of Employees Or Workers Related To Minimum Wages - More Than Minimum Wage Member - Male Member - Permanent Workers Member":
        "{Number Of Employees Or Workers Related To Minimum Wages - More Than Minimum Wage Member - Gender Member - Permanent Workers Member} - {Number Of Employees Or Workers Related To Minimum Wages - More Than Minimum Wage Member - Female Member - Permanent Workers Member} - {Number Of Employees Or Workers Related To Minimum Wages - More Than Minimum Wage Member - Other Gender Member - Permanent Workers Member}",
    "Percentage Of Employees Or Workers Related To Minimum Wages - More Than Minimum Wage Member - Male Member - Permanent Workers Member": "0",
    "Number Of Employees Or Workers Related To Minimum Wages - More Than Minimum Wage Member - Female Member - Permanent Workers Member":
        "{Number Of Employees Or Workers Related To Minimum Wages - More Than Minimum Wage Member - Gender Member - Permanent Workers Member} - {Number Of Employees Or Workers Related To Minimum Wages - More Than Minimum Wage Member - Male Member - Permanent Workers Member} - {Number Of Employees Or Workers Related To Minimum Wages - More Than Minimum Wage Member - Other Gender Member - Permanent Workers Member}",
    "Percentage Of Employees Or Workers Related To Minimum Wages - More Than Minimum Wage Member - Female Member - Permanent Workers Member": "0",
    "Number Of Employees Or Workers Related To Minimum Wages - More Than Minimum Wage Member - Other Gender Member - Permanent Workers Member":
        "{Number Of Employees Or Workers Related To Minimum Wages - More Than Minimum Wage Member - Gender Member - Permanent Workers Member} - {Number Of Employees Or Workers Related To Minimum Wages - More Than Minimum Wage Member - Male Member - Permanent Workers Member} - {Number Of Employees Or Workers Related To Minimum Wages - More Than Minimum Wage Member - Female Member - Permanent Workers Member}",
    "Percentage Of Employees Or Workers Related To Minimum Wages - More Than Minimum Wage Member - Other Gender Member - Permanent Workers Member": "0",
    "Number Of Employees Or Workers Related To Minimum Wages - Total Minimum Wages Member - Gender Member - Permanent Workers Member - Previous Year":
        "{Number Of Employees Or Workers Related To Minimum Wages - Equal To Minimum Wage Member - Gender Member - Permanent Workers Member - Previous Year} + {Number Of Employees Or Workers Related To Minimum Wages - More Than Minimum Wage Member - Gender Member - Permanent Workers Member - Previous Year}",
    "Number Of Employees Or Workers Related To Minimum Wages - Total Minimum Wages Member - Male Member - Permanent Workers Member - Previous Year":
        "{Number Of Employees Or Workers Related To Minimum Wages - Total Minimum Wages Member - Gender Member - Permanent Workers Member - Previous Year} - {Number Of Employees Or Workers Related To Minimum Wages - Total Minimum Wages Member - Female Member - Permanent Workers Member - Previous Year} - {Number Of Employees Or Workers Related To Minimum Wages - Total Minimum Wages Member - Other Gender Member - Permanent Workers Member - Previous Year}",
    "Number Of Employees Or Workers Related To Minimum Wages - Total Minimum Wages Member - Female Member - Permanent Workers Member - Previous Year":
        "{Number Of Employees Or Workers Related To Minimum Wages - Total Minimum Wages Member - Gender Member - Permanent Workers Member - Previous Year} - {Number Of Employees Or Workers Related To Minimum Wages - Total Minimum Wages Member - Male Member - Permanent Workers Member - Previous Year} - {Number Of Employees Or Workers Related To Minimum Wages - Total Minimum Wages Member - Other Gender Member - Permanent Workers Member - Previous Year}",
    "Number Of Employees Or Workers Related To Minimum Wages - Total Minimum Wages Member - Other Gender Member - Permanent Workers Member - Previous Year":
        "{Number Of Employees Or Workers Related To Minimum Wages - Total Minimum Wages Member - Gender Member - Permanent Workers Member - Previous Year} - {Number Of Employees Or Workers Related To Minimum Wages - Total Minimum Wages Member - Male Member - Permanent Workers Member - Previous Year} - {Number Of Employees Or Workers Related To Minimum Wages - Total Minimum Wages Member - Female Member - Permanent Workers Member - Previous Year}",
    "Number Of Employees Or Workers Related To Minimum Wages - Equal To Minimum Wage Member - Gender Member - Permanent Workers Member - Previous Year":
        "{Number Of Employees Or Workers Related To Minimum Wages - Total Minimum Wages Member - Gender Member - Permanent Workers Member - Previous Year} - {Number Of Employees Or Workers Related To Minimum Wages - More Than Minimum Wage Member - Gender Member - Permanent Workers Member - Previous Year}",
    "Percentage Of Employees Or Workers Related To Minimum Wages - Equal To Minimum Wage Member - Gender Member - Permanent Workers Member - Previous Year":
        "({Number Of Employees Or Workers Related To Minimum Wages - Equal To Minimum Wage Member - Gender Member - Permanent Workers Member - Previous Year} / {Number Of Employees Or Workers Related To Minimum Wages - Total Minimum Wages Member - Gender Member - Permanent Workers Member - Previous Year}) * 100",
    "Number Of Employees Or Workers Related To Minimum Wages - More Than Minimum Wage Member - Gender Member - Permanent Workers Member - Previous Year":
        "{Number Of Employees Or Workers Related To Minimum Wages - Total Minimum Wages Member - Gender Member - Permanent Workers Member - Previous Year} - {Number Of Employees Or Workers Related To Minimum Wages - Equal To Minimum Wage Member - Gender Member - Permanent Workers Member - Previous Year}",
    "Percentage Of Employees Or Workers Related To Minimum Wages - More Than Minimum Wage Member - Gender Member - Permanent Workers Member - Previous Year":
        "({Number Of Employees Or Workers Related To Minimum Wages - More Than Minimum Wage Member - Gender Member - Permanent Workers Member - Previous Year} / {Number Of Employees Or Workers Related To Minimum Wages - Total Minimum Wages Member - Gender Member - Permanent Workers Member - Previous Year}) * 100",
    "Number Of Employees Or Workers Related To Minimum Wages - Equal To Minimum Wage Member - Male Member - Permanent Workers Member - Previous Year":
        "{Number Of Employees Or Workers Related To Minimum Wages - Equal To Minimum Wage Member - Gender Member - Permanent Workers Member - Previous Year} - {Number Of Employees Or Workers Related To Minimum Wages - Equal To Minimum Wage Member - Female Member - Permanent Workers Member - Previous Year} - {Number Of Employees Or Workers Related To Minimum Wages - Equal To Minimum Wage Member - Other Gender Member - Permanent Workers Member - Previous Year}",
    "Percentage Of Employees Or Workers Related To Minimum Wages - Equal To Minimum Wage Member - Male Member - Permanent Workers Member - Previous Year": "0",
    "Number Of Employees Or Workers Related To Minimum Wages - More Than Minimum Wage Member - Male Member - Permanent Workers Member - Previous Year":
        "{Number Of Employees Or Workers Related To Minimum Wages - More Than Minimum Wage Member - Gender Member - Permanent Workers Member - Previous Year} - {Number Of Employees Or Workers Related To Minimum Wages - More Than Minimum Wage Member - Female Member - Permanent Workers Member - Previous Year} - {Number Of Employees Or Workers Related To Minimum Wages - More Than Minimum Wage Member - Other Gender Member - Permanent Workers Member - Previous Year}",
    "Percentage Of Employees Or Workers Related To Minimum Wages - More Than Minimum Wage Member - Male Member - Permanent Workers Member - Previous Year": "0",
    "Number Of Employees Or Workers Related To Minimum Wages - Equal To Minimum Wage Member - Female Member - Permanent Workers Member - Previous Year":
        "{Number Of Employees Or Workers Related To Minimum Wages - Equal To Minimum Wage Member - Gender Member - Permanent Workers Member - Previous Year} - {Number Of Employees Or Workers Related To Minimum Wages - Equal To Minimum Wage Member - Male Member - Permanent Workers Member - Previous Year} - {Number Of Employees Or Workers Related To Minimum Wages - Equal To Minimum Wage Member - Other Gender Member - Permanent Workers Member - Previous Year}",
    "Percentage Of Employees Or Workers Related To Minimum Wages - Equal To Minimum Wage Member - Female Member - Permanent Workers Member - Previous Year":
        "{Percentage Of Employees Or Workers Related To Minimum Wages - Equal To Minimum Wage Member - Gender Member - Permanent Workers Member - Previous Year} - {Percentage Of Employees Or Workers Related To Minimum Wages - Equal To Minimum Wage Member - Male Member - Permanent Workers Member - Previous Year} - {Percentage Of Employees Or Workers Related To Minimum Wages - Equal To Minimum Wage Member - Other Gender Member - Permanent Workers Member - Previous Year}",
    "Number Of Employees Or Workers Related To Minimum Wages - More Than Minimum Wage Member - Female Member - Permanent Workers Member - Previous Year":
        "{Number Of Employees Or Workers Related To Minimum Wages - More Than Minimum Wage Member - Gender Member - Permanent Workers Member - Previous Year} - {Number Of Employees Or Workers Related To Minimum Wages - More Than Minimum Wage Member - Male Member - Permanent Workers Member - Previous Year} - {Number Of Employees Or Workers Related To Minimum Wages - More Than Minimum Wage Member - Other Gender Member - Permanent Workers Member - Previous Year}",
    "Percentage Of Employees Or Workers Related To Minimum Wages - More Than Minimum Wage Member - Female Member - Permanent Workers Member - Previous Year":
        "{Percentage Of Employees Or Workers Related To Minimum Wages - More Than Minimum Wage Member - Gender Member - Permanent Workers Member - Previous Year} - {Percentage Of Employees Or Workers Related To Minimum Wages - More Than Minimum Wage Member - Male Member - Permanent Workers Member - Previous Year} - {Percentage Of Employees Or Workers Related To Minimum Wages - More Than Minimum Wage Member - Other Gender Member - Permanent Workers Member - Previous Year}",
    "Number Of Employees Or Workers Related To Minimum Wages - Equal To Minimum Wage Member - Other Gender Member - Permanent Workers Member - Previous Year":
        "{Number Of Employees Or Workers Related To Minimum Wages - Equal To Minimum Wage Member - Gender Member - Permanent Workers Member - Previous Year} - {Number Of Employees Or Workers Related To Minimum Wages - Equal To Minimum Wage Member - Male Member - Permanent Workers Member - Previous Year} - {Number Of Employees Or Workers Related To Minimum Wages - Equal To Minimum Wage Member - Female Member - Permanent Workers Member - Previous Year}",
    "Percentage Of Employees Or Workers Related To Minimum Wages - Equal To Minimum Wage Member - Other Gender Member - Permanent Workers Member - Previous Year": "0",
    "Number Of Employees Or Workers Related To Minimum Wages - More Than Minimum Wage Member - Other Gender Member - Permanent Workers Member - Previous Year":
        "{Number Of Employees Or Workers Related To Minimum Wages - More Than Minimum Wage Member - Gender Member - Permanent Workers Member - Previous Year} - {Number Of Employees Or Workers Related To Minimum Wages - More Than Minimum Wage Member - Male Member - Permanent Workers Member - Previous Year} - {Number Of Employees Or Workers Related To Minimum Wages - More Than Minimum Wage Member - Female Member - Permanent Workers Member - Previous Year}",
    "Percentage Of Employees Or Workers Related To Minimum Wages - More Than Minimum Wage Member - Other Gender Member - Permanent Workers Member - Previous Year": "0",
    "Number Of Employees Or Workers Related To Minimum Wages - Total Minimum Wages Member - Gender Member - Other Than Permanent Workers Member":
        "{Number Of Employees Or Workers Related To Minimum Wages - Equal To Minimum Wage Member - Gender Member - Other Than Permanent Workers Member} + {Number Of Employees Or Workers Related To Minimum Wages - More Than Minimum Wage Member - Gender Member - Other Than Permanent Workers Member}",
    "Number Of Employees Or Workers Related To Minimum Wages - Total Minimum Wages Member - Male Member - Other Than Permanent Workers Member":
        "{Number Of Employees Or Workers Related To Minimum Wages - Total Minimum Wages Member - Gender Member - Other Than Permanent Workers Member} - {Number Of Employees Or Workers Related To Minimum Wages - Total Minimum Wages Member - Female Member - Other Than Permanent Workers Member} - {Number Of Employees Or Workers Related To Minimum Wages - Total Minimum Wages Member - Other Gender Member - Other Than Permanent Workers Member}",
    "Number Of Employees Or Workers Related To Minimum Wages - Total Minimum Wages Member - Female Member - Other Than Permanent Workers Member":
        "{Number Of Employees Or Workers Related To Minimum Wages - Total Minimum Wages Member - Gender Member - Other Than Permanent Workers Member} - {Number Of Employees Or Workers Related To Minimum Wages - Total Minimum Wages Member - Male Member - Other Than Permanent Workers Member} - {Number Of Employees Or Workers Related To Minimum Wages - Total Minimum Wages Member - Other Gender Member - Other Than Permanent Workers Member}",
    "Number Of Employees Or Workers Related To Minimum Wages - Total Minimum Wages Member - Other Gender Member - Other Than Permanent Workers Member":
        "{Number Of Employees Or Workers Related To Minimum Wages - Total Minimum Wages Member - Gender Member - Other Than Permanent Workers Member} - {Number Of Employees Or Workers Related To Minimum Wages - Total Minimum Wages Member - Male Member - Other Than Permanent Workers Member} - {Number Of Employees Or Workers Related To Minimum Wages - Total Minimum Wages Member - Female Member - Other Than Permanent Workers Member}",
    "Number Of Employees Or Workers Related To Minimum Wages - Equal To Minimum Wage Member - Gender Member - Other Than Permanent Workers Member":
        "{Number Of Employees Or Workers Related To Minimum Wages - Total Minimum Wages Member - Gender Member - Other Than Permanent Workers Member} - {Number Of Employees Or Workers Related To Minimum Wages - More Than Minimum Wage Member - Gender Member - Other Than Permanent Workers Member}",
    "Percentage Of Employees Or Workers Related To Minimum Wages - Equal To Minimum Wage Member - Gender Member - Other Than Permanent Workers Member":
        "({Number Of Employees Or Workers Related To Minimum Wages - Equal To Minimum Wage Member - Gender Member - Other Than Permanent Workers Member} / {Number Of Employees Or Workers Related To Minimum Wages - Total Minimum Wages Member - Gender Member - Other Than Permanent Workers Member}) * 100",
    "Number Of Employees Or Workers Related To Minimum Wages - Equal To Minimum Wage Member - Male Member - Other Than Permanent Workers Member":
        "{Number Of Employees Or Workers Related To Minimum Wages - Equal To Minimum Wage Member - Gender Member - Other Than Permanent Workers Member} - {Number Of Employees Or Workers Related To Minimum Wages - Equal To Minimum Wage Member - Female Member - Other Than Permanent Workers Member} - {Number Of Employees Or Workers Related To Minimum Wages - Equal To Minimum Wage Member - Other Gender Member - Other Than Permanent Workers Member}",
    "Percentage Of Employees Or Workers Related To Minimum Wages - Equal To Minimum Wage Member - Male Member - Other Than Permanent Workers Member": "0",
    "Number Of Employees Or Workers Related To Minimum Wages - Equal To Minimum Wage Member - Female Member - Other Than Permanent Workers Member":
        "{Number Of Employees Or Workers Related To Minimum Wages - Equal To Minimum Wage Member - Gender Member - Other Than Permanent Workers Member} - {Number Of Employees Or Workers Related To Minimum Wages - Equal To Minimum Wage Member - Male Member - Other Than Permanent Workers Member} - {Number Of Employees Or Workers Related To Minimum Wages - Equal To Minimum Wage Member - Other Gender Member - Other Than Permanent Workers Member}",
    "Percentage Of Employees Or Workers Related To Minimum Wages - Equal To Minimum Wage Member - Female Member - Other Than Permanent Workers Member": "0",
    "Number Of Employees Or Workers Related To Minimum Wages - Equal To Minimum Wage Member - Other Gender Member - Other Than Permanent Workers Member":
        "{Number Of Employees Or Workers Related To Minimum Wages - Equal To Minimum Wage Member - Gender Member - Other Than Permanent Workers Member} - {Number Of Employees Or Workers Related To Minimum Wages - Equal To Minimum Wage Member - Male Member - Other Than Permanent Workers Member} - {Number Of Employees Or Workers Related To Minimum Wages - Equal To Minimum Wage Member - Female Member - Other Than Permanent Workers Member}",
    "Percentage Of Employees Or Workers Related To Minimum Wages - Equal To Minimum Wage Member - Other Gender Member - Other Than Permanent Workers Member": "0",
    "Number Of Employees Or Workers Related To Minimum Wages - More Than Minimum Wage Member - Gender Member - Other Than Permanent Workers Member":
        "{Number Of Employees Or Workers Related To Minimum Wages - Total Minimum Wages Member - Gender Member - Other Than Permanent Workers Member} - {Number Of Employees Or Workers Related To Minimum Wages - Equal To Minimum Wage Member - Gender Member - Other Than Permanent Workers Member}",
    "Percentage Of Employees Or Workers Related To Minimum Wages - More Than Minimum Wage Member - Gender Member - Other Than Permanent Workers Member":
        "({Number Of Employees Or Workers Related To Minimum Wages - More Than Minimum Wage Member - Gender Member - Other Than Permanent Workers Member} / {Number Of Employees Or Workers Related To Minimum Wages - Total Minimum Wages Member - Gender Member - Other Than Permanent Workers Member}) * 100",
    "Number Of Employees Or Workers Related To Minimum Wages - More Than Minimum Wage Member - Male Member - Other Than Permanent Workers Member":
        "{Number Of Employees Or Workers Related To Minimum Wages - More Than Minimum Wage Member - Gender Member - Other Than Permanent Workers Member} - {Number Of Employees Or Workers Related To Minimum Wages - More Than Minimum Wage Member - Female Member - Other Than Permanent Workers Member} - {Number Of Employees Or Workers Related To Minimum Wages - More Than Minimum Wage Member - Other Gender Member - Other Than Permanent Workers Member}",
    "Percentage Of Employees Or Workers Related To Minimum Wages - More Than Minimum Wage Member - Male Member - Other Than Permanent Workers Member": "0",
    "Number Of Employees Or Workers Related To Minimum Wages - More Than Minimum Wage Member - Female Member - Other Than Permanent Workers Member":
        "{Number Of Employees Or Workers Related To Minimum Wages - More Than Minimum Wage Member - Gender Member - Other Than Permanent Workers Member} - {Number Of Employees Or Workers Related To Minimum Wages - More Than Minimum Wage Member - Male Member - Other Than Permanent Workers Member} - {Number Of Employees Or Workers Related To Minimum Wages - More Than Minimum Wage Member - Other Gender Member - Other Than Permanent Workers Member}",
    "Percentage Of Employees Or Workers Related To Minimum Wages - More Than Minimum Wage Member - Female Member - Other Than Permanent Workers Member": "0",
    "Number Of Employees Or Workers Related To Minimum Wages - More Than Minimum Wage Member - Other Gender Member - Other Than Permanent Workers Member":
        "{Number Of Employees Or Workers Related To Minimum Wages - More Than Minimum Wage Member - Gender Member - Other Than Permanent Workers Member} - {Number Of Employees Or Workers Related To Minimum Wages - More Than Minimum Wage Member - Male Member - Other Than Permanent Workers Member} - {Number Of Employees Or Workers Related To Minimum Wages - More Than Minimum Wage Member - Female Member - Other Than Permanent Workers Member}",
    "Percentage Of Employees Or Workers Related To Minimum Wages - More Than Minimum Wage Member - Other Gender Member - Other Than Permanent Workers Member": "0",
    "Number Of Employees Or Workers Related To Minimum Wages - Total Minimum Wages Member - Gender Member - Other Than Permanent Workers Member - Previous Year":
        "{Number Of Employees Or Workers Related To Minimum Wages - Equal To Minimum Wage Member - Gender Member - Other Than Permanent Workers Member - Previous Year} + {Number Of Employees Or Workers Related To Minimum Wages - More Than Minimum Wage Member - Gender Member - Other Than Permanent Workers Member - Previous Year}",
    "Number Of Employees Or Workers Related To Minimum Wages - Total Minimum Wages Member - Male Member - Other Than Permanent Workers Member - Previous Year":
        "{Number Of Employees Or Workers Related To Minimum Wages - Total Minimum Wages Member - Gender Member - Other Than Permanent Workers Member - Previous Year} - {Number Of Employees Or Workers Related To Minimum Wages - Total Minimum Wages Member - Female Member - Other Than Permanent Workers Member - Previous Year} - {Number Of Employees Or Workers Related To Minimum Wages - Total Minimum Wages Member - Other Gender Member - Other Than Permanent Workers Member - Previous Year}",
    "Number Of Employees Or Workers Related To Minimum Wages - Total Minimum Wages Member - Female Member - Other Than Permanent Workers Member - Previous Year":
        "{Number Of Employees Or Workers Related To Minimum Wages - Total Minimum Wages Member - Gender Member - Other Than Permanent Workers Member - Previous Year} - {Number Of Employees Or Workers Related To Minimum Wages - Total Minimum Wages Member - Male Member - Other Than Permanent Workers Member - Previous Year} - {Number Of Employees Or Workers Related To Minimum Wages - Total Minimum Wages Member - Other Gender Member - Other Than Permanent Workers Member - Previous Year}",
    "Number Of Employees Or Workers Related To Minimum Wages - Total Minimum Wages Member - Other Gender Member - Other Than Permanent Workers Member - Previous Year":
        "{Number Of Employees Or Workers Related To Minimum Wages - Total Minimum Wages Member - Gender Member - Other Than Permanent Workers Member - Previous Year} - {Number Of Employees Or Workers Related To Minimum Wages - Total Minimum Wages Member - Male Member - Other Than Permanent Workers Member - Previous Year} - {Number Of Employees Or Workers Related To Minimum Wages - Total Minimum Wages Member - Female Member - Other Than Permanent Workers Member - Previous Year}",
    "Number Of Employees Or Workers Related To Minimum Wages - Equal To Minimum Wage Member - Gender Member - Other Than Permanent Workers Member - Previous Year":
        "{Number Of Employees Or Workers Related To Minimum Wages - Total Minimum Wages Member - Gender Member - Other Than Permanent Workers Member - Previous Year} - {Number Of Employees Or Workers Related To Minimum Wages - More Than Minimum Wage Member - Gender Member - Other Than Permanent Workers Member - Previous Year}",
    "Percentage Of Employees Or Workers Related To Minimum Wages - Equal To Minimum Wage Member - Gender Member - Other Than Permanent Workers Member - Previous Year":
        "({Number Of Employees Or Workers Related To Minimum Wages - Equal To Minimum Wage Member - Gender Member - Other Than Permanent Workers Member - Previous Year} / {Number Of Employees Or Workers Related To Minimum Wages - Total Minimum Wages Member - Gender Member - Other Than Permanent Workers Member - Previous Year}) * 100",
    "Number Of Employees Or Workers Related To Minimum Wages - More Than Minimum Wage Member - Gender Member - Other Than Permanent Workers Member - Previous Year":
        "{Number Of Employees Or Workers Related To Minimum Wages - Total Minimum Wages Member - Gender Member - Other Than Permanent Workers Member - Previous Year} - {Number Of Employees Or Workers Related To Minimum Wages - Equal To Minimum Wage Member - Gender Member - Other Than Permanent Workers Member - Previous Year}",
    "Percentage Of Employees Or Workers Related To Minimum Wages - More Than Minimum Wage Member - Gender Member - Other Than Permanent Workers Member - Previous Year":
        "({Number Of Employees Or Workers Related To Minimum Wages - More Than Minimum Wage Member - Gender Member - Other Than Permanent Workers Member - Previous Year} / {Number Of Employees Or Workers Related To Minimum Wages - Total Minimum Wages Member - Gender Member - Other Than Permanent Workers Member - Previous Year}) * 100",
    "Number Of Employees Or Workers Related To Minimum Wages - Equal To Minimum Wage Member - Male Member - Other Than Permanent Workers Member - Previous Year":
        "{Number Of Employees Or Workers Related To Minimum Wages - Equal To Minimum Wage Member - Gender Member - Other Than Permanent Workers Member - Previous Year} - {Number Of Employees Or Workers Related To Minimum Wages - Equal To Minimum Wage Member - Female Member - Other Than Permanent Workers Member - Previous Year} - {Number Of Employees Or Workers Related To Minimum Wages - Equal To Minimum Wage Member - Other Gender Member - Other Than Permanent Workers Member - Previous Year}",
    "Percentage Of Employees Or Workers Related To Minimum Wages - Equal To Minimum Wage Member - Male Member - Other Than Permanent Workers Member - Previous Year": "0",
    "Number Of Employees Or Workers Related To Minimum Wages - More Than Minimum Wage Member - Male Member - Other Than Permanent Workers Member - Previous Year":
        "{Number Of Employees Or Workers Related To Minimum Wages - More Than Minimum Wage Member - Gender Member - Other Than Permanent Workers Member - Previous Year} - {Number Of Employees Or Workers Related To Minimum Wages - More Than Minimum Wage Member - Female Member - Other Than Permanent Workers Member - Previous Year} - {Number Of Employees Or Workers Related To Minimum Wages - More Than Minimum Wage Member - Other Gender Member - Other Than Permanent Workers Member - Previous Year}",
    "Percentage Of Employees Or Workers Related To Minimum Wages - More Than Minimum Wage Member - Male Member - Other Than Permanent Workers Member - Previous Year": "0",
    "Number Of Employees Or Workers Related To Minimum Wages - Equal To Minimum Wage Member - Female Member - Other Than Permanent Workers Member - Previous Year":
        "{Number Of Employees Or Workers Related To Minimum Wages - Equal To Minimum Wage Member - Gender Member - Other Than Permanent Workers Member - Previous Year} - {Number Of Employees Or Workers Related To Minimum Wages - Equal To Minimum Wage Member - Male Member - Other Than Permanent Workers Member - Previous Year} - {Number Of Employees Or Workers Related To Minimum Wages - Equal To Minimum Wage Member - Other Gender Member - Other Than Permanent Workers Member - Previous Year}",
    "Percentage Of Employees Or Workers Related To Minimum Wages - Equal To Minimum Wage Member - Female Member - Other Than Permanent Workers Member - Previous Year": "0",
    "Number Of Employees Or Workers Related To Minimum Wages - More Than Minimum Wage Member - Female Member - Other Than Permanent Workers Member - Previous Year":
        "{Number Of Employees Or Workers Related To Minimum Wages - More Than Minimum Wage Member - Gender Member - Other Than Permanent Workers Member - Previous Year} - {Number Of Employees Or Workers Related To Minimum Wages - More Than Minimum Wage Member - Male Member - Other Than Permanent Workers Member - Previous Year} - {Number Of Employees Or Workers Related To Minimum Wages - More Than Minimum Wage Member - Other Gender Member - Other Than Permanent Workers Member - Previous Year}",
    "Percentage Of Employees Or Workers Related To Minimum Wages - More Than Minimum Wage Member - Female Member - Other Than Permanent Workers Member - Previous Year": "0",
    "Number Of Employees Or Workers Related To Minimum Wages - Equal To Minimum Wage Member - Other Gender Member - Other Than Permanent Workers Member - Previous Year":
        "{Number Of Employees Or Workers Related To Minimum Wages - Equal To Minimum Wage Member - Gender Member - Other Than Permanent Workers Member - Previous Year} - {Number Of Employees Or Workers Related To Minimum Wages - Equal To Minimum Wage Member - Male Member - Other Than Permanent Workers Member - Previous Year} - {Number Of Employees Or Workers Related To Minimum Wages - Equal To Minimum Wage Member - Female Member - Other Than Permanent Workers Member - Previous Year}",
    "Percentage Of Employees Or Workers Related To Minimum Wages - Equal To Minimum Wage Member - Other Gender Member - Other Than Permanent Workers Member - Previous Year": "0",
    "Number Of Employees Or Workers Related To Minimum Wages - More Than Minimum Wage Member - Other Gender Member - Other Than Permanent Workers Member - Previous Year":
        "{Number Of Employees Or Workers Related To Minimum Wages - More Than Minimum Wage Member - Gender Member - Other Than Permanent Workers Member - Previous Year} - {Number Of Employees Or Workers Related To Minimum Wages - More Than Minimum Wage Member - Male Member - Other Than Permanent Workers Member - Previous Year} - {Number Of Employees Or Workers Related To Minimum Wages - More Than Minimum Wage Member - Female Member - Other Than Permanent Workers Member - Previous Year}",
    "Percentage Of Employees Or Workers Related To Minimum Wages - More Than Minimum Wage Member - Other Gender Member - Other Than Permanent Workers Member - Previous Year": "0",
    "Number Of Board Of Directors For Remuneration Or Salary Or Wages - Male Member": "0",
    "Median Of Remuneration Or Salary Or Wages Of Board Of Directors - Male Member": "0",
    "Number Of Board Of Directors For Remuneration Or Salary Or Wages - Female Member": "0",
    "Median Of Remuneration Or Salary Or Wages Of Board Of Directors - Female Member": "0",
    "Number Of Board Of Directors For Remuneration Or Salary Or Wages - Other Gender Member": "0",
    "Median Of Remuneration Or Salary Or Wages Of Board Of Directors - Other Gender Member": "0",
    "Number Of Key Managerial Personnel For Remuneration Or Salary Or Wages - Male Member": "0",
    "Median Of Remuneration Or Salary Or Wages Of Key Managerial Personnel - Male Member": "0",
    "Number Of Key Managerial Personnel For Remuneration Or Salary Or Wages - Female Member": "0",
    "Median Of Remuneration Or Salary Or Wages Of Key Managerial Personnel - Female Member": "0",
    "Number Of Key Managerial Personnel For Remuneration Or Salary Or Wages - Other Gender Member": "0",
    "Median Of Remuneration Or Salary Or Wages Of Key Managerial Personnel - Other Gender Member": "0",
    "Number Of Employees Other Than Bod And KMPFor Remuneration Or Salary Or Wages - Male Member": "0",
    "Median Of Remuneration Or Salary Or Wages Of Employees Other Than Bod And KMP - Male Member": "0",
    "Number Of Employees Other Than Bod And KMPFor Remuneration Or Salary Or Wages - Female Member": "0",
    "Median Of Remuneration Or Salary Or Wages Of Employees Other Than Bod And KMP - Female Member": "0",
    "Number Of Employees Other Than Bod And KMPFor Remuneration Or Salary Or Wages - Other Gender Member": "0",
    "Median Of Remuneration Or Salary Or Wages Of Employees Other Than Bod And KMP - Other Gender Member": "0",
    "Number Of Workers For Remuneration Or Salary Or Wages - Male Member": "0",
    "Median Of Remuneration Or Salary Or Wages Of Workers - Male Member": "0",
    "Number Of Workers For Remuneration Or Salary Or Wages - Female Member": "0",
    "Median Of Remuneration Or Salary Or Wages Of Workers - Female Member": "0",
    "Number Of Workers For Remuneration Or Salary Or Wages - Other Gender Member": "0",
    "Median Of Remuneration Or Salary Or Wages Of Workers - Other Gender Member": "0",
    "Gross Wages Paid To Female": "0",
    "Gross Wages Paid To Female - Previous Year": "0",
    "Total Wages Paid": "0",
    "Total Wages Paid - Previous Year": "0",
    "Percentage Of Gross Wages Paid To Female To Total Wages Paid": "0",
    "Percentage Of Gross Wages Paid To Female To Total Wages Paid - Previous Year": "0",
    "Do You Have AFocal Point Responsible For Addressing Human Rights Impacts Or Issues Caused Or Contributed To By The Business": "0",
    "Number Of Complaints Filed During The Year - Sexual Harassment Member": "0",
    "Number Of Complaints Pending Resolution At The End Of Year - Sexual Harassment Member": "0",
    "Number Of Complaints Filed During The Year - Discrimination At Work Place Member": "0",
    "Number Of Complaints Pending Resolution At The End Of Year - Discrimination At Work Place Member": "0",
    "Number Of Complaints Filed During The Year - Child Labour Member": "0",
    "Number Of Complaints Pending Resolution At The End Of Year - Child Labour Member": "0",
    "Number Of Complaints Filed During The Year - Forced Labour Or Involuntary Labour Member": "0",
    "Number Of Complaints Pending Resolution At The End Of Year - Forced Labour Or Involuntary Labour Member": "0",
    "Number Of Complaints Filed During The Year - Wages Member": "0",
    "Number Of Complaints Pending Resolution At The End Of Year - Wages Member": "0",
    "Number Of Complaints Filed During The Year - Otherhumanrightsrelatedissues Member": "0",
    "Number Of Complaints Pending Resolution At The End Of Year - Otherhumanrightsrelatedissues Member": "0",
    "Number Of Complaints Filed During The Year - Sexual Harassment Member - Previous Year": "0",
    "Number Of Complaints Pending Resolution At The End Of Year - Sexual Harassment Member - Previous Year": "0",
    "Number Of Complaints Filed During The Year - Discrimination At Work Place Member - Previous Year": "0",
    "Number Of Complaints Pending Resolution At The End Of Year - Discrimination At Work Place Member - Previous Year": "0",
    "Number Of Complaints Filed During The Year - Child Labour Member - Previous Year": "0",
    "Number Of Complaints Pending Resolution At The End Of Year - Child Labour Member - Previous Year": "0",
    "Number Of Complaints Filed During The Year - Forced Labour Or Involuntary Labour Member - Previous Year": "0",
    "Number Of Complaints Pending Resolution At The End Of Year - Forced Labour Or Involuntary Labour Member - Previous Year": "0",
    "Number Of Complaints Filed During The Year - Wages Member - Previous Year": "0",
    "Number Of Complaints Pending Resolution At The End Of Year - Wages Member - Previous Year": "0",
    "Number Of Complaints Filed During The Year - Otherhumanrightsrelatedissues Member - Previous Year": "0",
    "Number Of Complaints Pending Resolution At The End Of Year - Otherhumanrightsrelatedissues Member - Previous Year": "0",
    "Total Complaints Reported Under Sexual Harassment Of Women At Workplace": "0",
    "Total Complaints Reported Under Sexual Harassment Of Women At Workplace - Previous Year": "0",
    "Average Number Of Female Employees Or Workers At The Beginning Of The Year And As At End Of The Year": "0",
    "Average Number Of Female Employees Or Workers At The Beginning Of The Year And As At End Of The Year - Previous Year": "0",
    "Percentage Of Complaints In Respect Of Number Of Employees Or Worker": "0",
    "Percentage Of Complaints In Respect Of Number Of Employees Or Worker - Previous Year": "0",
    "Complaints On POSHUp Held": "0",
    "Complaints On POSHUp Held - Previous Year": "0",
    "Whether Details Of Total Energy Consumption And Energy Intensity Applicable To The Company": "0",
    "Revenue From Operations": "0",
    "Revenue From Operations - Previous Year": "0",
    "Total Electricity Consumption From Renewable Sources": "0",
    "Total Electricity Consumption From Renewable Sources - Previous Year": "0",
    "Total Fuel Consumption From Renewable Sources": "0",
    "Total Fuel Consumption From Renewable Sources - Previous Year": "0",
    "Energy Consumption Through Other Sources From Renewable Sources": "0",
    "Energy Consumption Through Other Sources From Renewable Sources - Previous Year": "0",
    "Total Energy Consumed From Renewable Sources": "0",
    "Total Energy Consumed From Renewable Sources - Previous Year": "0",
    "Total Electricity Consumption From Non Renewable Sources": "0",
    "Total Electricity Consumption From Non Renewable Sources - Previous Year": "0",
    "Total Fuel Consumption From Non Renewable Sources": "0",
    "Total Fuel Consumption From Non Renewable Sources - Previous Year": "0",
    "Energy Consumption Through Other Sources From Non Renewable Sources": "0",
    "Energy Consumption Through Other Sources From Non Renewable Sources - Previous Year": "0",
    "Total Energy Consumed From Non Renewable Sources": "0",
    "Total Energy Consumed From Non Renewable Sources - Previous Year": "0",
    "Total Energy Consumed From Renewable And Non Renewable Sources": "0",
    "Total Energy Consumed From Renewable And Non Renewable Sources - Previous Year": "0",
    "Energy Intensity Per Rupee Of Turnover": "0",
    "Energy Intensity Per Rupee Of Turnover - Previous Year": "0",
    "Energy Intensity Per Rupee Of Turnover Adjusting For Purchasing Power Parity": "0",
    "Energy Intensity Per Rupee Of Turnover Adjusting For Purchasing Power Parity - Previous Year": "0",
    "Energy Intensity In Term Of Physical Output": "0",
    "Energy Intensity In Term Of Physical Output - Previous Year": "0",
    "Whether Any Independent Assessment Or Evaluation Or Assurance Has Been Carried Out By An External Agency For Energy Consumption Under Leadership Indicators": "0",
    "Does The Entity Have Any Sites Or Facilities Identified As Designated Consumers Under The Performance Achieve And Trade Scheme Of The Government Of India": "0",
    "Water Withdrawal By Surface Water": "0",
    "Water Withdrawal By Surface Water - Previous Year": "0",
    "Water Withdrawal By Groundwater": "0",
    "Water Withdrawal By Groundwater - Previous Year": "0",
    "Water Withdrawal By Third Party Water": "0",
    "Water Withdrawal By Third Party Water - Previous Year": "0",
    "Water Withdrawal By Seawater Or Desalinated Water": "0",
    "Water Withdrawal By Seawater Or Desalinated Water - Previous Year": "0",
    "Water Withdrawal By Others": "0",
    "Water Withdrawal By Others - Previous Year": "0",
    "Total Volume Of Water Withdrawal": "0",
    "Total Volume Of Water Withdrawal - Previous Year": "0",
    "Total Volume Of Water Consumption": "0",
    "Total Volume Of Water Consumption - Previous Year": "0",
    "Water Intensity Per Rupee Of Turnover": "0",
    "Water Intensity Per Rupee Of Turnover - Previous Year": "0",
    "Water Intensity Per Rupee Of Turnover Adjusting For Purchasing Power Parity": "0",
    "Water Intensity Per Rupee Of Turnover Adjusting For Purchasing Power Parity - Previous Year": "0",
    "Water Intensity In Term Of Physical Output": "0",
    "Water Intensity In Term Of Physical Output - Previous Year": "0",
    "Any Independent Assessment Or Evaluation Or Assurance Has Been Carried Out By An External Agency For Water Withdrawal": "0",
    "Water Discharge To Surface Water": "0",
    "Water Discharge To Surface Water - Previous Year": "0",
    "Water Discharge To Surface Water With Out Treatment":
        "{Water Discharge To Surface Water} - {Water Discharge To Surface Water With Treatment}",
    "Water Discharge To Surface Water With Out Treatment - Previous Year":
        "{Water Discharge To Surface Water - Previous Year} - {Water Discharge To Surface Water With Treatment - Previous Year}",
    "Water Discharge To Surface Water With Treatment":
        "{Water Discharge To Surface Water} - {Water Discharge To Surface Water With Out Treatment}",
    "Water Discharge To Surface Water With Treatment - Previous Year":
        "{Water Discharge To Surface Water - Previous Year} - {Water Discharge To Surface Water With Out Treatment - Previous Year}",
    "Water Discharge To Groundwater": "0",
    "Water Discharge To Groundwater - Previous Year": "0",
    "Water Discharge To Groundwater With Out Treatment":
        "{Water Discharge To Groundwater} - {Water Discharge To Groundwater With Treatment}",
    "Water Discharge To Groundwater With Out Treatment - Previous Year":
        "{Water Discharge To Groundwater - Previous Year} - {Water Discharge To Groundwater With Treatment - Previous Year}",
    "Water Discharge To Groundwater With Treatment":
        "{Water Discharge To Groundwater} - {Water Discharge To Groundwater With Out Treatment}",
    "Water Discharge To Groundwater With Treatment - Previous Year":
        "{Water Discharge To Groundwater - Previous Year} - {Water Discharge To Groundwater With Out Treatment - Previous Year}",
    "Water Discharge To Seawater": "0",
    "Water Discharge To Seawater - Previous Year": "0",
    "Water Discharge To Seawater With Out Treatment":
        "{Water Discharge To Seawater} - {Water Discharge To Seawater With Treatment}",
    "Water Discharge To Seawater With Out Treatment - Previous Year":
        "{Water Discharge To Seawater - Previous Year} - {Water Discharge To Seawater With Treatment - Previous Year}",
    "Water Discharge To Seawater With Treatment":
        "{Water Discharge To Seawater} - {Water Discharge To Seawater With Out Treatment}",
    "Water Discharge To Seawater With Treatment - Previous Year":
        "{Water Discharge To Seawater - Previous Year} - {Water Discharge To Seawater With Out Treatment - Previous Year}",
    "Water Discharge By Sent To Third Parties": "0",
    "Water Discharge By Sent To Third Parties - Previous Year": "0",
    "Water Discharge By Sent To Third Parties Without Treatment": "0",
    "Water Discharge By Sent To Third Parties Without Treatment - Previous Year": "0",
    "Water Discharge By Sent To Third Parties With Treatment": "0",
    "Water Discharge By Sent To Third Parties With Treatment - Previous Year": "0",
    "Water Discharge To Others": "0",
    "Water Discharge To Others - Previous Year": "0",
    "Water Discharge To Others Without Treatment": "0",
    "Water Discharge To Others Without Treatment - Previous Year": "0",
    "Water Discharge To Others With Treatment": "0",
    "Water Discharge To Others With Treatment - Previous Year": "0",
    "Total Water Discharged In Kilolitres": "0",
    "Total Water Discharged In Kilolitres - Previous Year": "0",
    "Whether Any Independent Assessment Or Evaluation Or Assurance Has Been Carried Out By An External Agency For Water Discharged": "0",
    "Whether Details Of Air Emissions Other Than Ghg Emissions By The Entity Is Applicable To The Company": "0",
    "NOx": "0",
    "NOx - Previous Year": "0",
    "SOx": "0",
    "SOx - Previous Year": "0",
    "Particulate Matter": "0",
    "Particulate Matter - Previous Year": "0",
    "Persistent Organic Pollutants": "0",
    "Persistent Organic Pollutants - Previous Year": "0",
    "Volatile Organic Compounds": "0",
    "Volatile Organic Compounds - Previous Year": "0",
    "Hazardous Air Pollutants": "0",
    "Hazardous Air Pollutants - Previous Year": "0",
    "Other Emissions - Other Air Emissions Domain1 - Previous Year": "0",
    "Indicate If Any Independent Assessment Or Evaluation Or Assurance Has Been Carried Out By An External Agency For Air Emissions Other Than GHGEmissions": "0",
    "Whether Details Of Green House Gas Emissions And Its Intensity Is Applicable To The Company": "0",
    "Total Scope1 Emissions": "0",
    "Total Scope1 Emissions - Previous Year": "0",
    "Total Scope2 Emissions": "0",
    "Total Scope2 Emissions - Previous Year": "0",
    "Total Scope1 And Scope2 Emissions Intensity Per Rupee Of Turnover - Previous Year": "0",
    "Total Scope1 And Scope2 Emissions Intensity Per Rupee Of Turnover Adjusted For Purchasing Power Parity - Previous Year": "0",
    "Total Scope1 And Scope2 Emissions Intensity In Term Of Physical Output": "0",
    "Total Scope1 And Scope2 Emissions Intensity In Term Of Physical Output - Previous Year": "0",
    "Total Scope1 And Scope2 Emissions Intensity The Relevant Metric May Be Selected By The Entity": "0",
    "Total Scope1 And Scope2 Emissions Intensity The Relevant Metric May Be Selected By The Entity - Previous Year": "0",
    "Whether Any Indicate If Any Independent Assessment Or Evaluation Or Assurance Has Been Carried Out By An External Agency For Green House Gas Emissions": "0",
    "Plastic Waste": "0",
    "Plastic Waste - Previous Year": "0",
    "EWaste": "0",
    "EWaste - Previous Year": "0",
    "Bio Medical Waste": "0",
    "Bio Medical Waste - Previous Year": "0",
    "Construction And Demolition Waste": "0",
    "Construction And Demolition Waste - Previous Year": "0",
    "Battery Waste": "0",
    "Battery Waste - Previous Year": "0",
    "Radioactive Waste": "0",
    "Radioactive Waste - Previous Year": "0",
    "Other Hazardous Waste": "0",
    "Other Hazardous Waste - Previous Year": "0",
    "Other Non Hazardous Waste Generated": "0",
    "Other Non Hazardous Waste Generated - Previous Year": "0",
    "Total Waste Generated": "0",
    "Total Waste Generated - Previous Year": "0",
    "Waste Intensity Per Rupee Of Turnover":
        "{Total Waste Generated} / {Revenue From Operations}",
    "Waste Intensity Per Rupee Of Turnover - Previous Year":
        "{Total Waste Generated} / {Revenue From Operations}",
    "Waste Intensity Per Rupee Of Turnover Adjusting For Purchasing Power Parity":
        "{Total Waste Generated} / {Revenue From Operations}",
    "Waste Intensity Per Rupee Of Turnover Adjusting For Purchasing Power Parity - Previous Year":
        "{Total Waste Generated} / {Revenue From Operations}",
    "Waste Intensity In Term Of Physical Output":
        "{Total Waste Generated} / {Revenue From Operations}",
    "Waste Intensity In Term Of Physical Output - Previous Year":
        "{Total Waste Generated} / {Revenue From Operations}",
    "Waste Recovered Through Recycled": "0",
    "Waste Recovered Through Recycled - Previous Year": "0",
    "Waste Recovered Through Re Used": "0",
    "Waste Recovered Through Re Used - Previous Year": "0",
    "Waste Recovered Through Other Recovery Operations": "0",
    "Waste Recovered Through Other Recovery Operations - Previous Year": "0",
    "Total Waste Recovered": "0",
    "Total Waste Recovered - Previous Year": "0",
    "Waste Disposed By Incineration": "0",
    "Waste Disposed By Incineration - Previous Year": "0",
    "Waste Disposed By Landfilling": "0",
    "Waste Disposed By Landfilling - Previous Year": "0",
    "Waste Disposed By Other Disposal Operations": "0",
    "Waste Disposed By Other Disposal Operations - Previous Year": "0",
    "Total Waste Disposed": "0",
    "Total Waste Disposed - Previous Year": "0",
    "Whether Any Independent Assessment Or Evaluation Or Assurance Has Been Carried Out By An External Agency For Waste Management": "0",
    "Whether Total Scope3 Emissions And Its Intensity Is Applicable To The Company": "0",
    "Number Of Affiliations With Trade And Industry Chambers Or Associations": "0",
    "Percentage Of Directly Sourced From MSMEs Or Small Producers": "0",
    "Percentage Of Directly Sourced From MSMEs Or Small Producers - Previous Year": "0",
    "Percentage Of Sourced Directly From Within The District And Neighbouring Districts": "0",
    "Percentage Of Sourced Directly From Within The District And Neighbouring Districts - Previous Year": "0",
    "Disclose Wages Paid To Persons Employed - Rural Member": "0",
    "Disclose Wages Paid To Persons Employed - Rural Member - Previous Year": "0",
    "Total Wage Cost - Rural Member": "0",
    "Total Wage Cost - Rural Member - Previous Year": "0",
    "Percentage Of Job Creation - Rural Member": "0",
    "Percentage Of Job Creation - Rural Member - Previous Year": "0",
    "Disclose Wages Paid To Persons Employed - Semi Urban Member": "0",
    "Disclose Wages Paid To Persons Employed - Semi Urban Member - Previous Year": "0",
    "Total Wage Cost - Semi Urban Member": "0",
    "Total Wage Cost - Semi Urban Member - Previous Year": "0",
    "Percentage Of Job Creation - Semi Urban Member": "0",
    "Percentage Of Job Creation - Semi Urban Member - Previous Year": "0",
    "Disclose Wages Paid To Persons Employed - Urban Member": "0",
    "Disclose Wages Paid To Persons Employed - Urban Member - Previous Year": "0",
    "Total Wage Cost - Urban Member": "0",
    "Total Wage Cost - Urban Member - Previous Year": "0",
    "Percentage Of Job Creation - Urban Member": "0",
    "Percentage Of Job Creation - Urban Member - Previous Year": "0",
    "Disclose Wages Paid To Persons Employed - Metropolitan Member": "0",
    "Disclose Wages Paid To Persons Employed - Metropolitan Member - Previous Year": "0",
    "Total Wage Cost - Metropolitan Member": "0",
    "Total Wage Cost - Metropolitan Member - Previous Year": "0",
    "Percentage Of Job Creation - Metropolitan Member": "0",
    "Percentage Of Job Creation - Metropolitan Member - Previous Year": "0",
    "Environmental And Social Parameters Relevant To The Product As APercentage To Total Turnover": "0",
    "Safe And Responsible Usage As APercentage To Total Turnover": "0",
    "Recycling And Or Safe Disposal As APercentage To Total Turnover": "0",
    "Consumer Complaints Received During The Year - Data Privacy Member": "0",
    "Consumer Complaints Pending Resolution At End Of Year - Data Privacy Member": "0",
    "Consumer Complaints Received During The Year - Advertising Member": "0",
    "Consumer Complaints Pending Resolution At End Of Year - Advertising Member": "0",
    "Consumer Complaints Received During The Year - Cyber Security Member": "0",
    "Consumer Complaints Pending Resolution At End Of Year - Cyber Security Member": "0",
    "Consumer Complaints Received During The Year - Delivery Of Essential Services Member": "0",
    "Consumer Complaints Pending Resolution At End Of Year - Delivery Of Essential Services Member": "0",
    "Consumer Complaints Received During The Year - Restrictive Trade Practices Member": "0",
    "Consumer Complaints Pending Resolution At End Of Year - Restrictive Trade Practices Member": "0",
    "Consumer Complaints Received During The Year - Unfair Trade Practices Member": "0",
    "Consumer Complaints Pending Resolution At End Of Year - Unfair Trade Practices Member": "0",
    "Consumer Complaints Received During The Year - Other Member": "0",
    "Consumer Complaints Pending Resolution At End Of Year - Other Member": "0",
    "Consumer Complaints Received During The Year - Data Privacy Member - Previous Year": "0",
    "Consumer Complaints Pending Resolution At End Of Year - Data Privacy Member - Previous Year": "0",
    "Consumer Complaints Received During The Year - Advertising Member - Previous Year": "0",
    "Consumer Complaints Pending Resolution At End Of Year - Advertising Member - Previous Year": "0",
    "Consumer Complaints Received During The Year - Cyber Security Member - Previous Year": "0",
    "Consumer Complaints Pending Resolution At End Of Year - Cyber Security Member - Previous Year": "0",
    "Consumer Complaints Received During The Year - Delivery Of Essential Services Member - Previous Year": "0",
    "Consumer Complaints Pending Resolution At End Of Year - Delivery Of Essential Services Member - Previous Year": "0",
    "Consumer Complaints Received During The Year - Restrictive Trade Practices Member - Previous Year": "0",
    "Consumer Complaints Pending Resolution At End Of Year - Restrictive Trade Practices Member - Previous Year": "0",
    "Consumer Complaints Received During The Year - Unfair Trade Practices Member - Previous Year": "0",
    "Consumer Complaints Pending Resolution At End Of Year - Unfair Trade Practices Member - Previous Year": "0",
    "Consumer Complaints Received During The Year - Other Member - Previous Year": "0",
    "Consumer Complaints Pending Resolution At End Of Year - Other Member - Previous Year": "0",
    "Number Of Voluntary Recalls": "0",
    "Number Of Forced Recalls": "0",
    "Number Of Instances Of Data Breaches Along With Impact": "0",
    "Percentage Of Data Breaches Involving Personally Identifiable Information Of Customers": "0",
    "Whether Corporate Identity Number Is Assured By Assurer": "0",
    "Whether Name Of The Company Is Assured By Assurer": "0",
    "Whether Year Of Incorporation Is Assured By Assurer": "0",
    "Whether Address Of Registered Office Of Company Is Assured By Assurer": "0",
    "Whether Address Of Corporate Office Of Company Is Assured By Assurer": "0",
    "Whether EMail Of The Company Is Assured By Assurer": "0",
    "Whether Telephone Of Company Is Assured By Assurer": "0",
    "Whether Website Of Company Is Assured By Assurer": "0",
    "Whether Details Of Financial Year For Which Reporting Is Being Done Is Assured By Assurer": "0",
    "Whether Details Of The Stock Exchange Where The Company Is Listed Is Assured By Assurer": "0",
    "Whether Value Of Shares Paid Up Is Assured By Assurer": "0",
    "Whether Name And Contact Details Of The Contact Person In Case Of Any Queries On The BRSRReport Is Assured By Assurer": "0",
    "Whether Reporting Boundary Is Assured By Assurer": "0",
    "Whether Details Of Business Activities Accounting For Ninety Percent Of The Turnover Is Assured By Assurer": "0",
    "Whether Products Or Services Sold By The Entity Accounting For Ninety Percent Of The Turnover Is Assured By Assurer": "0",
    "Whether Details Of Number Of Locations Where Plants And Or Operations Or Offices Of The Entity Are Situated Is Assured By Assurer": "0",
    "Whether Markets Served By The Entity Is Assured By Assurer": "0",
    "Whether Details Of Employees As At The End Of Financial Year Is Assured By Assurer": "0",
    "Whether Participation Or Inclusion Or Representation Of Women Is Assured By Assurer": "0",
    "Whether Turnover Rate For Permanent Employees And Workers Disclose Trends For Past Three Years Is Assured By Assurer": "0",
    "Whether Names Of Holding Subsidiary Associate Companies Joint Ventures Is Assured By Assurer": "0",
    "Whether CSRIs Applicable As Per Section135 Of Companies Act2013 Is Assured By Assurer": "0",
    "Whether Complaints Or Grievances On Any Of The Principles Under The National Guidelines On Responsible Business Conduct Is Assured By Assurer": "0",
    "Whether Overview Of The Entitys Material Responsible Business Conduct Issues Is Assured By Assurer": "0",
    "Assurer Has Assured Whether Your Entitys Policy Or Policies Cover Each Principle And Its Core Elements Of The NGRBCs": "0",
    "Assurer Has Assured Whether The Entity Has Translated The Policy Into Procedures": "0",
    "Assurer Has Assured Whether The Enlisted Policies Extend To Your Value Chain Partners": "0",
    "Whether Name Of The National And International Codes Or Certifications Or Labels Or Standards Adopted By Your Entity And Mapped To Each Principle Is Assured By Assurer": "0",
    "Whether Specific Commitments Goals And Targets Set By The Entity With Defined Timelines Is Assured By Assurer": "0",
    "Whether Performance Of The Entity Against The Specific Commitments Goals And Targets Along With Reasons In Case The Same Are Not Met Is Assured By Assurer": "0",
    "Whether Statement By Director Responsible For The Business Responsibility Report Highlighting ESGRelated Challenges Targets And Achievements Is Assured By Assurer": "0",
    "Whether Details Of The Highest Authority Responsible For Implementation And Oversight Of The Business Responsibility Policy Is Assured By Assurer": "0",
    "Assurer Has Assured Whether The Entity Have ASpecified Committee Of The Board Or Director Responsible For Decision Making On Sustainability Related Issues": "0",
    "Whether Performance Against Above Policies And Follow Up Action Is Assured By Assurer": "0",
    "Whether Compliance With Statutory Requirements Of Relevance To The Principles And Rectification Of Any Non Compliances Is Assured By Assurer": "0",
    "Assurer Has Assured Whether The Entity Has Carried Out Independent Assessment Evaluation Of The Working Of Its Policies By An External Agency": "0",
    "Whether Reasons If Policies Not Cover Each Principle And Its Core Elements Of The NGRBCs Is Assured By Assurer": "0",
    "Whether Percentage Coverage By Training And Awareness Programs On Any Of The Principles During The Financial Year For BODOr KMPOr Employee Or Worker Is Assured By Assurer": "0",
    "Whether Details Of Fines Or Penalties Or Punishment Or Award Or Compounding Fees Or Settlement Is Assured By Assurer": "0",
    "Whether Details Of The Appeal Or Revision Preferred In Cases Where Monetary Or Non Monetary Action Has Been Appealed Is Assured By Assurer": "0",
    "Whether Details And Weblink Of An Anti Corruption Or Anti Bribery Policy Is Place Is Assured By Assurer": "0",
    "Whether Number Of Directors Or KMPs Or Employees Or Workers Against Whom Disciplinary Action Was Taken By Any Law Enforcement Agency For The Charges Of Bribery Or Corruption Is Assured By Assurer": "0",
    "Whether Details Of Complaints With Regard To Conflict Of Interest Is Assured By Assurer": "0",
    "Whether Details Of Any Corrective Action Taken Or Underway On Issues Related To Fines Or Penalties Or Action Taken By Regulators Or Law Enforcement Agencies Or Judicial Institutions On Cases Of Corruption And Conflicts Of Interest Is Assured By Assurer": "0",
    "Whether Number Of Days Of Accounts Payables Is Assured By Assurer": "0",
    "Whether Details Of Concentration Of Purchases And Sales With Trading Houses Dealers And Related Parties Along With Loans And Advances And Investments With Related Parties Is Assured By Assurer": "0",
    "Whether Awareness Programmes Conducted For Value Chain Partners On Any Of The Principles During The Financial Year Is Assured By Assurer": "0",
    "Whether The Entity Have Processes In Place To Avoid Or Manage Conflict Of Interests Involving Members Of The Board Is Assured By Assurer": "0",
    "Whether Percentage Of RAnd DAnd Capital Expenditure Investments In Specific Technologies Is Assured By Assurer": "0",
    "Whether The Entity Have Procedures In Place For Sustainable Sourcing And Percentage Of Inputs Were Sourced Sustainably Is Assured By Assurer": "0",
    "Whether Describe The Processes In Place To Safely Reclaim Your Products For Reusing Recycling And Disposing At The End Of Life For Plastics Including Packaging EWaste Hazardous Waste And Other Waste Is Assured By Assurer": "0",
    "Assurer Has Assured Whether The Waste Collection Plan Is In Line With The Extended Producer Responsibility Plan Submitted To Pollution Control Boards And Steps Taken To Address The Waste Collection Plan If Not Submitted": "0",
    "Assurer Has Assured Whether The Entity Conducted Life Cycle Perspective Or Assessments For Any Of Its Products Or For Its Services": "0",
    "Whether Details Of Significant Social Or Environmental Concerns From Production Or Disposal Of Product Or Service With Action Taken To Mitigate The Same Is Assured By Assurer": "0",
    "Whether Details Of Percentage Of Recycled Or Reused Input Material To Total Material By Value Used In Production Or Providing Services Is Assured By Assurer": "0",
    "Whether The Products And Packaging Reclaimed At End Of Life Of Products Amount Reused Or Recycled Or Safely Disposed Is Assured By Assurer": "0",
    "Whether Details Of Reclaimed Products And Their Packaging Materials For Each Product Category Is Assured By Assurer": "0",
    "Whether Details Of Measures For The Well Being Of Employees And Workers And Spending On It Is Assured By Assurer": "0",
    "Whether Details Of Retirement Benefits Is Assured By Assurer": "0",
    "Whether The Premises Or Offices Of The Entity Accessible To Differently Abled Employees And Workers And Steps Are Being Taken By The Entity If The Premises Or Offices Of The Entity Not Accessible Is Assured By Assurer": "0",
    "Whether Return To Work And Retention Rates Of Permanent Employees And Workers That Took Parental Leave Is Assured By Assurer": "0",
    "Assurer Has Assured Whether Is There AMechanism Available To Receive And Redress Grievances For The Following Categories Of Employees And Worker": "0",
    "Whether Membership Of Employees And Worker In Associations Or Unions Recognised By The Listed Entity Is Assured By Assurer": "0",
    "Whether Details Of Training Given To Employees And Workers Is Assured By Assurer": "0",
    "Whether Details Of Performance And Career Development Reviews Of Employees And Worker Is Assured By Assurer": "0",
    "Whether Health And Safety Management System Is Assured By Assurer": "0",
    "Whether Details Of Safety Related Incidents Is Assured By Assurer": "0",
    "Whether Measures Taken By The Entity To Ensure ASafe And Healthy Work Place Is Assured By Assurer": "0",
    "Whether Assessments Of Your Plants And Offices That Were Assessed For The Year P3 Is Assured By Assurer": "0",
    "Whether Details Of Any Corrective Action Taken Or Underway To Address Safety Related Incidents Of Your Plants And Offices That Were Assessed Is Assured By Assurer": "0",
    "Assurer Has Assured Whether The Entity Extend Any Life Insurance Or Any Compensatory Package In The Event Of Death Of Employees": "0",
    "Whether Details Of Measures Undertaken By The Entity To Ensure That Statutory Dues Have Been Deducted And Deposited By The Value Chain Partners Is Assured By Assurer": "0",
    "Whether Details Of Number Of Employees Or Workers Having Suffered High Consequence Work Related Injury Or Ill Health Or Fatalities Who Or Whose Family Members Are Rehabilitated And Placed In Suitable Employment Is Assured By Assurer": "0",
    "Assurer Has Assured Whether The Entity Provide Transition Assistance Programs To Facilitate Continued Employability And The Management Of Career Endings Resulting From Retirement Or Termination Of Employment": "0",
    "Whether Details On Assessment Of Value Chain Partners P3 Is Assured By Assurer": "0",
    "Whether Details Of Any Corrective Action Taken Or Underway To Address Safety Related Incidents On Assessment Of Value Chain Partners Is Assured By Assurer": "0",
    "Whether The Processes For Identifying Key Stakeholder Groups Of The Entity Is Assured By Assurer": "0",
    "Whether List Stakeholder Groups Identified As Key For Your Entity And The Frequency Of Engagement With Each Stakeholder Group Is Assured By Assurer": "0",
    "Whether The Processes For Consultation Between Stakeholders And The Board On Economic Environmental And Social Topics Or If Consultation Is Delegated How Is Feedback From Such Consultations Provided To The Board Is Assured By Assurer": "0",
    "Assurer Has Assured Whether Stakeholder Consultation Is Used To Support The Identification And Management Of Environmental And Social Topics": "0",
    "Whether Details Of Instances Of Engagement With And Actions Taken To Address The Concerns Of Vulnerable Or Marginalized Stakeholder Groups Is Assured By Assurer": "0",
    "Whether Employees And Workers Who Have Been Provided Training On Human Rights Issues And Policies Of The Entity Is Assured By Assurer": "0",
    "Whether Details Of Minimum Wages Paid To Employees And Workers Is Assured By Assurer": "0",
    "Whether Details Of Median Of Remuneration Or Salary Or Wages And Wages Paid To Female Is Assured By Assurer": "0",
    "Assurer Has Assured Whether Do You Have AFocal Point Responsible For Addressing Human Rights Impacts Or Issues Caused Or Contributed To By The Business": "0",
    "Whether The Internal Mechanisms In Place To Redress Grievances Related To Human Rights Issues Is Assured By Assurer": "0",
    "Whether Complaints Filed Under The Sexual Harassment Of Women At Workplace Is Assured By Assurer": "0",
    "Whether Mechanisms To Prevent Adverse Consequences To The Complainant In Discrimination And Harassment Cases Is Assured By Assurer": "0",
    "Whether Human Rights Requirements Form Part Of Your Business Agreements And Contracts Is Assured By Assurer": "0",
    "Whether Assessments Of Your Plants And Offices That Were Assessed For The Year P5 Is Assured By Assurer": "0",
    "Whether Details Of Any Corrective Actions Taken Or Underway To Address Significant Risks Or Concerns Arising From The Assessments Of Plant And Office Is Assured By Assurer": "0",
    "Whether Details Of ABusiness Process Being Modified Or Introduced As AResult Of Addressing Human Rights Grievances Or Complaints Is Assured By Assurer": "0",
    "Whether Details Of The Scope And Coverage Of Any Human Rights Due Diligence Conducted Is Assured By Assurer": "0",
    "Whether Details On Assessment Of Value Chain Partners P5 Is Assured By Assurer": "0",
    "Whether Details Of Any Corrective Actions Taken Or Underway To Address Significant Risks Or Concerns Arising From The Assessments Of Value Chain Partner Is Assured By Assurer": "0",
    "Whether Details Of Total Energy Consumption In Joules Or Multiples And Energy Intensity Is Assured By Assurer": "0",
    "Assurer Has Assured Whether The Entity Have Any Sites Or Facilities Identified As Designated Consumers Under The Performance Achieve And Trade Scheme Of The Government Of India": "0",
    "Whether Details Of The Disclosures Related To Water Withdrawal Is Assured By Assurer": "0",
    "Whether Details Of The Disclosures Related To Water Discharged Is Assured By Assurer": "0",
    "Whether The Entity Implemented AMechanism For Zero Liquid Discharge Is Assured By Assurer": "0",
    "Whether Details Of Air Emissions Other Than Ghg Emissions By The Entity Is Assured By Assurer": "0",
    "Whether Details Of Green House Gas Emissions And Its Intensity Is Assured By Assurer": "0",
    "Assurer Has Assured Whether The Entity Have Any Project Related To Reducing Green House Gas Emission": "0",
    "Whether Details Related To Waste Management By The Entity Is Assured By Assurer": "0",
    "Whether Details Of Waste Management Practices Adopted In Your Establishments And The Strategy Adopted By Company To Reduce Usage Of Hazardous And Toxic Chemicals Is Assured By Assurer": "0",
    "Whether Details Of Operations Or Offices In Or Around Ecologically Sensitive Areas Where Environmental Approvals Or Clearances Are Required Is Assured By Assurer": "0",
    "Whether Details Of Environmental Impact Assessments Of Projects Undertaken By The Entity Based On Applicable Laws Is Assured By Assurer": "0",
    "Assurer Has Assured Whether The Entity Compliant With The Applicable Environmental Law": "0",
    "Whether Water Withdrawal Or Consumption And Discharge In Areas Of Water Stress In Kilolitres Is Assured By Assurer": "0",
    "Whether Details Of Total Scope3 Emissions And Its Intensity Is Assured By Assurer": "0",
    "Whether Details Of Significant Direct And Indirect Impact Of The Entity On Biodiversity In Such Areas Along With Prevention And Remediation Activities Is Assured By Assurer": "0",
    "Whether The Entity Has Undertaken Any Specific Initiatives Or Used Innovative Technology Or Solutions To Improve Resource Efficiency Is Assured By Assurer": "0",
    "Assurer Has Assured Whether The Entity Have ABusiness Continuity And Disaster Management Plan": "0",
    "Whether Disclose Any Significant Adverse Impact To The Environment Arising From The Value Chain Of The Entity What Mitigation Or Adaptation Measures Have Been Taken By The Entity In This Regard Is Assured By Assurer": "0",
    "Whether Percentage Of Value Chain Partners By Value Of Business Done With Such Partners That Were Assessed For Environmental Impacts Is Assured By Assurer": "0",
    "Whether Green Credits Have Been Generated Or Procured By The Listed Entity And Top Ten Value Chain Partners Is Assured By Assurer": "0",
    "Whether The Entity Is AMember Of Or Affiliated To Trade And Industry Chambers Or Associations Determined Based On The Total Members Of Such Body Is Assured By Assurer": "0",
    "Whether Details Of Corrective Action Taken Or Underway On Any Issues Related To Anti Competitive Conduct By The Entity Based On Adverse Orders From Regulatory Authorities Is Assured By Assurer": "0",
    "Whether Details Of Public Policy Positions Advocated By The Entity Is Assured By Assurer": "0",
    "Whether Details Of Social Impact Assessments Of Projects Undertaken By The Entity Based On Applicable Laws Is Assured By Assurer": "0",
    "Whether Details Of Projects For Which Ongoing Rehabilitation And Resettlement Is Being Undertaken By Entity Is Assured By Assurer": "0",
    "Whether Describe The Mechanisms To Receive And Redress Grievances Of The Community Is Assured By Assurer": "0",
    "Whether Percentage Of Input Material Inputs To Total Inputs By Value Sourced From Suppliers Is Assured By Assurer": "0",
    "Whether Job Creation In Smaller Towns Disclose Wages Paid To Persons Employed Including Employees Or Workers Employed On APermanent Or Non Permanent Or On Contract Basis Is Assured By Assurer": "0",
    "Whether Details Of Actions Taken To Mitigate Any Negative Social Impacts Identified In The Social Impact Assessments Is Assured By Assurer": "0",
    "Whether Details Of CSRProjects Undertaken In Designated Aspirational Districts As Identified By Government Bodies Is Assured By Assurer": "0",
    "Whether APreferential Procurement Policy Where Preference To Purchase From Suppliers Comprising Marginalized Or Vulnerable Groups And Its Percentage Of Total Procurement By Value Does It Constitute Is Assured By Assurer": "0",
    "Whether Details Of The Benefits Derived And Shared From The Intellectual Properties Owned Or Acquired Is Assured By Assurer": "0",
    "Whether Details Of Corrective Actions Taken Or Underway Based On Any Adverse Order In Intellectual Property Related Disputes Wherein Usage Of Traditional Knowledge Is Involved Is Assured By Assurer": "0",
    "Whether Details Of Beneficiaries Of CSRProjects Is Assured By Assurer": "0",
    "Whether The Mechanisms In Place To Receive And Respond To Consumer Complaints And Feedback Is Assured By Assurer": "0",
    "Whether Turnover Of Products And Or Services As APercentage Of Turnover From All Products Or Service That Carry Information About As APercentage To Total Turnover Is Assured By Assurer": "0",
    "Whether Details Of Number Of Consumer Complaints P9 Is Assured By Assurer": "0",
    "Whether Details Of Instances Of Product Recalls On Account Of Safety Issues Is Assured By Assurer": "0",
    "Assurer Has Assured Whether The Entity Have AFramework Or Policy On Cyber Security And Risks Related To Data Privacy": "0",
    "Whether Details Of Any Corrective Actions Taken Or Underway On Issues Relating To Advertising And Delivery Of Essential Services Or Cyber Security And Data Privacy Or Recalls Or Penalty Or Action Taken By Regulatory Authorities On Safety Of Products Or Services Is Assured By Assurer": "0",
    "Whether Data Breaches Information Like Number Of Instances Of Data Breaches Along With Impact And Percentage Of Data Breaches Involving Personally Identifiable Information Of Customers Is Assured By Assurer": "0",
    "Whether Weblink Where Information On Products And Services Of The Entity Can Be Accessed Is Assured By Assurer": "0",
    "Whether Steps Taken To Inform And Educate Consumers About Safe And Responsible Usage Of Products And Or Services Is Assured By Assurer": "0",
    "Whether Mechanisms In Place To Inform Consumers Of Any Risk Of Disruption Or Discontinuation Of Essential Services Is Assured By Assurer": "0",
    "Assurer Has Assured Whether The Entity Display Product Information On The Product Over And Above What Is Mandated As Per Local Laws": "0",
    "Number Of Employees Covered As Percentage Of Total Employees - Other Retirement Benefits Domain1 - Previous Year": "0",
    "Number Of Employees Covered As Percentage Of Total Worker - Other Retirement Benefits Domain1 - Previous Year": "0",
    "Does The Entity Extend Any Life Insurance Or Any Compensatory Package In The Event Of Death Of Employees": "0",
    "Does The Entity Extend Any Life Insurance Or Any Compensatory Package In The Event Of Death Of Workers": "0",
    "Total Number Of Affected Employees": "0",
    "Total Number Of Affected Employees - Previous Year": "0",
    "Number Of Employees Or Whose Family Members Rehabilitated And Placed In Suitable Employment": "0",
    "Number Of Employees Or Whose Family Members Rehabilitated And Placed In Suitable Employment - Previous Year": "0",
    "Total Number Of Affected Workers": "0",
    "Total Number Of Affected Workers - Previous Year": "0",
    "Number Of Workers Or Whose Family Members Rehabilitated And Placed In Suitable Employment": "0",
    "Number Of Workers Or Whose Family Members Rehabilitated And Placed In Suitable Employment - Previous Year": "0",
    "Whether Stakeholder Consultation Is Used To Support The Identification And Management Of Environmental And Social Topics": "0",
    "Indicate If Any Independent Assessment Or Evaluation Or Assurance Has Been Carried Out By An External Agency For Areas Of Water Stress": "0",
    "Total Scope3 Emissions": "0",
    "Total Scope3 Emissions - Previous Year": "0",
    "Total Scope3 Emissions Per Rupee Of Turnover": "0",
    "Total Scope3 Emissions Per Rupee Of Turnover - Previous Year": "0",
    "Total Scope3 Emission Intensity The Relevant Metric May Be Selected By The Entity": "0",
    "Total Scope3 Emission Intensity The Relevant Metric May Be Selected By The Entity - Previous Year": "0",
    "Whether Any Independent Assessment Or Evaluation Or Assurance Has Been Carried Out By An External Agency For Total Scope3 Emissions": "0",
    "Percentage Of Value Chain Partners By Value Of Business Done With Such Partners That Were Assessed For Environmental Impacts": "0",
    "The Entity Does Not Consider The Principles Material To Its Business - Principle7 Member": "0",
    "The Entity Is Not At AStage Where It Is In APosition To Formulate And Implement The Policies On Specified Principles - Principle7 Member": "0",
    "The Entity Does Not Have The Financial Or Human And Technical Resources Available For The Task - Principle7 Member": "0",
    "It Is Planned To Be Done In The Next Financial Year - Principle7 Member": "0",
    "Waste Intensity The Relevant Metric May Be Selected By The Entity":
        "{Total Waste Generated} / {Revenue From Operations}",
    "Waste Intensity The Relevant Metric May Be Selected By The Entity - Previous Year":
        "{Total Waste Generated} / {Revenue From Operations}",
    "Energy Consumption Through Other Sources From Renewable Sources - Energy Consumption Through Other Source From Renewable Sources Domain1 - Previous Year": "0",
    "Energy Consumption Through Other Sources From Non Renewable Sources - Energy Consumption Through Other Source From Non Renewable Sources Domain1 - Previous Year": "0",
    "Amount Of Re Used - Plastics Including Packaging Member": "0",
    "Amount Of Recycled - Plastics Including Packaging Member": "0",
    "Amount Of Safely Disposed - Plastics Including Packaging Member": "0",
    "Amount Of Re Used - Plastics Including Packaging Member - Previous Year": "0",
    "Amount Of Recycled - Plastics Including Packaging Member - Previous Year": "0",
    "Amount Of Safely Disposed - Plastics Including Packaging Member - Previous Year": "0",
    "Amount Of Re Used - EWaste Member": "0",
    "Amount Of Recycled - EWaste Member": "0",
    "Amount Of Safely Disposed - EWaste Member": "0",
    "Amount Of Re Used - EWaste Member - Previous Year": "0",
    "Amount Of Recycled - EWaste Member - Previous Year": "0",
    "Amount Of Safely Disposed - EWaste Member - Previous Year": "0",
    "Amount Of Re Used - Hazardous Waste Member": "0",
    "Amount Of Recycled - Hazardous Waste Member": "0",
    "Amount Of Safely Disposed - Hazardous Waste Member": "0",
    "Amount Of Re Used - Hazardous Waste Member - Previous Year": "0",
    "Amount Of Recycled - Hazardous Waste Member - Previous Year": "0",
    "Amount Of Safely Disposed - Hazardous Waste Member - Previous Year": "0",
    "Water Intensity The Relevant Metric May Be Selected By The Entity": "0",
    "Water Intensity The Relevant Metric May Be Selected By The Entity - Previous Year": "0",
    "Number Of Green Credits Have Been Generated Or Procured By The Listed Entity": "0",
    "Number Of Green Credits Have Been Generated Or Procured By The Top Ten Value Chain Partners": "0",
    "What Percentage Of Total Procurement By Value Does It Constitute": "0",
    "Number Of Complaints Filed From Stake Holder Group During The Year - Other Stake Holder Domain1 - Previous Year": "0",
    "Number Of Complaints Pending From Stake Holder Group Resolution At The End Of Year - Other Stake Holder Domain1 - Previous Year": "0",
    "Amount Of Re Used - Other Waste Domain1 - Previous Year": "0",
    "Amount Of Recycled - Other Waste Domain1 - Previous Year": "0",
    "Amount Of Safely Disposed - Other Waste Domain1 - Previous Year": "0",
    "Recycled Or Re Used In Put Material To Total Material - Recycled Or Reused Input Material Used In Production Or Providing Services Domain1 - Previous Year": "0",
    "Water Withdrawal By Surface Water Per Area - Facility Or Plant Located In Areas Of Water Stress Domain1 - Previous Year": "0",
    "Water Withdrawal By Groundwater Per Area - Facility Or Plant Located In Areas Of Water Stress Domain1 - Previous Year": "0",
    "Water Withdrawal By Third Party Water Per Area - Facility Or Plant Located In Areas Of Water Stress Domain1 - Previous Year": "0",
    "Water Withdrawal By Seawater Or Desalinated Water Per Area - Facility Or Plant Located In Areas Of Water Stress Domain1 - Previous Year": "0",
    "Water Withdrawal By Others Per Area - Facility Or Plant Located In Areas Of Water Stress Domain1 - Previous Year": "0",
    "Total Volume Of Water Withdrawal Per Area - Facility Or Plant Located In Areas Of Water Stress Domain1 - Previous Year": "0",
    "Total Volume Of Water Consumption Per Area - Facility Or Plant Located In Areas Of Water Stress Domain1 - Previous Year": "0",
    "Water Intensity Per Rupee Of Turnover Per Area - Facility Or Plant Located In Areas Of Water Stress Domain1 - Previous Year": "0",
    "Waste Intensity The Relevant Metric May Be Selected By The Entity Per Area - Facility Or Plant Located In Areas Of Water Stress Domain1 - Previous Year":
        "{Total Waste Generated} / {Revenue From Operations}",
    "Water Discharge To Surface Water Per Area - Facility Or Plant Located In Areas Of Water Stress Domain1 - Previous Year":
        "{Total Water Discharged In Kilolitres Per Area - Facility Or Plant Located In Areas Of Water Stress Domain1 - Previous Year} - {Water Discharge To Groundwater Per Area - Facility Or Plant Located In Areas Of Water Stress Domain1 - Previous Year} - {Water Discharge To Seawater Per Area - Facility Or Plant Located In Areas Of Water Stress Domain1 - Previous Year} - {Water Discharge By Sent To Third Parties Per Area - Facility Or Plant Located In Areas Of Water Stress Domain1 - Previous Year} - {Water Discharge To Others Per Area - Facility Or Plant Located In Areas Of Water Stress Domain1 - Previous Year}",
    "Water Discharge To Surface Water With Out Treatment Per Area - Facility Or Plant Located In Areas Of Water Stress Domain1 - Previous Year":
        "{Water Discharge To Surface Water Per Area - Facility Or Plant Located In Areas Of Water Stress Domain1 - Previous Year} - {Water Discharge To Surface Water With Treatment Per Area - Facility Or Plant Located In Areas Of Water Stress Domain1 - Previous Year}",
    "Water Discharge To Surface Water With Treatment Per Area - Facility Or Plant Located In Areas Of Water Stress Domain1 - Previous Year":
        "{Water Discharge To Surface Water Per Area - Facility Or Plant Located In Areas Of Water Stress Domain1 - Previous Year} - {Water Discharge To Surface Water With Out Treatment Per Area - Facility Or Plant Located In Areas Of Water Stress Domain1 - Previous Year}",
    "Water Discharge To Groundwater Per Area - Facility Or Plant Located In Areas Of Water Stress Domain1 - Previous Year":
        "{Total Water Discharged In Kilolitres Per Area - Facility Or Plant Located In Areas Of Water Stress Domain1 - Previous Year} - {Water Discharge To Surface Water Per Area - Facility Or Plant Located In Areas Of Water Stress Domain1 - Previous Year} - {Water Discharge To Seawater Per Area - Facility Or Plant Located In Areas Of Water Stress Domain1 - Previous Year} - {Water Discharge By Sent To Third Parties Per Area - Facility Or Plant Located In Areas Of Water Stress Domain1 - Previous Year} - {Water Discharge To Others Per Area - Facility Or Plant Located In Areas Of Water Stress Domain1 - Previous Year}",
    "Water Discharge To Groundwater With Out Treatment Per Area - Facility Or Plant Located In Areas Of Water Stress Domain1 - Previous Year":
        "{Water Discharge To Groundwater Per Area - Facility Or Plant Located In Areas Of Water Stress Domain1 - Previous Year} - {Water Discharge To Groundwater With Treatment Per Area - Facility Or Plant Located In Areas Of Water Stress Domain1 - Previous Year}",
    "Water Discharge To Groundwater With Treatment Per Area - Facility Or Plant Located In Areas Of Water Stress Domain1 - Previous Year":
        "{Water Discharge To Groundwater Per Area - Facility Or Plant Located In Areas Of Water Stress Domain1 - Previous Year} - {Water Discharge To Groundwater With Out Treatment Per Area - Facility Or Plant Located In Areas Of Water Stress Domain1 - Previous Year}",
    "Water Discharge To Seawater Per Area - Facility Or Plant Located In Areas Of Water Stress Domain1 - Previous Year":
        "{Total Water Discharged In Kilolitres Per Area - Facility Or Plant Located In Areas Of Water Stress Domain1 - Previous Year} - {Water Discharge To Surface Water Per Area - Facility Or Plant Located In Areas Of Water Stress Domain1 - Previous Year} - {Water Discharge To Groundwater Per Area - Facility Or Plant Located In Areas Of Water Stress Domain1 - Previous Year} - {Water Discharge By Sent To Third Parties Per Area - Facility Or Plant Located In Areas Of Water Stress Domain1 - Previous Year} - {Water Discharge To Others Per Area - Facility Or Plant Located In Areas Of Water Stress Domain1 - Previous Year}",
    "Water Discharge To Seawater With Out Treatment Per Area - Facility Or Plant Located In Areas Of Water Stress Domain1 - Previous Year":
        "{Water Discharge To Seawater Per Area - Facility Or Plant Located In Areas Of Water Stress Domain1 - Previous Year} - {Water Discharge To Seawater With Treatment Per Area - Facility Or Plant Located In Areas Of Water Stress Domain1 - Previous Year}",
    "Water Discharge To Seawater With Treatment Per Area - Facility Or Plant Located In Areas Of Water Stress Domain1 - Previous Year":
        "{Water Discharge To Seawater Per Area - Facility Or Plant Located In Areas Of Water Stress Domain1 - Previous Year} - {Water Discharge To Seawater With Out Treatment Per Area - Facility Or Plant Located In Areas Of Water Stress Domain1 - Previous Year}",
    "Water Discharge By Sent To Third Parties Per Area - Facility Or Plant Located In Areas Of Water Stress Domain1 - Previous Year":
        "{Total Water Discharged In Kilolitres Per Area - Facility Or Plant Located In Areas Of Water Stress Domain1 - Previous Year} - {Water Discharge To Surface Water Per Area - Facility Or Plant Located In Areas Of Water Stress Domain1 - Previous Year} - {Water Discharge To Groundwater Per Area - Facility Or Plant Located In Areas Of Water Stress Domain1 - Previous Year} - {Water Discharge To Seawater Per Area - Facility Or Plant Located In Areas Of Water Stress Domain1 - Previous Year} - {Water Discharge To Others Per Area - Facility Or Plant Located In Areas Of Water Stress Domain1 - Previous Year}",
    "Water Discharge By Sent To Third Parties Without Treatment Per Area - Facility Or Plant Located In Areas Of Water Stress Domain1 - Previous Year": "0",
    "Water Discharge By Sent To Third Parties With Treatment Per Area - Facility Or Plant Located In Areas Of Water Stress Domain1 - Previous Year": "0",
    "Water Discharge To Others Per Area - Facility Or Plant Located In Areas Of Water Stress Domain1 - Previous Year":
        "{Total Water Discharged In Kilolitres Per Area - Facility Or Plant Located In Areas Of Water Stress Domain1 - Previous Year} - {Water Discharge To Surface Water Per Area - Facility Or Plant Located In Areas Of Water Stress Domain1 - Previous Year} - {Water Discharge To Groundwater Per Area - Facility Or Plant Located In Areas Of Water Stress Domain1 - Previous Year} - {Water Discharge To Seawater Per Area - Facility Or Plant Located In Areas Of Water Stress Domain1 - Previous Year} - {Water Discharge By Sent To Third Parties Per Area - Facility Or Plant Located In Areas Of Water Stress Domain1 - Previous Year}",
    "Water Discharge To Others Without Treatment Per Area - Facility Or Plant Located In Areas Of Water Stress Domain1 - Previous Year": "0",
    "Water Discharge To Others With Treatment Per Area - Facility Or Plant Located In Areas Of Water Stress Domain1 - Previous Year": "0",
    "Total Water Discharged In Kilolitres Per Area - Facility Or Plant Located In Areas Of Water Stress Domain1 - Previous Year": "0",
    "Energy Intensity The Relevant Metric May Be Selected By The Entity": "0",
    "Energy Intensity The Relevant Metric May Be Selected By The Entity - Previous Year": "0",
    "Energy Consumption Through Other Sources From Non Renewable Sources - Energy Consumption Through Other Source From Non Renewable Sources Domain2 - Previous Year": "0",
    "Recycled Or Re Used In Put Material To Total Material - Recycled Or Reused Input Material Used In Production Or Providing Services Domain2 - Previous Year": "0",
    "Whether The Company Has Undertaken Reasonable Assurance Of The BRSRCore": "0",
    "Number Of Female Employees Or Workers": "0",
    "Number Of Female Employees Or Workers - Previous Year": "0",
    "Water Withdrawal By Surface Water Per Area - Facility Or Plant Located In Areas Of Water Stress Domain2 - Previous Year": "0",
    "Water Withdrawal By Groundwater Per Area - Facility Or Plant Located In Areas Of Water Stress Domain2 - Previous Year": "0",
    "Water Withdrawal By Third Party Water Per Area - Facility Or Plant Located In Areas Of Water Stress Domain2 - Previous Year": "0",
    "Water Withdrawal By Seawater Or Desalinated Water Per Area - Facility Or Plant Located In Areas Of Water Stress Domain2 - Previous Year": "0",
    "Water Withdrawal By Others Per Area - Facility Or Plant Located In Areas Of Water Stress Domain2 - Previous Year": "0",
    "Total Volume Of Water Withdrawal Per Area - Facility Or Plant Located In Areas Of Water Stress Domain2 - Previous Year": "0",
    "Total Volume Of Water Consumption Per Area - Facility Or Plant Located In Areas Of Water Stress Domain2 - Previous Year": "0",
    "Water Intensity Per Rupee Of Turnover Per Area - Facility Or Plant Located In Areas Of Water Stress Domain2 - Previous Year": "0",
    "Waste Intensity The Relevant Metric May Be Selected By The Entity Per Area - Facility Or Plant Located In Areas Of Water Stress Domain2 - Previous Year":
        "{Total Waste Generated} / {Revenue From Operations}",
    "Water Discharge To Surface Water Per Area - Facility Or Plant Located In Areas Of Water Stress Domain2 - Previous Year":
        "{Total Water Discharged In Kilolitres Per Area - Facility Or Plant Located In Areas Of Water Stress Domain2 - Previous Year} - {Water Discharge To Groundwater Per Area - Facility Or Plant Located In Areas Of Water Stress Domain2 - Previous Year} - {Water Discharge To Seawater Per Area - Facility Or Plant Located In Areas Of Water Stress Domain2 - Previous Year} - {Water Discharge By Sent To Third Parties Per Area - Facility Or Plant Located In Areas Of Water Stress Domain2 - Previous Year} - {Water Discharge To Others Per Area - Facility Or Plant Located In Areas Of Water Stress Domain2 - Previous Year}",
    "Water Discharge To Surface Water With Out Treatment Per Area - Facility Or Plant Located In Areas Of Water Stress Domain2 - Previous Year":
        "{Water Discharge To Surface Water Per Area - Facility Or Plant Located In Areas Of Water Stress Domain2 - Previous Year} - {Water Discharge To Surface Water With Treatment Per Area - Facility Or Plant Located In Areas Of Water Stress Domain2 - Previous Year}",
    "Water Discharge To Surface Water With Treatment Per Area - Facility Or Plant Located In Areas Of Water Stress Domain2 - Previous Year":
        "{Water Discharge To Surface Water Per Area - Facility Or Plant Located In Areas Of Water Stress Domain2 - Previous Year} - {Water Discharge To Surface Water With Out Treatment Per Area - Facility Or Plant Located In Areas Of Water Stress Domain2 - Previous Year}",
    "Water Discharge To Groundwater Per Area - Facility Or Plant Located In Areas Of Water Stress Domain2 - Previous Year":
        "{Total Water Discharged In Kilolitres Per Area - Facility Or Plant Located In Areas Of Water Stress Domain2 - Previous Year} - {Water Discharge To Surface Water Per Area - Facility Or Plant Located In Areas Of Water Stress Domain2 - Previous Year} - {Water Discharge To Seawater Per Area - Facility Or Plant Located In Areas Of Water Stress Domain2 - Previous Year} - {Water Discharge By Sent To Third Parties Per Area - Facility Or Plant Located In Areas Of Water Stress Domain2 - Previous Year} - {Water Discharge To Others Per Area - Facility Or Plant Located In Areas Of Water Stress Domain2 - Previous Year}",
    "Water Discharge To Groundwater With Out Treatment Per Area - Facility Or Plant Located In Areas Of Water Stress Domain2 - Previous Year":
        "{Water Discharge To Groundwater Per Area - Facility Or Plant Located In Areas Of Water Stress Domain2 - Previous Year} - {Water Discharge To Groundwater With Treatment Per Area - Facility Or Plant Located In Areas Of Water Stress Domain2 - Previous Year}",
    "Water Discharge To Groundwater With Treatment Per Area - Facility Or Plant Located In Areas Of Water Stress Domain2 - Previous Year":
        "{Water Discharge To Groundwater Per Area - Facility Or Plant Located In Areas Of Water Stress Domain2 - Previous Year} - {Water Discharge To Groundwater With Out Treatment Per Area - Facility Or Plant Located In Areas Of Water Stress Domain2 - Previous Year}",
    "Water Discharge To Seawater Per Area - Facility Or Plant Located In Areas Of Water Stress Domain2 - Previous Year":
        "{Total Water Discharged In Kilolitres Per Area - Facility Or Plant Located In Areas Of Water Stress Domain2 - Previous Year} - {Water Discharge To Surface Water Per Area - Facility Or Plant Located In Areas Of Water Stress Domain2 - Previous Year} - {Water Discharge To Groundwater Per Area - Facility Or Plant Located In Areas Of Water Stress Domain2 - Previous Year} - {Water Discharge By Sent To Third Parties Per Area - Facility Or Plant Located In Areas Of Water Stress Domain2 - Previous Year} - {Water Discharge To Others Per Area - Facility Or Plant Located In Areas Of Water Stress Domain2 - Previous Year}",
    "Water Discharge To Seawater With Out Treatment Per Area - Facility Or Plant Located In Areas Of Water Stress Domain2 - Previous Year":
        "{Water Discharge To Seawater Per Area - Facility Or Plant Located In Areas Of Water Stress Domain2 - Previous Year} - {Water Discharge To Seawater With Treatment Per Area - Facility Or Plant Located In Areas Of Water Stress Domain2 - Previous Year}",
    "Water Discharge To Seawater With Treatment Per Area - Facility Or Plant Located In Areas Of Water Stress Domain2 - Previous Year":
        "{Water Discharge To Seawater Per Area - Facility Or Plant Located In Areas Of Water Stress Domain2 - Previous Year} - {Water Discharge To Seawater With Out Treatment Per Area - Facility Or Plant Located In Areas Of Water Stress Domain2 - Previous Year}",
    "Water Discharge By Sent To Third Parties Per Area - Facility Or Plant Located In Areas Of Water Stress Domain2 - Previous Year":
        "{Total Water Discharged In Kilolitres Per Area - Facility Or Plant Located In Areas Of Water Stress Domain2 - Previous Year} - {Water Discharge To Surface Water Per Area - Facility Or Plant Located In Areas Of Water Stress Domain2 - Previous Year} - {Water Discharge To Groundwater Per Area - Facility Or Plant Located In Areas Of Water Stress Domain2 - Previous Year} - {Water Discharge To Seawater Per Area - Facility Or Plant Located In Areas Of Water Stress Domain2 - Previous Year} - {Water Discharge To Others Per Area - Facility Or Plant Located In Areas Of Water Stress Domain2 - Previous Year}",
    "Water Discharge By Sent To Third Parties Without Treatment Per Area - Facility Or Plant Located In Areas Of Water Stress Domain2 - Previous Year": "0",
    "Water Discharge By Sent To Third Parties With Treatment Per Area - Facility Or Plant Located In Areas Of Water Stress Domain2 - Previous Year": "0",
    "Water Discharge To Others Per Area - Facility Or Plant Located In Areas Of Water Stress Domain2 - Previous Year":
        "{Total Water Discharged In Kilolitres Per Area - Facility Or Plant Located In Areas Of Water Stress Domain2 - Previous Year} - {Water Discharge To Surface Water Per Area - Facility Or Plant Located In Areas Of Water Stress Domain2 - Previous Year} - {Water Discharge To Groundwater Per Area - Facility Or Plant Located In Areas Of Water Stress Domain2 - Previous Year} - {Water Discharge To Seawater Per Area - Facility Or Plant Located In Areas Of Water Stress Domain2 - Previous Year} - {Water Discharge By Sent To Third Parties Per Area - Facility Or Plant Located In Areas Of Water Stress Domain2 - Previous Year}",
    "Water Discharge To Others Without Treatment Per Area - Facility Or Plant Located In Areas Of Water Stress Domain2 - Previous Year": "0",
    "Water Discharge To Others With Treatment Per Area - Facility Or Plant Located In Areas Of Water Stress Domain2 - Previous Year": "0",
    "Total Water Discharged In Kilolitres Per Area - Facility Or Plant Located In Areas Of Water Stress Domain2 - Previous Year": "0",
    "Water Withdrawal By Surface Water Per Area - Facility Or Plant Located In Areas Of Water Stress Domain3 - Previous Year": "0",
    "Water Withdrawal By Groundwater Per Area - Facility Or Plant Located In Areas Of Water Stress Domain3 - Previous Year": "0",
    "Water Withdrawal By Third Party Water Per Area - Facility Or Plant Located In Areas Of Water Stress Domain3 - Previous Year": "0",
    "Water Withdrawal By Seawater Or Desalinated Water Per Area - Facility Or Plant Located In Areas Of Water Stress Domain3 - Previous Year": "0",
    "Water Withdrawal By Others Per Area - Facility Or Plant Located In Areas Of Water Stress Domain3 - Previous Year": "0",
    "Total Volume Of Water Withdrawal Per Area - Facility Or Plant Located In Areas Of Water Stress Domain3 - Previous Year": "0",
    "Total Volume Of Water Consumption Per Area - Facility Or Plant Located In Areas Of Water Stress Domain3 - Previous Year": "0",
    "Water Intensity Per Rupee Of Turnover Per Area - Facility Or Plant Located In Areas Of Water Stress Domain3 - Previous Year": "0",
    "Waste Intensity The Relevant Metric May Be Selected By The Entity Per Area - Facility Or Plant Located In Areas Of Water Stress Domain3 - Previous Year":
        "{Total Waste Generated} / {Revenue From Operations}",
    "Water Discharge To Surface Water Per Area - Facility Or Plant Located In Areas Of Water Stress Domain3 - Previous Year":
        "{Total Water Discharged In Kilolitres Per Area - Facility Or Plant Located In Areas Of Water Stress Domain3 - Previous Year} - {Water Discharge To Groundwater Per Area - Facility Or Plant Located In Areas Of Water Stress Domain3 - Previous Year} - {Water Discharge To Seawater Per Area - Facility Or Plant Located In Areas Of Water Stress Domain3 - Previous Year} - {Water Discharge By Sent To Third Parties Per Area - Facility Or Plant Located In Areas Of Water Stress Domain3 - Previous Year} - {Water Discharge To Others Per Area - Facility Or Plant Located In Areas Of Water Stress Domain3 - Previous Year}",
    "Water Discharge To Surface Water With Out Treatment Per Area - Facility Or Plant Located In Areas Of Water Stress Domain3 - Previous Year":
        "{Water Discharge To Surface Water Per Area - Facility Or Plant Located In Areas Of Water Stress Domain3 - Previous Year} - {Water Discharge To Surface Water With Treatment Per Area - Facility Or Plant Located In Areas Of Water Stress Domain3 - Previous Year}",
    "Water Discharge To Surface Water With Treatment Per Area - Facility Or Plant Located In Areas Of Water Stress Domain3 - Previous Year":
        "{Water Discharge To Surface Water Per Area - Facility Or Plant Located In Areas Of Water Stress Domain3 - Previous Year} - {Water Discharge To Surface Water With Out Treatment Per Area - Facility Or Plant Located In Areas Of Water Stress Domain3 - Previous Year}",
    "Water Discharge To Groundwater Per Area - Facility Or Plant Located In Areas Of Water Stress Domain3 - Previous Year":
        "{Total Water Discharged In Kilolitres Per Area - Facility Or Plant Located In Areas Of Water Stress Domain3 - Previous Year} - {Water Discharge To Surface Water Per Area - Facility Or Plant Located In Areas Of Water Stress Domain3 - Previous Year} - {Water Discharge To Seawater Per Area - Facility Or Plant Located In Areas Of Water Stress Domain3 - Previous Year} - {Water Discharge By Sent To Third Parties Per Area - Facility Or Plant Located In Areas Of Water Stress Domain3 - Previous Year} - {Water Discharge To Others Per Area - Facility Or Plant Located In Areas Of Water Stress Domain3 - Previous Year}",
    "Water Discharge To Groundwater With Out Treatment Per Area - Facility Or Plant Located In Areas Of Water Stress Domain3 - Previous Year":
        "{Water Discharge To Groundwater Per Area - Facility Or Plant Located In Areas Of Water Stress Domain3 - Previous Year} - {Water Discharge To Groundwater With Treatment Per Area - Facility Or Plant Located In Areas Of Water Stress Domain3 - Previous Year}",
    "Water Discharge To Groundwater With Treatment Per Area - Facility Or Plant Located In Areas Of Water Stress Domain3 - Previous Year":
        "{Water Discharge To Groundwater Per Area - Facility Or Plant Located In Areas Of Water Stress Domain3 - Previous Year} - {Water Discharge To Groundwater With Out Treatment Per Area - Facility Or Plant Located In Areas Of Water Stress Domain3 - Previous Year}",
    "Water Discharge To Seawater Per Area - Facility Or Plant Located In Areas Of Water Stress Domain3 - Previous Year":
        "{Total Water Discharged In Kilolitres Per Area - Facility Or Plant Located In Areas Of Water Stress Domain3 - Previous Year} - {Water Discharge To Surface Water Per Area - Facility Or Plant Located In Areas Of Water Stress Domain3 - Previous Year} - {Water Discharge To Groundwater Per Area - Facility Or Plant Located In Areas Of Water Stress Domain3 - Previous Year} - {Water Discharge By Sent To Third Parties Per Area - Facility Or Plant Located In Areas Of Water Stress Domain3 - Previous Year} - {Water Discharge To Others Per Area - Facility Or Plant Located In Areas Of Water Stress Domain3 - Previous Year}",
    "Water Discharge To Seawater With Out Treatment Per Area - Facility Or Plant Located In Areas Of Water Stress Domain3 - Previous Year":
        "{Water Discharge To Seawater Per Area - Facility Or Plant Located In Areas Of Water Stress Domain3 - Previous Year} - {Water Discharge To Seawater With Treatment Per Area - Facility Or Plant Located In Areas Of Water Stress Domain3 - Previous Year}",
    "Water Discharge To Seawater With Treatment Per Area - Facility Or Plant Located In Areas Of Water Stress Domain3 - Previous Year":
        "{Water Discharge To Seawater Per Area - Facility Or Plant Located In Areas Of Water Stress Domain3 - Previous Year} - {Water Discharge To Seawater With Out Treatment Per Area - Facility Or Plant Located In Areas Of Water Stress Domain3 - Previous Year}",
    "Water Discharge By Sent To Third Parties Per Area - Facility Or Plant Located In Areas Of Water Stress Domain3 - Previous Year":
        "{Total Water Discharged In Kilolitres Per Area - Facility Or Plant Located In Areas Of Water Stress Domain3 - Previous Year} - {Water Discharge To Surface Water Per Area - Facility Or Plant Located In Areas Of Water Stress Domain3 - Previous Year} - {Water Discharge To Groundwater Per Area - Facility Or Plant Located In Areas Of Water Stress Domain3 - Previous Year} - {Water Discharge To Seawater Per Area - Facility Or Plant Located In Areas Of Water Stress Domain3 - Previous Year} - {Water Discharge To Others Per Area - Facility Or Plant Located In Areas Of Water Stress Domain3 - Previous Year}",
    "Water Discharge By Sent To Third Parties Without Treatment Per Area - Facility Or Plant Located In Areas Of Water Stress Domain3 - Previous Year": "0",
    "Water Discharge By Sent To Third Parties With Treatment Per Area - Facility Or Plant Located In Areas Of Water Stress Domain3 - Previous Year": "0",
    "Water Discharge To Others Per Area - Facility Or Plant Located In Areas Of Water Stress Domain3 - Previous Year":
        "{Total Water Discharged In Kilolitres Per Area - Facility Or Plant Located In Areas Of Water Stress Domain3 - Previous Year} - {Water Discharge To Surface Water Per Area - Facility Or Plant Located In Areas Of Water Stress Domain3 - Previous Year} - {Water Discharge To Groundwater Per Area - Facility Or Plant Located In Areas Of Water Stress Domain3 - Previous Year} - {Water Discharge To Seawater Per Area - Facility Or Plant Located In Areas Of Water Stress Domain3 - Previous Year} - {Water Discharge By Sent To Third Parties Per Area - Facility Or Plant Located In Areas Of Water Stress Domain3 - Previous Year}",
    "Water Discharge To Others Without Treatment Per Area - Facility Or Plant Located In Areas Of Water Stress Domain3 - Previous Year": "0",
    "Water Discharge To Others With Treatment Per Area - Facility Or Plant Located In Areas Of Water Stress Domain3 - Previous Year": "0",
    "Total Water Discharged In Kilolitres Per Area - Facility Or Plant Located In Areas Of Water Stress Domain3 - Previous Year": "0",
    "Water Withdrawal By Surface Water Per Area - Facility Or Plant Located In Areas Of Water Stress Domain4 - Previous Year": "0",
    "Water Withdrawal By Groundwater Per Area - Facility Or Plant Located In Areas Of Water Stress Domain4 - Previous Year": "0",
    "Water Withdrawal By Third Party Water Per Area - Facility Or Plant Located In Areas Of Water Stress Domain4 - Previous Year": "0",
    "Water Withdrawal By Seawater Or Desalinated Water Per Area - Facility Or Plant Located In Areas Of Water Stress Domain4 - Previous Year": "0",
    "Water Withdrawal By Others Per Area - Facility Or Plant Located In Areas Of Water Stress Domain4 - Previous Year": "0",
    "Total Volume Of Water Withdrawal Per Area - Facility Or Plant Located In Areas Of Water Stress Domain4 - Previous Year": "0",
    "Total Volume Of Water Consumption Per Area - Facility Or Plant Located In Areas Of Water Stress Domain4 - Previous Year": "0",
    "Water Intensity Per Rupee Of Turnover Per Area - Facility Or Plant Located In Areas Of Water Stress Domain4 - Previous Year": "0",
    "Waste Intensity The Relevant Metric May Be Selected By The Entity Per Area - Facility Or Plant Located In Areas Of Water Stress Domain4 - Previous Year":
        "{Total Waste Generated} / {Revenue From Operations}",
    "Water Discharge To Surface Water Per Area - Facility Or Plant Located In Areas Of Water Stress Domain4 - Previous Year":
        "{Total Water Discharged In Kilolitres Per Area - Facility Or Plant Located In Areas Of Water Stress Domain4 - Previous Year} - {Water Discharge To Groundwater Per Area - Facility Or Plant Located In Areas Of Water Stress Domain4 - Previous Year} - {Water Discharge To Seawater Per Area - Facility Or Plant Located In Areas Of Water Stress Domain4 - Previous Year} - {Water Discharge By Sent To Third Parties Per Area - Facility Or Plant Located In Areas Of Water Stress Domain4 - Previous Year} - {Water Discharge To Others Per Area - Facility Or Plant Located In Areas Of Water Stress Domain4 - Previous Year}",
    "Water Discharge To Surface Water With Out Treatment Per Area - Facility Or Plant Located In Areas Of Water Stress Domain4 - Previous Year":
        "{Water Discharge To Surface Water Per Area - Facility Or Plant Located In Areas Of Water Stress Domain4 - Previous Year} - {Water Discharge To Surface Water With Treatment Per Area - Facility Or Plant Located In Areas Of Water Stress Domain4 - Previous Year}",
    "Water Discharge To Surface Water With Treatment Per Area - Facility Or Plant Located In Areas Of Water Stress Domain4 - Previous Year":
        "{Water Discharge To Surface Water Per Area - Facility Or Plant Located In Areas Of Water Stress Domain4 - Previous Year} - {Water Discharge To Surface Water With Out Treatment Per Area - Facility Or Plant Located In Areas Of Water Stress Domain4 - Previous Year}",
    "Water Discharge To Groundwater Per Area - Facility Or Plant Located In Areas Of Water Stress Domain4 - Previous Year":
        "{Total Water Discharged In Kilolitres Per Area - Facility Or Plant Located In Areas Of Water Stress Domain4 - Previous Year} - {Water Discharge To Surface Water Per Area - Facility Or Plant Located In Areas Of Water Stress Domain4 - Previous Year} - {Water Discharge To Seawater Per Area - Facility Or Plant Located In Areas Of Water Stress Domain4 - Previous Year} - {Water Discharge By Sent To Third Parties Per Area - Facility Or Plant Located In Areas Of Water Stress Domain4 - Previous Year} - {Water Discharge To Others Per Area - Facility Or Plant Located In Areas Of Water Stress Domain4 - Previous Year}",
    "Water Discharge To Groundwater With Out Treatment Per Area - Facility Or Plant Located In Areas Of Water Stress Domain4 - Previous Year":
        "{Water Discharge To Groundwater Per Area - Facility Or Plant Located In Areas Of Water Stress Domain4 - Previous Year} - {Water Discharge To Groundwater With Treatment Per Area - Facility Or Plant Located In Areas Of Water Stress Domain4 - Previous Year}",
    "Water Discharge To Groundwater With Treatment Per Area - Facility Or Plant Located In Areas Of Water Stress Domain4 - Previous Year":
        "{Water Discharge To Groundwater Per Area - Facility Or Plant Located In Areas Of Water Stress Domain4 - Previous Year} - {Water Discharge To Groundwater With Out Treatment Per Area - Facility Or Plant Located In Areas Of Water Stress Domain4 - Previous Year}",
    "Water Discharge To Seawater Per Area - Facility Or Plant Located In Areas Of Water Stress Domain4 - Previous Year":
        "{Total Water Discharged In Kilolitres Per Area - Facility Or Plant Located In Areas Of Water Stress Domain4 - Previous Year} - {Water Discharge To Surface Water Per Area - Facility Or Plant Located In Areas Of Water Stress Domain4 - Previous Year} - {Water Discharge To Groundwater Per Area - Facility Or Plant Located In Areas Of Water Stress Domain4 - Previous Year} - {Water Discharge By Sent To Third Parties Per Area - Facility Or Plant Located In Areas Of Water Stress Domain4 - Previous Year} - {Water Discharge To Others Per Area - Facility Or Plant Located In Areas Of Water Stress Domain4 - Previous Year}",
    "Water Discharge To Seawater With Out Treatment Per Area - Facility Or Plant Located In Areas Of Water Stress Domain4 - Previous Year":
        "{Water Discharge To Seawater Per Area - Facility Or Plant Located In Areas Of Water Stress Domain4 - Previous Year} - {Water Discharge To Seawater With Treatment Per Area - Facility Or Plant Located In Areas Of Water Stress Domain4 - Previous Year}",
    "Water Discharge To Seawater With Treatment Per Area - Facility Or Plant Located In Areas Of Water Stress Domain4 - Previous Year":
        "{Water Discharge To Seawater Per Area - Facility Or Plant Located In Areas Of Water Stress Domain4 - Previous Year} - {Water Discharge To Seawater With Out Treatment Per Area - Facility Or Plant Located In Areas Of Water Stress Domain4 - Previous Year}",
    "Water Discharge By Sent To Third Parties Per Area - Facility Or Plant Located In Areas Of Water Stress Domain4 - Previous Year":
        "{Total Water Discharged In Kilolitres Per Area - Facility Or Plant Located In Areas Of Water Stress Domain4 - Previous Year} - {Water Discharge To Surface Water Per Area - Facility Or Plant Located In Areas Of Water Stress Domain4 - Previous Year} - {Water Discharge To Groundwater Per Area - Facility Or Plant Located In Areas Of Water Stress Domain4 - Previous Year} - {Water Discharge To Seawater Per Area - Facility Or Plant Located In Areas Of Water Stress Domain4 - Previous Year} - {Water Discharge To Others Per Area - Facility Or Plant Located In Areas Of Water Stress Domain4 - Previous Year}",
    "Water Discharge By Sent To Third Parties Without Treatment Per Area - Facility Or Plant Located In Areas Of Water Stress Domain4 - Previous Year": "0",
    "Water Discharge By Sent To Third Parties With Treatment Per Area - Facility Or Plant Located In Areas Of Water Stress Domain4 - Previous Year": "0",
    "Water Discharge To Others Per Area - Facility Or Plant Located In Areas Of Water Stress Domain4 - Previous Year":
        "{Total Water Discharged In Kilolitres Per Area - Facility Or Plant Located In Areas Of Water Stress Domain4 - Previous Year} - {Water Discharge To Surface Water Per Area - Facility Or Plant Located In Areas Of Water Stress Domain4 - Previous Year} - {Water Discharge To Groundwater Per Area - Facility Or Plant Located In Areas Of Water Stress Domain4 - Previous Year} - {Water Discharge To Seawater Per Area - Facility Or Plant Located In Areas Of Water Stress Domain4 - Previous Year} - {Water Discharge By Sent To Third Parties Per Area - Facility Or Plant Located In Areas Of Water Stress Domain4 - Previous Year}",
    "Water Discharge To Others Without Treatment Per Area - Facility Or Plant Located In Areas Of Water Stress Domain4 - Previous Year": "0",
    "Water Discharge To Others With Treatment Per Area - Facility Or Plant Located In Areas Of Water Stress Domain4 - Previous Year": "0",
    "Total Water Discharged In Kilolitres Per Area - Facility Or Plant Located In Areas Of Water Stress Domain4 - Previous Year": "0",
    "Water Withdrawal By Surface Water Per Area - Facility Or Plant Located In Areas Of Water Stress Domain5 - Previous Year": "0",
    "Water Withdrawal By Groundwater Per Area - Facility Or Plant Located In Areas Of Water Stress Domain5 - Previous Year": "0",
    "Water Withdrawal By Third Party Water Per Area - Facility Or Plant Located In Areas Of Water Stress Domain5 - Previous Year": "0",
    "Water Withdrawal By Seawater Or Desalinated Water Per Area - Facility Or Plant Located In Areas Of Water Stress Domain5 - Previous Year": "0",
    "Water Withdrawal By Others Per Area - Facility Or Plant Located In Areas Of Water Stress Domain5 - Previous Year": "0",
    "Total Volume Of Water Withdrawal Per Area - Facility Or Plant Located In Areas Of Water Stress Domain5 - Previous Year": "0",
    "Total Volume Of Water Consumption Per Area - Facility Or Plant Located In Areas Of Water Stress Domain5 - Previous Year": "0",
    "Water Intensity Per Rupee Of Turnover Per Area - Facility Or Plant Located In Areas Of Water Stress Domain5 - Previous Year": "0",
    "Waste Intensity The Relevant Metric May Be Selected By The Entity Per Area - Facility Or Plant Located In Areas Of Water Stress Domain5 - Previous Year":
        "{Total Waste Generated} / {Revenue From Operations}",
    "Water Discharge To Surface Water Per Area - Facility Or Plant Located In Areas Of Water Stress Domain5 - Previous Year":
        "{Total Water Discharged In Kilolitres Per Area - Facility Or Plant Located In Areas Of Water Stress Domain5 - Previous Year} - {Water Discharge To Groundwater Per Area - Facility Or Plant Located In Areas Of Water Stress Domain5 - Previous Year} - {Water Discharge To Seawater Per Area - Facility Or Plant Located In Areas Of Water Stress Domain5 - Previous Year} - {Water Discharge By Sent To Third Parties Per Area - Facility Or Plant Located In Areas Of Water Stress Domain5 - Previous Year} - {Water Discharge To Others Per Area - Facility Or Plant Located In Areas Of Water Stress Domain5 - Previous Year}",
    "Water Discharge To Surface Water With Out Treatment Per Area - Facility Or Plant Located In Areas Of Water Stress Domain5 - Previous Year":
        "{Water Discharge To Surface Water Per Area - Facility Or Plant Located In Areas Of Water Stress Domain5 - Previous Year} - {Water Discharge To Surface Water With Treatment Per Area - Facility Or Plant Located In Areas Of Water Stress Domain5 - Previous Year}",
    "Water Discharge To Surface Water With Treatment Per Area - Facility Or Plant Located In Areas Of Water Stress Domain5 - Previous Year":
        "{Water Discharge To Surface Water Per Area - Facility Or Plant Located In Areas Of Water Stress Domain5 - Previous Year} - {Water Discharge To Surface Water With Out Treatment Per Area - Facility Or Plant Located In Areas Of Water Stress Domain5 - Previous Year}",
    "Water Discharge To Groundwater Per Area - Facility Or Plant Located In Areas Of Water Stress Domain5 - Previous Year":
        "{Total Water Discharged In Kilolitres Per Area - Facility Or Plant Located In Areas Of Water Stress Domain5 - Previous Year} - {Water Discharge To Surface Water Per Area - Facility Or Plant Located In Areas Of Water Stress Domain5 - Previous Year} - {Water Discharge To Seawater Per Area - Facility Or Plant Located In Areas Of Water Stress Domain5 - Previous Year} - {Water Discharge By Sent To Third Parties Per Area - Facility Or Plant Located In Areas Of Water Stress Domain5 - Previous Year} - {Water Discharge To Others Per Area - Facility Or Plant Located In Areas Of Water Stress Domain5 - Previous Year}",
    "Water Discharge To Groundwater With Out Treatment Per Area - Facility Or Plant Located In Areas Of Water Stress Domain5 - Previous Year":
        "{Water Discharge To Groundwater Per Area - Facility Or Plant Located In Areas Of Water Stress Domain5 - Previous Year} - {Water Discharge To Groundwater With Treatment Per Area - Facility Or Plant Located In Areas Of Water Stress Domain5 - Previous Year}",
    "Water Discharge To Groundwater With Treatment Per Area - Facility Or Plant Located In Areas Of Water Stress Domain5 - Previous Year":
        "{Water Discharge To Groundwater Per Area - Facility Or Plant Located In Areas Of Water Stress Domain5 - Previous Year} - {Water Discharge To Groundwater With Out Treatment Per Area - Facility Or Plant Located In Areas Of Water Stress Domain5 - Previous Year}",
    "Water Discharge To Seawater Per Area - Facility Or Plant Located In Areas Of Water Stress Domain5 - Previous Year":
        "{Total Water Discharged In Kilolitres Per Area - Facility Or Plant Located In Areas Of Water Stress Domain5 - Previous Year} - {Water Discharge To Surface Water Per Area - Facility Or Plant Located In Areas Of Water Stress Domain5 - Previous Year} - {Water Discharge To Groundwater Per Area - Facility Or Plant Located In Areas Of Water Stress Domain5 - Previous Year} - {Water Discharge By Sent To Third Parties Per Area - Facility Or Plant Located In Areas Of Water Stress Domain5 - Previous Year} - {Water Discharge To Others Per Area - Facility Or Plant Located In Areas Of Water Stress Domain5 - Previous Year}",
    "Water Discharge To Seawater With Out Treatment Per Area - Facility Or Plant Located In Areas Of Water Stress Domain5 - Previous Year":
        "{Water Discharge To Seawater Per Area - Facility Or Plant Located In Areas Of Water Stress Domain5 - Previous Year} - {Water Discharge To Seawater With Treatment Per Area - Facility Or Plant Located In Areas Of Water Stress Domain5 - Previous Year}",
    "Water Discharge To Seawater With Treatment Per Area - Facility Or Plant Located In Areas Of Water Stress Domain5 - Previous Year":
        "{Water Discharge To Seawater Per Area - Facility Or Plant Located In Areas Of Water Stress Domain5 - Previous Year} - {Water Discharge To Seawater With Out Treatment Per Area - Facility Or Plant Located In Areas Of Water Stress Domain5 - Previous Year}",
    "Water Discharge By Sent To Third Parties Per Area - Facility Or Plant Located In Areas Of Water Stress Domain5 - Previous Year":
        "{Total Water Discharged In Kilolitres Per Area - Facility Or Plant Located In Areas Of Water Stress Domain5 - Previous Year} - {Water Discharge To Surface Water Per Area - Facility Or Plant Located In Areas Of Water Stress Domain5 - Previous Year} - {Water Discharge To Groundwater Per Area - Facility Or Plant Located In Areas Of Water Stress Domain5 - Previous Year} - {Water Discharge To Seawater Per Area - Facility Or Plant Located In Areas Of Water Stress Domain5 - Previous Year} - {Water Discharge To Others Per Area - Facility Or Plant Located In Areas Of Water Stress Domain5 - Previous Year}",
    "Water Discharge By Sent To Third Parties Without Treatment Per Area - Facility Or Plant Located In Areas Of Water Stress Domain5 - Previous Year": "0",
    "Water Discharge By Sent To Third Parties With Treatment Per Area - Facility Or Plant Located In Areas Of Water Stress Domain5 - Previous Year": "0",
    "Water Discharge To Others Per Area - Facility Or Plant Located In Areas Of Water Stress Domain5 - Previous Year":
        "{Total Water Discharged In Kilolitres Per Area - Facility Or Plant Located In Areas Of Water Stress Domain5 - Previous Year} - {Water Discharge To Surface Water Per Area - Facility Or Plant Located In Areas Of Water Stress Domain5 - Previous Year} - {Water Discharge To Groundwater Per Area - Facility Or Plant Located In Areas Of Water Stress Domain5 - Previous Year} - {Water Discharge To Seawater Per Area - Facility Or Plant Located In Areas Of Water Stress Domain5 - Previous Year} - {Water Discharge By Sent To Third Parties Per Area - Facility Or Plant Located In Areas Of Water Stress Domain5 - Previous Year}",
    "Water Discharge To Others Without Treatment Per Area - Facility Or Plant Located In Areas Of Water Stress Domain5 - Previous Year": "0",
    "Water Discharge To Others With Treatment Per Area - Facility Or Plant Located In Areas Of Water Stress Domain5 - Previous Year": "0",
    "Total Water Discharged In Kilolitres Per Area - Facility Or Plant Located In Areas Of Water Stress Domain5 - Previous Year": "0",
    "Number Of Employees Covered As Percentage Of Total Employees - Other Retirement Benefits Domain2 - Previous Year": "0",
    "Number Of Employees Covered As Percentage Of Total Worker - Other Retirement Benefits Domain2 - Previous Year": "0",
    "Number Of Employees Covered As Percentage Of Total Employees - Other Retirement Benefits Domain3 - Previous Year": "0",
    "Number Of Employees Covered As Percentage Of Total Worker - Other Retirement Benefits Domain3 - Previous Year": "0",
    "Number Of Employees Covered As Percentage Of Total Employees - Other Retirement Benefits Domain4 - Previous Year": "0",
    "Number Of Employees Covered As Percentage Of Total Worker - Other Retirement Benefits Domain4 - Previous Year": "0",
    "Number Of Complaints Filed From Stake Holder Group During The Year - Other Stake Holder Domain2 - Previous Year": "0",
    "Number Of Complaints Pending From Stake Holder Group Resolution At The End Of Year - Other Stake Holder Domain2 - Previous Year": "0",
    "Number Of Complaints Filed From Stake Holder Group During The Year - Other Stake Holder Domain3 - Previous Year": "0",
    "Number Of Complaints Pending From Stake Holder Group Resolution At The End Of Year - Other Stake Holder Domain3 - Previous Year": "0",
    "Energy Consumption Through Other Sources From Renewable Sources - Energy Consumption Through Other Source From Renewable Sources Domain2 - Previous Year": "0",
    "Recycled Or Re Used In Put Material To Total Material - Recycled Or Reused Input Material Used In Production Or Providing Services Domain3 - Previous Year": "0",
    "Amount Of Re Used - Other Waste Domain2 - Previous Year": "0",
    "Amount Of Recycled - Other Waste Domain2 - Previous Year": "0",
    "Amount Of Safely Disposed - Other Waste Domain2 - Previous Year": "0",
    "Amount Of Re Used - Other Waste Domain3 - Previous Year": "0",
    "Amount Of Recycled - Other Waste Domain3 - Previous Year": "0",
    "Amount Of Safely Disposed - Other Waste Domain3 - Previous Year": "0",
    "Amount Of Re Used - Other Waste Domain4 - Previous Year": "0",
    "Amount Of Recycled - Other Waste Domain4 - Previous Year": "0",
    "Amount Of Safely Disposed - Other Waste Domain4 - Previous Year": "0",
    "Amount Of Re Used - Other Waste Domain5 - Previous Year": "0",
    "Amount Of Recycled - Other Waste Domain5 - Previous Year": "0",
    "Amount Of Safely Disposed - Other Waste Domain5 - Previous Year": "0",
    "Number Of Complaints Filed From Stake Holder Group During The Year - Other Stake Holder Domain4 - Previous Year": "0",
    "Number Of Complaints Pending From Stake Holder Group Resolution At The End Of Year - Other Stake Holder Domain4 - Previous Year": "0",
    "Number Of Complaints Filed From Stake Holder Group During The Year - Other Stake Holder Domain5 - Previous Year": "0",
    "Number Of Complaints Pending From Stake Holder Group Resolution At The End Of Year - Other Stake Holder Domain5 - Previous Year": "0",
    "Number Of Complaints Filed From Stake Holder Group During The Year - Other Stake Holder Domain6 - Previous Year": "0",
    "Number Of Complaints Pending From Stake Holder Group Resolution At The End Of Year - Other Stake Holder Domain6 - Previous Year": "0",
    "Number Of Complaints Filed From Stake Holder Group During The Year - Other Stake Holder Domain7 - Previous Year": "0",
    "Number Of Complaints Pending From Stake Holder Group Resolution At The End Of Year - Other Stake Holder Domain7 - Previous Year": "0",
    "Recycled Or Re Used In Put Material To Total Material - Recycled Or Reused Input Material Used In Production Or Providing Services Domain4 - Previous Year": "0",
    "Recycled Or Re Used In Put Material To Total Material - Recycled Or Reused Input Material Used In Production Or Providing Services Domain5 - Previous Year": "0",
    "Recycled Or Re Used In Put Material To Total Material - Recycled Or Reused Input Material Used In Production Or Providing Services Domain6 - Previous Year": "0",
    "Recycled Or Re Used In Put Material To Total Material - Recycled Or Reused Input Material Used In Production Or Providing Services Domain7 - Previous Year": "0",
    "Other Emissions - Other Air Emissions Domain2 - Previous Year": "0",
    "Other Emissions - Other Air Emissions Domain3 - Previous Year": "0",
    "Details For Grievance Redressal Mechanism In Place Is Not Applicable Explanatory Text Block - Other Stake Holder Domain7 - Previous Year": "0",
    "Other Emissions - Other Air Emissions Domain4 - Previous Year": "0",
    "Other Emissions - Other Air Emissions Domain5 - Previous Year": "0",
    "Other Emissions - Other Air Emissions Domain6 - Previous Year": "0",
    "Other Emissions - Other Air Emissions Domain7 - Previous Year": "0",
    "Energy Consumption Through Other Sources From Renewable Sources - Energy Consumption Through Other Source From Renewable Sources Domain3 - Previous Year": "0",
    "Energy Consumption Through Other Sources From Renewable Sources - Energy Consumption Through Other Source From Renewable Sources Domain4 - Previous Year": "0",
    "Energy Consumption Through Other Sources From Non Renewable Sources - Energy Consumption Through Other Source From Non Renewable Sources Domain3 - Previous Year": "0",
    "Energy Consumption Through Other Sources From Non Renewable Sources - Energy Consumption Through Other Source From Non Renewable Sources Domain4 - Previous Year": "0",
    "Recycled Or Re Used In Put Material To Total Material - Recycled Or Reused Input Material Used In Production Or Providing Services Domain8 - Previous Year": "0",
    "The Entity Does Not Consider The Principles Material To Its Business - Principle2 Member": "0",
    "The Entity Does Not Consider The Principles Material To Its Business - Principle6 Member": "0",
    "The Entity Does Not Consider The Principles Material To Its Business - Principle9 Member": "0",
    "The Entity Is Not At AStage Where It Is In APosition To Formulate And Implement The Policies On Specified Principles - Principle2 Member": "0",
    "The Entity Is Not At AStage Where It Is In APosition To Formulate And Implement The Policies On Specified Principles - Principle6 Member": "0",
    "The Entity Is Not At AStage Where It Is In APosition To Formulate And Implement The Policies On Specified Principles - Principle9 Member": "0",
    "The Entity Does Not Have The Financial Or Human And Technical Resources Available For The Task - Principle2 Member": "0",
    "The Entity Does Not Have The Financial Or Human And Technical Resources Available For The Task - Principle6 Member": "0",
    "The Entity Does Not Have The Financial Or Human And Technical Resources Available For The Task - Principle9 Member": "0",
    "It Is Planned To Be Done In The Next Financial Year - Principle2 Member": "0",
    "It Is Planned To Be Done In The Next Financial Year - Principle6 Member": "0",
    "It Is Planned To Be Done In The Next Financial Year - Principle9 Member": "0",
    "Scrip Code": "0",
    "Any Independent Assessment Or Evaluation Or Assurance Has Been Carried Out By An External Agency For Energy Consumption": "0",
    "Other Emissions - Other Air Emissions Domain8 - Previous Year": "0",
    "The Entity Does Not Consider The Principles Material To Its Business - Principle8 Member": "0",
    "The Entity Is Not At AStage Where It Is In APosition To Formulate And Implement The Policies On Specified Principles - Principle8 Member": "0",
    "The Entity Does Not Have The Financial Or Human And Technical Resources Available For The Task - Principle8 Member": "0",
    "It Is Planned To Be Done In The Next Financial Year - Principle8 Member": "0",
    "The Entity Does Not Consider The Principles Material To Its Business - Principle4 Member": "0",
    "The Entity Does Not Consider The Principles Material To Its Business - Principle5 Member": "0",
    "The Entity Is Not At AStage Where It Is In APosition To Formulate And Implement The Policies On Specified Principles - Principle4 Member": "0",
    "The Entity Is Not At AStage Where It Is In APosition To Formulate And Implement The Policies On Specified Principles - Principle5 Member": "0",
    "The Entity Does Not Have The Financial Or Human And Technical Resources Available For The Task - Principle4 Member": "0",
    "The Entity Does Not Have The Financial Or Human And Technical Resources Available For The Task - Principle5 Member": "0",
    "It Is Planned To Be Done In The Next Financial Year - Principle4 Member": "0",
    "It Is Planned To Be Done In The Next Financial Year - Principle5 Member": "0",
    "Other Emissions - Other Air Emissions Domain9 - Previous Year": "0",
    "Other Emissions - Other Air Emissions Domain10 - Previous Year": "0",
    "Other Emissions - Other Air Emissions Domain11 - Previous Year": "0",
    "Other Emissions - Other Air Emissions Domain12 - Previous Year": "0",
    "Other Emissions - Other Air Emissions Domain13 - Previous Year": "0",
    "Recycled Or Re Used In Put Material To Total Material - Recycled Or Reused Input Material Used In Production Or Providing Services Domain9 - Previous Year": "0",
    "The Entity Does Not Consider The Principles Material To Its Business - Principle3 Member": "0",
    "The Entity Is Not At AStage Where It Is In APosition To Formulate And Implement The Policies On Specified Principles - Principle3 Member": "0",
    "The Entity Does Not Have The Financial Or Human And Technical Resources Available For The Task - Principle3 Member": "0",
    "It Is Planned To Be Done In The Next Financial Year - Principle3 Member": "0",
    "Water Withdrawal By Surface Water Per Area - Facility Or Plant Located In Areas Of Water Stress Domain6 - Previous Year": "0",
    "Water Withdrawal By Groundwater Per Area - Facility Or Plant Located In Areas Of Water Stress Domain6 - Previous Year": "0",
    "Water Withdrawal By Third Party Water Per Area - Facility Or Plant Located In Areas Of Water Stress Domain6 - Previous Year": "0",
    "Water Withdrawal By Seawater Or Desalinated Water Per Area - Facility Or Plant Located In Areas Of Water Stress Domain6 - Previous Year": "0",
    "Water Withdrawal By Others Per Area - Facility Or Plant Located In Areas Of Water Stress Domain6 - Previous Year": "0",
    "Total Volume Of Water Withdrawal Per Area - Facility Or Plant Located In Areas Of Water Stress Domain6 - Previous Year": "0",
    "Total Volume Of Water Consumption Per Area - Facility Or Plant Located In Areas Of Water Stress Domain6 - Previous Year": "0",
    "Water Intensity Per Rupee Of Turnover Per Area - Facility Or Plant Located In Areas Of Water Stress Domain6 - Previous Year": "0",
    "Waste Intensity The Relevant Metric May Be Selected By The Entity Per Area - Facility Or Plant Located In Areas Of Water Stress Domain6 - Previous Year":
        "{Total Waste Generated} / {Revenue From Operations}",
    "Water Discharge To Surface Water Per Area - Facility Or Plant Located In Areas Of Water Stress Domain6 - Previous Year":
        "{Total Water Discharged In Kilolitres Per Area - Facility Or Plant Located In Areas Of Water Stress Domain6 - Previous Year} - {Water Discharge To Groundwater Per Area - Facility Or Plant Located In Areas Of Water Stress Domain6 - Previous Year} - {Water Discharge To Seawater Per Area - Facility Or Plant Located In Areas Of Water Stress Domain6 - Previous Year} - {Water Discharge By Sent To Third Parties Per Area - Facility Or Plant Located In Areas Of Water Stress Domain6 - Previous Year} - {Water Discharge To Others Per Area - Facility Or Plant Located In Areas Of Water Stress Domain6 - Previous Year}",
    "Water Discharge To Surface Water With Out Treatment Per Area - Facility Or Plant Located In Areas Of Water Stress Domain6 - Previous Year":
        "{Water Discharge To Surface Water Per Area - Facility Or Plant Located In Areas Of Water Stress Domain6 - Previous Year} - {Water Discharge To Surface Water With Treatment Per Area - Facility Or Plant Located In Areas Of Water Stress Domain6 - Previous Year}",
    "Water Discharge To Surface Water With Treatment Per Area - Facility Or Plant Located In Areas Of Water Stress Domain6 - Previous Year":
        "{Water Discharge To Surface Water Per Area - Facility Or Plant Located In Areas Of Water Stress Domain6 - Previous Year} - {Water Discharge To Surface Water With Out Treatment Per Area - Facility Or Plant Located In Areas Of Water Stress Domain6 - Previous Year}",
    "Water Discharge To Groundwater Per Area - Facility Or Plant Located In Areas Of Water Stress Domain6 - Previous Year":
        "{Total Water Discharged In Kilolitres Per Area - Facility Or Plant Located In Areas Of Water Stress Domain6 - Previous Year} - {Water Discharge To Surface Water Per Area - Facility Or Plant Located In Areas Of Water Stress Domain6 - Previous Year} - {Water Discharge To Seawater Per Area - Facility Or Plant Located In Areas Of Water Stress Domain6 - Previous Year} - {Water Discharge By Sent To Third Parties Per Area - Facility Or Plant Located In Areas Of Water Stress Domain6 - Previous Year} - {Water Discharge To Others Per Area - Facility Or Plant Located In Areas Of Water Stress Domain6 - Previous Year}",
    "Water Discharge To Groundwater With Out Treatment Per Area - Facility Or Plant Located In Areas Of Water Stress Domain6 - Previous Year":
        "{Water Discharge To Groundwater Per Area - Facility Or Plant Located In Areas Of Water Stress Domain6 - Previous Year} - {Water Discharge To Groundwater With Treatment Per Area - Facility Or Plant Located In Areas Of Water Stress Domain6 - Previous Year}",
    "Water Discharge To Groundwater With Treatment Per Area - Facility Or Plant Located In Areas Of Water Stress Domain6 - Previous Year":
        "{Water Discharge To Groundwater Per Area - Facility Or Plant Located In Areas Of Water Stress Domain6 - Previous Year} - {Water Discharge To Groundwater With Out Treatment Per Area - Facility Or Plant Located In Areas Of Water Stress Domain6 - Previous Year}",
    "Water Discharge To Seawater Per Area - Facility Or Plant Located In Areas Of Water Stress Domain6 - Previous Year":
        "{Total Water Discharged In Kilolitres Per Area - Facility Or Plant Located In Areas Of Water Stress Domain6 - Previous Year} - {Water Discharge To Surface Water Per Area - Facility Or Plant Located In Areas Of Water Stress Domain6 - Previous Year} - {Water Discharge To Groundwater Per Area - Facility Or Plant Located In Areas Of Water Stress Domain6 - Previous Year} - {Water Discharge By Sent To Third Parties Per Area - Facility Or Plant Located In Areas Of Water Stress Domain6 - Previous Year} - {Water Discharge To Others Per Area - Facility Or Plant Located In Areas Of Water Stress Domain6 - Previous Year}",
    "Water Discharge To Seawater With Out Treatment Per Area - Facility Or Plant Located In Areas Of Water Stress Domain6 - Previous Year":
        "{Water Discharge To Seawater Per Area - Facility Or Plant Located In Areas Of Water Stress Domain6 - Previous Year} - {Water Discharge To Seawater With Treatment Per Area - Facility Or Plant Located In Areas Of Water Stress Domain6 - Previous Year}",
    "Water Discharge To Seawater With Treatment Per Area - Facility Or Plant Located In Areas Of Water Stress Domain6 - Previous Year":
        "{Water Discharge To Seawater Per Area - Facility Or Plant Located In Areas Of Water Stress Domain6 - Previous Year} - {Water Discharge To Seawater With Out Treatment Per Area - Facility Or Plant Located In Areas Of Water Stress Domain6 - Previous Year}",
    "Water Discharge By Sent To Third Parties Per Area - Facility Or Plant Located In Areas Of Water Stress Domain6 - Previous Year":
        "{Total Water Discharged In Kilolitres Per Area - Facility Or Plant Located In Areas Of Water Stress Domain6 - Previous Year} - {Water Discharge To Surface Water Per Area - Facility Or Plant Located In Areas Of Water Stress Domain6 - Previous Year} - {Water Discharge To Groundwater Per Area - Facility Or Plant Located In Areas Of Water Stress Domain6 - Previous Year} - {Water Discharge To Seawater Per Area - Facility Or Plant Located In Areas Of Water Stress Domain6 - Previous Year} - {Water Discharge To Others Per Area - Facility Or Plant Located In Areas Of Water Stress Domain6 - Previous Year}",
    "Water Discharge By Sent To Third Parties Without Treatment Per Area - Facility Or Plant Located In Areas Of Water Stress Domain6 - Previous Year": "0",
    "Water Discharge By Sent To Third Parties With Treatment Per Area - Facility Or Plant Located In Areas Of Water Stress Domain6 - Previous Year": "0",
    "Water Discharge To Others Per Area - Facility Or Plant Located In Areas Of Water Stress Domain6 - Previous Year":
        "{Total Water Discharged In Kilolitres Per Area - Facility Or Plant Located In Areas Of Water Stress Domain6 - Previous Year} - {Water Discharge To Surface Water Per Area - Facility Or Plant Located In Areas Of Water Stress Domain6 - Previous Year} - {Water Discharge To Groundwater Per Area - Facility Or Plant Located In Areas Of Water Stress Domain6 - Previous Year} - {Water Discharge To Seawater Per Area - Facility Or Plant Located In Areas Of Water Stress Domain6 - Previous Year} - {Water Discharge By Sent To Third Parties Per Area - Facility Or Plant Located In Areas Of Water Stress Domain6 - Previous Year}",
    "Water Discharge To Others Without Treatment Per Area - Facility Or Plant Located In Areas Of Water Stress Domain6 - Previous Year": "0",
    "Water Discharge To Others With Treatment Per Area - Facility Or Plant Located In Areas Of Water Stress Domain6 - Previous Year": "0",
    "Total Water Discharged In Kilolitres Per Area - Facility Or Plant Located In Areas Of Water Stress Domain6 - Previous Year": "0",
    "Water Withdrawal By Surface Water Per Area - Facility Or Plant Located In Areas Of Water Stress Domain7 - Previous Year": "0",
    "Water Withdrawal By Groundwater Per Area - Facility Or Plant Located In Areas Of Water Stress Domain7 - Previous Year": "0",
    "Water Withdrawal By Third Party Water Per Area - Facility Or Plant Located In Areas Of Water Stress Domain7 - Previous Year": "0",
    "Water Withdrawal By Seawater Or Desalinated Water Per Area - Facility Or Plant Located In Areas Of Water Stress Domain7 - Previous Year": "0",
    "Water Withdrawal By Others Per Area - Facility Or Plant Located In Areas Of Water Stress Domain7 - Previous Year": "0",
    "Total Volume Of Water Withdrawal Per Area - Facility Or Plant Located In Areas Of Water Stress Domain7 - Previous Year": "0",
    "Total Volume Of Water Consumption Per Area - Facility Or Plant Located In Areas Of Water Stress Domain7 - Previous Year": "0",
    "Water Intensity Per Rupee Of Turnover Per Area - Facility Or Plant Located In Areas Of Water Stress Domain7 - Previous Year": "0",
    "Waste Intensity The Relevant Metric May Be Selected By The Entity Per Area - Facility Or Plant Located In Areas Of Water Stress Domain7 - Previous Year":
        "{Total Waste Generated} / {Revenue From Operations}",
    "Water Discharge To Surface Water Per Area - Facility Or Plant Located In Areas Of Water Stress Domain7 - Previous Year":
        "{Total Water Discharged In Kilolitres Per Area - Facility Or Plant Located In Areas Of Water Stress Domain7 - Previous Year} - {Water Discharge To Groundwater Per Area - Facility Or Plant Located In Areas Of Water Stress Domain7 - Previous Year} - {Water Discharge To Seawater Per Area - Facility Or Plant Located In Areas Of Water Stress Domain7 - Previous Year} - {Water Discharge By Sent To Third Parties Per Area - Facility Or Plant Located In Areas Of Water Stress Domain7 - Previous Year} - {Water Discharge To Others Per Area - Facility Or Plant Located In Areas Of Water Stress Domain7 - Previous Year}",
    "Water Discharge To Surface Water With Out Treatment Per Area - Facility Or Plant Located In Areas Of Water Stress Domain7 - Previous Year":
        "{Water Discharge To Surface Water Per Area - Facility Or Plant Located In Areas Of Water Stress Domain7 - Previous Year} - {Water Discharge To Surface Water With Treatment Per Area - Facility Or Plant Located In Areas Of Water Stress Domain7 - Previous Year}",
    "Water Discharge To Surface Water With Treatment Per Area - Facility Or Plant Located In Areas Of Water Stress Domain7 - Previous Year":
        "{Water Discharge To Surface Water Per Area - Facility Or Plant Located In Areas Of Water Stress Domain7 - Previous Year} - {Water Discharge To Surface Water With Out Treatment Per Area - Facility Or Plant Located In Areas Of Water Stress Domain7 - Previous Year}",
    "Water Discharge To Groundwater Per Area - Facility Or Plant Located In Areas Of Water Stress Domain7 - Previous Year":
        "{Total Water Discharged In Kilolitres Per Area - Facility Or Plant Located In Areas Of Water Stress Domain7 - Previous Year} - {Water Discharge To Surface Water Per Area - Facility Or Plant Located In Areas Of Water Stress Domain7 - Previous Year} - {Water Discharge To Seawater Per Area - Facility Or Plant Located In Areas Of Water Stress Domain7 - Previous Year} - {Water Discharge By Sent To Third Parties Per Area - Facility Or Plant Located In Areas Of Water Stress Domain7 - Previous Year} - {Water Discharge To Others Per Area - Facility Or Plant Located In Areas Of Water Stress Domain7 - Previous Year}",
    "Water Discharge To Groundwater With Out Treatment Per Area - Facility Or Plant Located In Areas Of Water Stress Domain7 - Previous Year":
        "{Water Discharge To Groundwater Per Area - Facility Or Plant Located In Areas Of Water Stress Domain7 - Previous Year} - {Water Discharge To Groundwater With Treatment Per Area - Facility Or Plant Located In Areas Of Water Stress Domain7 - Previous Year}",
    "Water Discharge To Groundwater With Treatment Per Area - Facility Or Plant Located In Areas Of Water Stress Domain7 - Previous Year":
        "{Water Discharge To Groundwater Per Area - Facility Or Plant Located In Areas Of Water Stress Domain7 - Previous Year} - {Water Discharge To Groundwater With Out Treatment Per Area - Facility Or Plant Located In Areas Of Water Stress Domain7 - Previous Year}",
    "Water Discharge To Seawater Per Area - Facility Or Plant Located In Areas Of Water Stress Domain7 - Previous Year":
        "{Total Water Discharged In Kilolitres Per Area - Facility Or Plant Located In Areas Of Water Stress Domain7 - Previous Year} - {Water Discharge To Surface Water Per Area - Facility Or Plant Located In Areas Of Water Stress Domain7 - Previous Year} - {Water Discharge To Groundwater Per Area - Facility Or Plant Located In Areas Of Water Stress Domain7 - Previous Year} - {Water Discharge By Sent To Third Parties Per Area - Facility Or Plant Located In Areas Of Water Stress Domain7 - Previous Year} - {Water Discharge To Others Per Area - Facility Or Plant Located In Areas Of Water Stress Domain7 - Previous Year}",
    "Water Discharge To Seawater With Out Treatment Per Area - Facility Or Plant Located In Areas Of Water Stress Domain7 - Previous Year":
        "{Water Discharge To Seawater Per Area - Facility Or Plant Located In Areas Of Water Stress Domain7 - Previous Year} - {Water Discharge To Seawater With Treatment Per Area - Facility Or Plant Located In Areas Of Water Stress Domain7 - Previous Year}",
    "Water Discharge To Seawater With Treatment Per Area - Facility Or Plant Located In Areas Of Water Stress Domain7 - Previous Year":
        "{Water Discharge To Seawater Per Area - Facility Or Plant Located In Areas Of Water Stress Domain7 - Previous Year} - {Water Discharge To Seawater With Out Treatment Per Area - Facility Or Plant Located In Areas Of Water Stress Domain7 - Previous Year}",
    "Water Discharge By Sent To Third Parties Per Area - Facility Or Plant Located In Areas Of Water Stress Domain7 - Previous Year":
        "{Total Water Discharged In Kilolitres Per Area - Facility Or Plant Located In Areas Of Water Stress Domain7 - Previous Year} - {Water Discharge To Surface Water Per Area - Facility Or Plant Located In Areas Of Water Stress Domain7 - Previous Year} - {Water Discharge To Groundwater Per Area - Facility Or Plant Located In Areas Of Water Stress Domain7 - Previous Year} - {Water Discharge To Seawater Per Area - Facility Or Plant Located In Areas Of Water Stress Domain7 - Previous Year} - {Water Discharge To Others Per Area - Facility Or Plant Located In Areas Of Water Stress Domain7 - Previous Year}",
    "Water Discharge By Sent To Third Parties Without Treatment Per Area - Facility Or Plant Located In Areas Of Water Stress Domain7 - Previous Year": "0",
    "Water Discharge By Sent To Third Parties With Treatment Per Area - Facility Or Plant Located In Areas Of Water Stress Domain7 - Previous Year": "0",
    "Water Discharge To Others Per Area - Facility Or Plant Located In Areas Of Water Stress Domain7 - Previous Year":
        "{Total Water Discharged In Kilolitres Per Area - Facility Or Plant Located In Areas Of Water Stress Domain7 - Previous Year} - {Water Discharge To Surface Water Per Area - Facility Or Plant Located In Areas Of Water Stress Domain7 - Previous Year} - {Water Discharge To Groundwater Per Area - Facility Or Plant Located In Areas Of Water Stress Domain7 - Previous Year} - {Water Discharge To Seawater Per Area - Facility Or Plant Located In Areas Of Water Stress Domain7 - Previous Year} - {Water Discharge By Sent To Third Parties Per Area - Facility Or Plant Located In Areas Of Water Stress Domain7 - Previous Year}",
    "Water Discharge To Others Without Treatment Per Area - Facility Or Plant Located In Areas Of Water Stress Domain7 - Previous Year": "0",
    "Water Discharge To Others With Treatment Per Area - Facility Or Plant Located In Areas Of Water Stress Domain7 - Previous Year": "0",
    "Total Water Discharged In Kilolitres Per Area - Facility Or Plant Located In Areas Of Water Stress Domain7 - Previous Year": "0",
    "Water Withdrawal By Surface Water Per Area - Facility Or Plant Located In Areas Of Water Stress Domain8 - Previous Year": "0",
    "Water Withdrawal By Groundwater Per Area - Facility Or Plant Located In Areas Of Water Stress Domain8 - Previous Year": "0",
    "Water Withdrawal By Third Party Water Per Area - Facility Or Plant Located In Areas Of Water Stress Domain8 - Previous Year": "0",
    "Water Withdrawal By Seawater Or Desalinated Water Per Area - Facility Or Plant Located In Areas Of Water Stress Domain8 - Previous Year": "0",
    "Water Withdrawal By Others Per Area - Facility Or Plant Located In Areas Of Water Stress Domain8 - Previous Year": "0",
    "Total Volume Of Water Withdrawal Per Area - Facility Or Plant Located In Areas Of Water Stress Domain8 - Previous Year": "0",
    "Total Volume Of Water Consumption Per Area - Facility Or Plant Located In Areas Of Water Stress Domain8 - Previous Year": "0",
    "Water Intensity Per Rupee Of Turnover Per Area - Facility Or Plant Located In Areas Of Water Stress Domain8 - Previous Year": "0",
    "Waste Intensity The Relevant Metric May Be Selected By The Entity Per Area - Facility Or Plant Located In Areas Of Water Stress Domain8 - Previous Year":
        "{Total Waste Generated} / {Revenue From Operations}",
    "Water Discharge To Surface Water Per Area - Facility Or Plant Located In Areas Of Water Stress Domain8 - Previous Year":
        "{Total Water Discharged In Kilolitres Per Area - Facility Or Plant Located In Areas Of Water Stress Domain8 - Previous Year} - {Water Discharge To Groundwater Per Area - Facility Or Plant Located In Areas Of Water Stress Domain8 - Previous Year} - {Water Discharge To Seawater Per Area - Facility Or Plant Located In Areas Of Water Stress Domain8 - Previous Year} - {Water Discharge By Sent To Third Parties Per Area - Facility Or Plant Located In Areas Of Water Stress Domain8 - Previous Year} - {Water Discharge To Others Per Area - Facility Or Plant Located In Areas Of Water Stress Domain8 - Previous Year}",
    "Water Discharge To Surface Water With Out Treatment Per Area - Facility Or Plant Located In Areas Of Water Stress Domain8 - Previous Year":
        "{Water Discharge To Surface Water Per Area - Facility Or Plant Located In Areas Of Water Stress Domain8 - Previous Year} - {Water Discharge To Surface Water With Treatment Per Area - Facility Or Plant Located In Areas Of Water Stress Domain8 - Previous Year}",
    "Water Discharge To Surface Water With Treatment Per Area - Facility Or Plant Located In Areas Of Water Stress Domain8 - Previous Year":
        "{Water Discharge To Surface Water Per Area - Facility Or Plant Located In Areas Of Water Stress Domain8 - Previous Year} - {Water Discharge To Surface Water With Out Treatment Per Area - Facility Or Plant Located In Areas Of Water Stress Domain8 - Previous Year}",
    "Water Discharge To Groundwater Per Area - Facility Or Plant Located In Areas Of Water Stress Domain8 - Previous Year":
        "{Total Water Discharged In Kilolitres Per Area - Facility Or Plant Located In Areas Of Water Stress Domain8 - Previous Year} - {Water Discharge To Surface Water Per Area - Facility Or Plant Located In Areas Of Water Stress Domain8 - Previous Year} - {Water Discharge To Seawater Per Area - Facility Or Plant Located In Areas Of Water Stress Domain8 - Previous Year} - {Water Discharge By Sent To Third Parties Per Area - Facility Or Plant Located In Areas Of Water Stress Domain8 - Previous Year} - {Water Discharge To Others Per Area - Facility Or Plant Located In Areas Of Water Stress Domain8 - Previous Year}",
    "Water Discharge To Groundwater With Out Treatment Per Area - Facility Or Plant Located In Areas Of Water Stress Domain8 - Previous Year":
        "{Water Discharge To Groundwater Per Area - Facility Or Plant Located In Areas Of Water Stress Domain8 - Previous Year} - {Water Discharge To Groundwater With Treatment Per Area - Facility Or Plant Located In Areas Of Water Stress Domain8 - Previous Year}",
    "Water Discharge To Groundwater With Treatment Per Area - Facility Or Plant Located In Areas Of Water Stress Domain8 - Previous Year":
        "{Water Discharge To Groundwater Per Area - Facility Or Plant Located In Areas Of Water Stress Domain8 - Previous Year} - {Water Discharge To Groundwater With Out Treatment Per Area - Facility Or Plant Located In Areas Of Water Stress Domain8 - Previous Year}",
    "Water Discharge To Seawater Per Area - Facility Or Plant Located In Areas Of Water Stress Domain8 - Previous Year":
        "{Total Water Discharged In Kilolitres Per Area - Facility Or Plant Located In Areas Of Water Stress Domain8 - Previous Year} - {Water Discharge To Surface Water Per Area - Facility Or Plant Located In Areas Of Water Stress Domain8 - Previous Year} - {Water Discharge To Groundwater Per Area - Facility Or Plant Located In Areas Of Water Stress Domain8 - Previous Year} - {Water Discharge By Sent To Third Parties Per Area - Facility Or Plant Located In Areas Of Water Stress Domain8 - Previous Year} - {Water Discharge To Others Per Area - Facility Or Plant Located In Areas Of Water Stress Domain8 - Previous Year}",
    "Water Discharge To Seawater With Out Treatment Per Area - Facility Or Plant Located In Areas Of Water Stress Domain8 - Previous Year":
        "{Water Discharge To Seawater Per Area - Facility Or Plant Located In Areas Of Water Stress Domain8 - Previous Year} - {Water Discharge To Seawater With Treatment Per Area - Facility Or Plant Located In Areas Of Water Stress Domain8 - Previous Year}",
    "Water Discharge To Seawater With Treatment Per Area - Facility Or Plant Located In Areas Of Water Stress Domain8 - Previous Year":
        "{Water Discharge To Seawater Per Area - Facility Or Plant Located In Areas Of Water Stress Domain8 - Previous Year} - {Water Discharge To Seawater With Out Treatment Per Area - Facility Or Plant Located In Areas Of Water Stress Domain8 - Previous Year}",
    "Water Discharge By Sent To Third Parties Per Area - Facility Or Plant Located In Areas Of Water Stress Domain8 - Previous Year":
        "{Total Water Discharged In Kilolitres Per Area - Facility Or Plant Located In Areas Of Water Stress Domain8 - Previous Year} - {Water Discharge To Surface Water Per Area - Facility Or Plant Located In Areas Of Water Stress Domain8 - Previous Year} - {Water Discharge To Groundwater Per Area - Facility Or Plant Located In Areas Of Water Stress Domain8 - Previous Year} - {Water Discharge To Seawater Per Area - Facility Or Plant Located In Areas Of Water Stress Domain8 - Previous Year} - {Water Discharge To Others Per Area - Facility Or Plant Located In Areas Of Water Stress Domain8 - Previous Year}",
    "Water Discharge By Sent To Third Parties Without Treatment Per Area - Facility Or Plant Located In Areas Of Water Stress Domain8 - Previous Year": "0",
    "Water Discharge By Sent To Third Parties With Treatment Per Area - Facility Or Plant Located In Areas Of Water Stress Domain8 - Previous Year": "0",
    "Water Discharge To Others Per Area - Facility Or Plant Located In Areas Of Water Stress Domain8 - Previous Year":
        "{Total Water Discharged In Kilolitres Per Area - Facility Or Plant Located In Areas Of Water Stress Domain8 - Previous Year} - {Water Discharge To Surface Water Per Area - Facility Or Plant Located In Areas Of Water Stress Domain8 - Previous Year} - {Water Discharge To Groundwater Per Area - Facility Or Plant Located In Areas Of Water Stress Domain8 - Previous Year} - {Water Discharge To Seawater Per Area - Facility Or Plant Located In Areas Of Water Stress Domain8 - Previous Year} - {Water Discharge By Sent To Third Parties Per Area - Facility Or Plant Located In Areas Of Water Stress Domain8 - Previous Year}",
    "Water Discharge To Others Without Treatment Per Area - Facility Or Plant Located In Areas Of Water Stress Domain8 - Previous Year": "0",
    "Water Discharge To Others With Treatment Per Area - Facility Or Plant Located In Areas Of Water Stress Domain8 - Previous Year": "0",
    "Total Water Discharged In Kilolitres Per Area - Facility Or Plant Located In Areas Of Water Stress Domain8 - Previous Year": "0",
    "Water Withdrawal By Surface Water Per Area - Facility Or Plant Located In Areas Of Water Stress Domain9 - Previous Year": "0",
    "Water Withdrawal By Groundwater Per Area - Facility Or Plant Located In Areas Of Water Stress Domain9 - Previous Year": "0",
    "Water Withdrawal By Third Party Water Per Area - Facility Or Plant Located In Areas Of Water Stress Domain9 - Previous Year": "0",
    "Water Withdrawal By Seawater Or Desalinated Water Per Area - Facility Or Plant Located In Areas Of Water Stress Domain9 - Previous Year": "0",
    "Water Withdrawal By Others Per Area - Facility Or Plant Located In Areas Of Water Stress Domain9 - Previous Year": "0",
    "Total Volume Of Water Withdrawal Per Area - Facility Or Plant Located In Areas Of Water Stress Domain9 - Previous Year": "0",
    "Total Volume Of Water Consumption Per Area - Facility Or Plant Located In Areas Of Water Stress Domain9 - Previous Year": "0",
    "Water Intensity Per Rupee Of Turnover Per Area - Facility Or Plant Located In Areas Of Water Stress Domain9 - Previous Year": "0",
    "Waste Intensity The Relevant Metric May Be Selected By The Entity Per Area - Facility Or Plant Located In Areas Of Water Stress Domain9 - Previous Year":
        "{Total Waste Generated} / {Revenue From Operations}",
    "Water Discharge To Surface Water Per Area - Facility Or Plant Located In Areas Of Water Stress Domain9 - Previous Year":
        "{Total Water Discharged In Kilolitres Per Area - Facility Or Plant Located In Areas Of Water Stress Domain9 - Previous Year} - {Water Discharge To Groundwater Per Area - Facility Or Plant Located In Areas Of Water Stress Domain9 - Previous Year} - {Water Discharge To Seawater Per Area - Facility Or Plant Located In Areas Of Water Stress Domain9 - Previous Year} - {Water Discharge By Sent To Third Parties Per Area - Facility Or Plant Located In Areas Of Water Stress Domain9 - Previous Year} - {Water Discharge To Others Per Area - Facility Or Plant Located In Areas Of Water Stress Domain9 - Previous Year}",
    "Water Discharge To Surface Water With Out Treatment Per Area - Facility Or Plant Located In Areas Of Water Stress Domain9 - Previous Year":
        "{Water Discharge To Surface Water Per Area - Facility Or Plant Located In Areas Of Water Stress Domain9 - Previous Year} - {Water Discharge To Surface Water With Treatment Per Area - Facility Or Plant Located In Areas Of Water Stress Domain9 - Previous Year}",
    "Water Discharge To Surface Water With Treatment Per Area - Facility Or Plant Located In Areas Of Water Stress Domain9 - Previous Year":
        "{Water Discharge To Surface Water Per Area - Facility Or Plant Located In Areas Of Water Stress Domain9 - Previous Year} - {Water Discharge To Surface Water With Out Treatment Per Area - Facility Or Plant Located In Areas Of Water Stress Domain9 - Previous Year}",
    "Water Discharge To Groundwater Per Area - Facility Or Plant Located In Areas Of Water Stress Domain9 - Previous Year":
        "{Total Water Discharged In Kilolitres Per Area - Facility Or Plant Located In Areas Of Water Stress Domain9 - Previous Year} - {Water Discharge To Surface Water Per Area - Facility Or Plant Located In Areas Of Water Stress Domain9 - Previous Year} - {Water Discharge To Seawater Per Area - Facility Or Plant Located In Areas Of Water Stress Domain9 - Previous Year} - {Water Discharge By Sent To Third Parties Per Area - Facility Or Plant Located In Areas Of Water Stress Domain9 - Previous Year} - {Water Discharge To Others Per Area - Facility Or Plant Located In Areas Of Water Stress Domain9 - Previous Year}",
    "Water Discharge To Groundwater With Out Treatment Per Area - Facility Or Plant Located In Areas Of Water Stress Domain9 - Previous Year":
        "{Water Discharge To Groundwater Per Area - Facility Or Plant Located In Areas Of Water Stress Domain9 - Previous Year} - {Water Discharge To Groundwater With Treatment Per Area - Facility Or Plant Located In Areas Of Water Stress Domain9 - Previous Year}",
    "Water Discharge To Groundwater With Treatment Per Area - Facility Or Plant Located In Areas Of Water Stress Domain9 - Previous Year":
        "{Water Discharge To Groundwater Per Area - Facility Or Plant Located In Areas Of Water Stress Domain9 - Previous Year} - {Water Discharge To Groundwater With Out Treatment Per Area - Facility Or Plant Located In Areas Of Water Stress Domain9 - Previous Year}",
    "Water Discharge To Seawater Per Area - Facility Or Plant Located In Areas Of Water Stress Domain9 - Previous Year":
        "{Total Water Discharged In Kilolitres Per Area - Facility Or Plant Located In Areas Of Water Stress Domain9 - Previous Year} - {Water Discharge To Surface Water Per Area - Facility Or Plant Located In Areas Of Water Stress Domain9 - Previous Year} - {Water Discharge To Groundwater Per Area - Facility Or Plant Located In Areas Of Water Stress Domain9 - Previous Year} - {Water Discharge By Sent To Third Parties Per Area - Facility Or Plant Located In Areas Of Water Stress Domain9 - Previous Year} - {Water Discharge To Others Per Area - Facility Or Plant Located In Areas Of Water Stress Domain9 - Previous Year}",
    "Water Discharge To Seawater With Out Treatment Per Area - Facility Or Plant Located In Areas Of Water Stress Domain9 - Previous Year":
        "{Water Discharge To Seawater Per Area - Facility Or Plant Located In Areas Of Water Stress Domain9 - Previous Year} - {Water Discharge To Seawater With Treatment Per Area - Facility Or Plant Located In Areas Of Water Stress Domain9 - Previous Year}",
    "Water Discharge To Seawater With Treatment Per Area - Facility Or Plant Located In Areas Of Water Stress Domain9 - Previous Year":
        "{Water Discharge To Seawater Per Area - Facility Or Plant Located In Areas Of Water Stress Domain9 - Previous Year} - {Water Discharge To Seawater With Out Treatment Per Area - Facility Or Plant Located In Areas Of Water Stress Domain9 - Previous Year}",
    "Water Discharge By Sent To Third Parties Per Area - Facility Or Plant Located In Areas Of Water Stress Domain9 - Previous Year":
        "{Total Water Discharged In Kilolitres Per Area - Facility Or Plant Located In Areas Of Water Stress Domain9 - Previous Year} - {Water Discharge To Surface Water Per Area - Facility Or Plant Located In Areas Of Water Stress Domain9 - Previous Year} - {Water Discharge To Groundwater Per Area - Facility Or Plant Located In Areas Of Water Stress Domain9 - Previous Year} - {Water Discharge To Seawater Per Area - Facility Or Plant Located In Areas Of Water Stress Domain9 - Previous Year} - {Water Discharge To Others Per Area - Facility Or Plant Located In Areas Of Water Stress Domain9 - Previous Year}",
    "Water Discharge By Sent To Third Parties Without Treatment Per Area - Facility Or Plant Located In Areas Of Water Stress Domain9 - Previous Year": "0",
    "Water Discharge By Sent To Third Parties With Treatment Per Area - Facility Or Plant Located In Areas Of Water Stress Domain9 - Previous Year": "0",
    "Water Discharge To Others Per Area - Facility Or Plant Located In Areas Of Water Stress Domain9 - Previous Year":
        "{Total Water Discharged In Kilolitres Per Area - Facility Or Plant Located In Areas Of Water Stress Domain9 - Previous Year} - {Water Discharge To Surface Water Per Area - Facility Or Plant Located In Areas Of Water Stress Domain9 - Previous Year} - {Water Discharge To Groundwater Per Area - Facility Or Plant Located In Areas Of Water Stress Domain9 - Previous Year} - {Water Discharge To Seawater Per Area - Facility Or Plant Located In Areas Of Water Stress Domain9 - Previous Year} - {Water Discharge By Sent To Third Parties Per Area - Facility Or Plant Located In Areas Of Water Stress Domain9 - Previous Year}",
    "Water Discharge To Others Without Treatment Per Area - Facility Or Plant Located In Areas Of Water Stress Domain9 - Previous Year": "0",
    "Water Discharge To Others With Treatment Per Area - Facility Or Plant Located In Areas Of Water Stress Domain9 - Previous Year": "0",
    "Total Water Discharged In Kilolitres Per Area - Facility Or Plant Located In Areas Of Water Stress Domain9 - Previous Year": "0",
    "Water Withdrawal By Surface Water Per Area - Facility Or Plant Located In Areas Of Water Stress Domain10 - Previous Year": "0",
    "Water Withdrawal By Groundwater Per Area - Facility Or Plant Located In Areas Of Water Stress Domain10 - Previous Year": "0",
    "Water Withdrawal By Third Party Water Per Area - Facility Or Plant Located In Areas Of Water Stress Domain10 - Previous Year": "0",
    "Water Withdrawal By Seawater Or Desalinated Water Per Area - Facility Or Plant Located In Areas Of Water Stress Domain10 - Previous Year": "0",
    "Water Withdrawal By Others Per Area - Facility Or Plant Located In Areas Of Water Stress Domain10 - Previous Year": "0",
    "Total Volume Of Water Withdrawal Per Area - Facility Or Plant Located In Areas Of Water Stress Domain10 - Previous Year": "0",
    "Total Volume Of Water Consumption Per Area - Facility Or Plant Located In Areas Of Water Stress Domain10 - Previous Year": "0",
    "Water Intensity Per Rupee Of Turnover Per Area - Facility Or Plant Located In Areas Of Water Stress Domain10 - Previous Year": "0",
    "Waste Intensity The Relevant Metric May Be Selected By The Entity Per Area - Facility Or Plant Located In Areas Of Water Stress Domain10 - Previous Year":
        "{Total Waste Generated} / {Revenue From Operations}",
    "Water Discharge To Surface Water Per Area - Facility Or Plant Located In Areas Of Water Stress Domain10 - Previous Year":
        "{Total Water Discharged In Kilolitres Per Area - Facility Or Plant Located In Areas Of Water Stress Domain10 - Previous Year} - {Water Discharge To Groundwater Per Area - Facility Or Plant Located In Areas Of Water Stress Domain10 - Previous Year} - {Water Discharge To Seawater Per Area - Facility Or Plant Located In Areas Of Water Stress Domain10 - Previous Year} - {Water Discharge By Sent To Third Parties Per Area - Facility Or Plant Located In Areas Of Water Stress Domain10 - Previous Year} - {Water Discharge To Others Per Area - Facility Or Plant Located In Areas Of Water Stress Domain10 - Previous Year}",
    "Water Discharge To Surface Water With Out Treatment Per Area - Facility Or Plant Located In Areas Of Water Stress Domain10 - Previous Year":
        "{Water Discharge To Surface Water Per Area - Facility Or Plant Located In Areas Of Water Stress Domain10 - Previous Year} - {Water Discharge To Surface Water With Treatment Per Area - Facility Or Plant Located In Areas Of Water Stress Domain10 - Previous Year}",
    "Water Discharge To Surface Water With Treatment Per Area - Facility Or Plant Located In Areas Of Water Stress Domain10 - Previous Year":
        "{Water Discharge To Surface Water Per Area - Facility Or Plant Located In Areas Of Water Stress Domain10 - Previous Year} - {Water Discharge To Surface Water With Out Treatment Per Area - Facility Or Plant Located In Areas Of Water Stress Domain10 - Previous Year}",
    "Water Discharge To Groundwater Per Area - Facility Or Plant Located In Areas Of Water Stress Domain10 - Previous Year":
        "{Total Water Discharged In Kilolitres Per Area - Facility Or Plant Located In Areas Of Water Stress Domain10 - Previous Year} - {Water Discharge To Surface Water Per Area - Facility Or Plant Located In Areas Of Water Stress Domain10 - Previous Year} - {Water Discharge To Seawater Per Area - Facility Or Plant Located In Areas Of Water Stress Domain10 - Previous Year} - {Water Discharge By Sent To Third Parties Per Area - Facility Or Plant Located In Areas Of Water Stress Domain10 - Previous Year} - {Water Discharge To Others Per Area - Facility Or Plant Located In Areas Of Water Stress Domain10 - Previous Year}",
    "Water Discharge To Groundwater With Out Treatment Per Area - Facility Or Plant Located In Areas Of Water Stress Domain10 - Previous Year":
        "{Water Discharge To Groundwater Per Area - Facility Or Plant Located In Areas Of Water Stress Domain10 - Previous Year} - {Water Discharge To Groundwater With Treatment Per Area - Facility Or Plant Located In Areas Of Water Stress Domain10 - Previous Year}",
    "Water Discharge To Groundwater With Treatment Per Area - Facility Or Plant Located In Areas Of Water Stress Domain10 - Previous Year":
        "{Water Discharge To Groundwater Per Area - Facility Or Plant Located In Areas Of Water Stress Domain10 - Previous Year} - {Water Discharge To Groundwater With Out Treatment Per Area - Facility Or Plant Located In Areas Of Water Stress Domain10 - Previous Year}",
    "Water Discharge To Seawater Per Area - Facility Or Plant Located In Areas Of Water Stress Domain10 - Previous Year":
        "{Total Water Discharged In Kilolitres Per Area - Facility Or Plant Located In Areas Of Water Stress Domain10 - Previous Year} - {Water Discharge To Surface Water Per Area - Facility Or Plant Located In Areas Of Water Stress Domain10 - Previous Year} - {Water Discharge To Groundwater Per Area - Facility Or Plant Located In Areas Of Water Stress Domain10 - Previous Year} - {Water Discharge By Sent To Third Parties Per Area - Facility Or Plant Located In Areas Of Water Stress Domain10 - Previous Year} - {Water Discharge To Others Per Area - Facility Or Plant Located In Areas Of Water Stress Domain10 - Previous Year}",
    "Water Discharge To Seawater With Out Treatment Per Area - Facility Or Plant Located In Areas Of Water Stress Domain10 - Previous Year":
        "{Water Discharge To Seawater Per Area - Facility Or Plant Located In Areas Of Water Stress Domain10 - Previous Year} - {Water Discharge To Seawater With Treatment Per Area - Facility Or Plant Located In Areas Of Water Stress Domain10 - Previous Year}",
    "Water Discharge To Seawater With Treatment Per Area - Facility Or Plant Located In Areas Of Water Stress Domain10 - Previous Year":
        "{Water Discharge To Seawater Per Area - Facility Or Plant Located In Areas Of Water Stress Domain10 - Previous Year} - {Water Discharge To Seawater With Out Treatment Per Area - Facility Or Plant Located In Areas Of Water Stress Domain10 - Previous Year}",
    "Water Discharge By Sent To Third Parties Per Area - Facility Or Plant Located In Areas Of Water Stress Domain10 - Previous Year":
        "{Total Water Discharged In Kilolitres Per Area - Facility Or Plant Located In Areas Of Water Stress Domain10 - Previous Year} - {Water Discharge To Surface Water Per Area - Facility Or Plant Located In Areas Of Water Stress Domain10 - Previous Year} - {Water Discharge To Groundwater Per Area - Facility Or Plant Located In Areas Of Water Stress Domain10 - Previous Year} - {Water Discharge To Seawater Per Area - Facility Or Plant Located In Areas Of Water Stress Domain10 - Previous Year} - {Water Discharge To Others Per Area - Facility Or Plant Located In Areas Of Water Stress Domain10 - Previous Year}",
    "Water Discharge By Sent To Third Parties Without Treatment Per Area - Facility Or Plant Located In Areas Of Water Stress Domain10 - Previous Year": "0",
    "Water Discharge By Sent To Third Parties With Treatment Per Area - Facility Or Plant Located In Areas Of Water Stress Domain10 - Previous Year": "0",
    "Water Discharge To Others Per Area - Facility Or Plant Located In Areas Of Water Stress Domain10 - Previous Year":
        "{Total Water Discharged In Kilolitres Per Area - Facility Or Plant Located In Areas Of Water Stress Domain10 - Previous Year} - {Water Discharge To Surface Water Per Area - Facility Or Plant Located In Areas Of Water Stress Domain10 - Previous Year} - {Water Discharge To Groundwater Per Area - Facility Or Plant Located In Areas Of Water Stress Domain10 - Previous Year} - {Water Discharge To Seawater Per Area - Facility Or Plant Located In Areas Of Water Stress Domain10 - Previous Year} - {Water Discharge By Sent To Third Parties Per Area - Facility Or Plant Located In Areas Of Water Stress Domain10 - Previous Year}",
    "Water Discharge To Others Without Treatment Per Area - Facility Or Plant Located In Areas Of Water Stress Domain10 - Previous Year": "0",
    "Water Discharge To Others With Treatment Per Area - Facility Or Plant Located In Areas Of Water Stress Domain10 - Previous Year": "0",
    "Total Water Discharged In Kilolitres Per Area - Facility Or Plant Located In Areas Of Water Stress Domain10 - Previous Year": "0",
}

def extract_variables(formula):
    """Extracts all variables enclosed in {} from the formula string."""
    return re.findall(r'\{(.*?)\}', formula)
