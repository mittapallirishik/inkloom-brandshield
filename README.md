# inkloom-brandshield
Evidence-to-Action Governance Loop for marketing content review and brand compliance.
# Inkloom BrandShield 🛡️

**An Evidence-to-Action Governance Loop for marketing content.**

Inkloom BrandShield is a prototype designed to help reviewers identify potential brand-compliance issues in marketing content using approved brand facts and configurable rules.

## Problem

Marketing content can contain unsupported product claims, prohibited terminology, or missing required disclaimers. Reviewing these issues manually can be inconsistent and time-consuming.

## Our Solution

BrandShield provides a simple review workflow that:

- Maintains a library of approved brand facts and source references.
- Flags configured prohibited terms.
- Checks for required phrases.
- Identifies claims that may need verification against approved facts.
- Supports human reviewer decisions and notes.
- Stores approved facts and review history in local JSON files.

## Technology Stack

- Python
- Streamlit
- JSON-based local storage

## Run Locally

1. Install Python.
2. Download or clone this repository.
3. Install the dependencies:

   ```bash
   pip install -r requirements.txt
   ```

4. Start the application:

   ```bash
   streamlit run app.py
   ```

5. Open the local URL shown in your terminal.

## Current Limitations

- The prototype uses rule-based checks, not a trained AI model.
- Claim matching is basic and does not establish whether a claim is true or false.
- Demo product facts are fictional and must not be treated as real product evidence.
- Local JSON storage is not a shared database.
- Human verification is required before approving marketing content.

## Project Status

Working prototype under development. Planned improvements include stronger claim verification, automated tests, improved review workflows, and deployment options.

## Responsible Use

BrandShield provides decision support. Reviewers should verify claims against authentic sources before making final decisions.
