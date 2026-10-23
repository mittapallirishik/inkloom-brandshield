
import streamlit as st

st.set_page_config(
    page_title="Inkloom BrandShield",
    page_icon="🛡️",
    layout="wide"
)

st.title("🛡️ Inkloom BrandShield")
st.caption("Evidence-to-Action Governance Loop")
st.write(
    "Review marketing content against approved brand rules "
    "and facts before publication."
)

# Fictional demo brand data
approved_facts = {
    "battery life": {
        "approved": "up to 12 hours",
        "source": "Demo Product Fact Sheet, section 1"
    },
    "warranty": {
        "approved": "2 years",
        "source": "Demo Product Fact Sheet, section 2"
    }
}

prohibited_terms = ["guaranteed cure", "100% risk-free"]
required_terms = ["Terms and conditions apply"]

draft = st.text_area(
    "Paste your marketing content",
    height=180,
    placeholder="Example: Enjoy up to 12 hours of battery life..."
)

if st.button("Analyse content", type="primary"):
    if not draft.strip():
        st.warning("Please enter some content first.")
    else:
        findings = []
        text = draft.lower()

        for term in prohibited_terms:
            if term in text:
                findings.append({
                    "risk": "High",
                    "issue": f"Prohibited term: {term}",
                    "evidence": "Demo brand rule: prohibited terms",
                    "suggestion": "Remove or revise this claim."
                })

        for term in required_terms:
            if term.lower() not in text:
                findings.append({
                    "risk": "Medium",
                    "issue": f"Missing required phrase: {term}",
                    "evidence": "Demo brand rule: required phrases",
                    "suggestion": f"Add '{term}' where appropriate."
                })

        for claim, fact in approved_facts.items():
            if claim in text:
                if fact["approved"] not in text:
                    findings.append({
                        "risk": "Review",
                        "issue": f"Check the claim about {claim}",
                        "evidence": (
                            f"Approved value: {fact['approved']}. "
                            f"Source: {fact['source']}"
                        ),
                        "suggestion": (
                            "Verify the exact claim against the "
                            "approved fact sheet."
                        )
                    })

        st.subheader("Review results")

        if not findings:
            st.success(
                "No configured rule violations detected. "
                "This does not mean the content is fully verified."
            )
        else:
            st.write(f"Found {len(findings)} item(s) to review.")

            for i, item in enumerate(findings, start=1):
                with st.expander(
                    f"{i}. [{item['risk']}] {item['issue']}",
                    expanded=True
                ):
                    st.write("**Evidence / rule:**", item["evidence"])
                    st.write("**Suggested action:**", item["suggestion"])

        st.info(
            "Prototype limitation: these are simple rule checks, "
            "not comprehensive AI or legal verification."
        )

st.divider()
st.caption(
    "Inkloom BrandShield · Prototype · "
    "Human review required before publication"
)
