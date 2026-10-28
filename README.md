# Inkloom BrandShield

**Evidence-to-Action Governance Loop**

Inkloom BrandShield is a prototype tool for reviewing marketing content against configurable brand rules and approved product facts.

## Features

- Guided sample marketing drafts
- Detection of configured prohibited phrases
- Checks for required disclaimers
- Approved-fact mismatch alerts for human verification
- Explainable, rule-based Risk Radar
- Reviewer decisions and notes
- Review history with timestamps and unique IDs
- JSON export for brand facts and review history
- Five built-in self-tests

## Technology

- Python
- Streamlit
- JSON-based local file storage

## Run locally

Install dependencies:

`pip install -r requirements.txt`

Start the app:

`streamlit run app.py`

## Limitations

Rule-based checks do not establish factual truth or full legal compliance. Risk Radar is a heuristic indicator, not a validated probability of harm. Local JSON storage may not persist across hosted restarts or redeployments.

## Author

MITTAPALLI RISHIK
BVRIT, Narsapur
MITTAPALLI RISHIK  
BVRIT, Narsapur
