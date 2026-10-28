import json
import os
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path

import streamlit as st

st.set_page_config(page_title="Inkloom BrandShield", page_icon="🛡️", layout="wide")
APP_DIR = Path(__file__).resolve().parent
FACTS_FILE = APP_DIR / "brand_facts.json"
HISTORY_FILE = APP_DIR / "review_history.json"
DEFAULT_FACTS = [
    {"claim": "battery life", "value": "up to 12 hours", "source": "Demo Product Fact Sheet, section 1"},
    {"claim": "warranty", "value": "2 years", "source": "Demo Product Fact Sheet, section 2"},
]
PROHIBITED = ["guaranteed cure", "100% risk-free"]
REQUIRED = ["Terms and conditions apply"]
SAMPLE_DRAFTS = {
    "Clean sample": "Our demo product offers up to 12 hours of battery life and a 2 years warranty. Terms and conditions apply.",
    "Needs review": "Our product offers 20 hours of battery life and a lifetime warranty. Terms and conditions apply.",
    "High-risk wording": "This product is a guaranteed cure and is 100% risk-free.",
    "Missing disclaimer": "Enjoy up to 12 hours of battery life with our demo product.",
}


def utc_timestamp():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def valid_fact_list(data):
    return isinstance(data, list) and all(
        isinstance(item, dict) and all(isinstance(item.get(k), str) and item[k].strip() for k in ("claim", "value", "source"))
        for item in data
    )


def valid_history_list(data):
    return isinstance(data, list) and all(
        isinstance(item, dict)
        and isinstance(item.get("draft", ""), str)
        and isinstance(item.get("findings", []), list)
        and isinstance(item.get("decisions", {}), dict)
        for item in data
    )


def save_json(path, data):
    """Write to a temporary file in the same directory, then replace atomically."""
    temp_name = None
    try:
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=str(path.parent), prefix=path.name + ".", suffix=".tmp", delete=False) as file:
            temp_name = file.name
            json.dump(data, file, indent=2, ensure_ascii=False)
            file.write("\n")
            file.flush()
            os.fsync(file.fileno())
        Path(temp_name).replace(path)
    finally:
        if temp_name and Path(temp_name).exists():
            try:
                Path(temp_name).unlink()
            except OSError:
                pass


def load_json(path, default, validator):
    if not path.exists():
        try:
            save_json(path, default)
        except OSError:
            st.warning(f"{path.name} could not be created. Default data is available for this session, but changes may not persist.")
        return json.loads(json.dumps(default))
    try:
        with path.open("r", encoding="utf-8") as file:
            data = json.load(file)
        if not validator(data):
            raise ValueError("Unexpected JSON structure")
        return data
    except (json.JSONDecodeError, OSError, ValueError) as error:
        st.warning(f"{path.name} could not be loaded safely ({error}). Defaults will be used for this session. Back up important data before replacing the file.")
        return json.loads(json.dumps(default))


def analyse_draft(draft, facts):
    """Transparent rule checks; these do not establish factual truth."""
    findings = []
    text = draft.casefold()
    for term in PROHIBITED:
        if term.casefold() in text:
            findings.append({"risk": "High", "issue": f"Prohibited term: {term}", "evidence": "Brand rule: prohibited terminology", "action": "Remove or revise this wording."})
    for term in REQUIRED:
        if term.casefold() not in text:
            findings.append({"risk": "Medium", "issue": f"Missing phrase: {term}", "evidence": "Brand rule: required phrase", "action": f"Add '{term}' where appropriate."})
    for fact in facts:
        claim, value = fact["claim"].strip(), fact["value"].strip()
        if claim and claim.casefold() in text and value.casefold() not in text:
            findings.append({"risk": "Review", "issue": f"Verify claim about {claim}", "evidence": f"Approved value: {value}. Source: {fact['source']}", "action": "Check the statement against the source. This flags a possible mismatch; it does not prove the claim is false."})
    return findings


def risk_radar(findings):
    """Return a transparent rule-based indicator, not a probability of harm."""
    weights = {"High": 50, "Medium": 25, "Review": 15}
    raw_score = sum(weights.get(item.get("risk", ""), 0) for item in findings)
    score = min(100, raw_score)
    if score >= 70:
        label = "HIGH"
        explanation = "Prioritise the flagged issues before publication."
    elif score >= 30:
        label = "MODERATE"
        explanation = "Review the flagged issues and resolve applicable rules."
    elif score > 0:
        label = "LOW — REVIEW NEEDED"
        explanation = "A potential issue was detected; check the evidence and context."
    else:
        label = "NO CONFIGURED FLAGS"
        explanation = "No configured rules triggered; this is not proof of full compliance."
    breakdown = {
        "High-severity flags": sum(1 for item in findings if item.get("risk") == "High"),
        "Medium-severity flags": sum(1 for item in findings if item.get("risk") == "Medium"),
        "Fact checks to verify": sum(1 for item in findings if item.get("risk") == "Review"),
    }
    return {"score": score, "label": label, "explanation": explanation, "breakdown": breakdown}


def clear_draft_state():
    """Clear widget state in a callback before Streamlit redraws the page."""
    for key, value in {"draft_input": "", "draft": "", "findings": [], "decisions": {}, "analysis_complete": False, "current_review_id": None, "saved_review_id": None}.items():
        st.session_state[key] = value


def run_self_tests():
    tests = [
        ("Prohibited phrase detected", "This is a guaranteed cure. Terms and conditions apply.", lambda f: any(x["risk"] == "High" and "guaranteed cure" in x["issue"] for x in f)),
        ("Missing disclaimer detected", "Our product has a useful feature.", lambda f: any("Missing phrase" in x["issue"] for x in f)),
        ("Approved battery value accepted", "Battery life is up to 12 hours. Terms and conditions apply.", lambda f: not any("Verify claim about battery life" in x["issue"] for x in f)),
        ("Mismatched battery value flagged", "Battery life is 20 hours. Terms and conditions apply.", lambda f: any("Verify claim about battery life" in x["issue"] for x in f)),
        ("Clean sample has no configured findings", SAMPLE_DRAFTS["Clean sample"], lambda f: len(f) == 0),
    ]
    results = []
    for name, draft, check in tests:
        try:
            passed = bool(check(analyse_draft(draft, DEFAULT_FACTS)))
            results.append({"Test": name, "Result": "PASS" if passed else "FAIL", "Details": "Passed" if passed else "Expected result not found"})
        except Exception as error:
            results.append({"Test": name, "Result": "FAIL", "Details": str(error)})
    return results


if "facts" not in st.session_state:
    st.session_state.facts = load_json(FACTS_FILE, DEFAULT_FACTS, valid_fact_list)
if "review_history" not in st.session_state:
    st.session_state.review_history = load_json(HISTORY_FILE, [], valid_history_list)
for key, default in {"findings": [], "decisions": {}, "draft": "", "analysis_complete": False, "current_review_id": None, "saved_review_id": None, "draft_input": ""}.items():
    if key not in st.session_state:
        st.session_state[key] = default

st.title("🛡️ Inkloom BrandShield")
st.caption("Evidence-to-Action Governance Loop")
st.info("Prototype notice: checks are rule-based. Claim alerts request human verification and do not prove a claim is false. Demo facts are fictional.")
review_tab, memory_tab, history_tab, testing_tab = st.tabs(["Content Review", "Brand Memory", "Review History", "Self-tests"])

with review_tab:
    st.subheader("🔍 Analyse Marketing Content")
    st.write("Choose a sample to explore the app, or paste your own draft.")
    sample_col, load_col = st.columns([3, 1])
    with sample_col:
        selected_sample = st.selectbox("Demo scenario", ["Choose a sample…"] + list(SAMPLE_DRAFTS), key="sample_choice")
    with load_col:
        st.write("")
        st.write("")
        if st.button("Load sample", use_container_width=True):
            if selected_sample == "Choose a sample…":
                st.warning("Choose a demo scenario first.")
            else:
                st.session_state.draft_input = SAMPLE_DRAFTS[selected_sample]
                st.session_state.draft = st.session_state.draft_input
                st.session_state.findings = []
                st.session_state.decisions = {}
                st.session_state.analysis_complete = False
                st.session_state.current_review_id = None
                st.session_state.saved_review_id = None
                st.rerun()
    draft = st.text_area("Marketing draft", key="draft_input", height=180, placeholder="Paste a product description, advert, or social post…")
    analyse_col, clear_col = st.columns(2)
    with analyse_col:
        analyse_clicked = st.button("Analyse draft", type="primary", use_container_width=True)
    with clear_col:
        st.button("Clear draft", use_container_width=True, on_click=clear_draft_state)
    if analyse_clicked:
        cleaned = draft.strip()
        st.session_state.draft = cleaned
        st.session_state.decisions = {}
        st.session_state.saved_review_id = None
        if not cleaned:
            st.session_state.findings = []
            st.session_state.analysis_complete = False
            st.session_state.current_review_id = None
            st.error("Enter a draft or load a sample before analysing.")
        else:
            st.session_state.findings = analyse_draft(cleaned, st.session_state.facts)
            st.session_state.analysis_complete = True
            st.session_state.current_review_id = str(uuid.uuid4())
            st.success("Analysis complete. Review each finding before saving.")
    if st.session_state.analysis_complete:
        findings = st.session_state.findings
        radar = risk_radar(findings)
        st.subheader("🛡️ BrandShield Risk Radar")
        radar_col, details_col = st.columns([1, 2])
        with radar_col:
            st.metric("Rule-based risk indicator", f"{radar['score']}/100", radar["label"])
            st.progress(radar["score"] / 100)
        with details_col:
            st.write(radar["explanation"])
            st.write("**What contributed to this indicator**")
            st.write(f"- High-severity flags: {radar['breakdown']['High-severity flags']}")
            st.write(f"- Medium-severity flags: {radar['breakdown']['Medium-severity flags']}")
            st.write(f"- Fact checks to verify: {radar['breakdown']['Fact checks to verify']}")
        st.caption("Score is a transparent prototype heuristic (High +50, Medium +25, Review +15; capped at 100). It is not an AI confidence score or a probability of legal, factual, or brand harm. Human review is required.")
        if not findings:
            st.success("No configured issues detected. This does not prove that the content is fully accurate or compliant.")
        else:
            st.write(f"**{len(findings)} finding(s) to review**")
            for i, item in enumerate(findings):
                with st.container(border=True):
                    st.markdown(f"**{item['risk']} — {item['issue']}**")
                    st.write("Evidence:", item["evidence"])
                    st.write("Suggested action:", item["action"])
                    decision = st.selectbox("Reviewer decision", ["Pending", "Accept suggestion", "Request changes", "Override finding"], key=f"decision_{st.session_state.current_review_id}_{i}")
                    note = st.text_input("Reviewer note", key=f"note_{st.session_state.current_review_id}_{i}")
                    st.session_state.decisions[str(i)] = {"decision": decision, "note": note.strip()}
        if st.session_state.saved_review_id == st.session_state.current_review_id:
            st.success("This review has already been saved. Analyse again to create a new review.")
        elif st.button("Save review to history", type="primary"):
            review_id = st.session_state.current_review_id
            if not review_id:
                st.error("Analyse the draft again before saving.")
            else:
                review = {"review_id": review_id, "created_at_utc": utc_timestamp(), "draft": st.session_state.draft, "findings": st.session_state.findings, "decisions": dict(st.session_state.decisions), "summary": "No configured findings" if not st.session_state.findings else f"{len(st.session_state.findings)} finding(s)"}
                st.session_state.review_history.append(review)
                try:
                    save_json(HISTORY_FILE, st.session_state.review_history)
                    st.session_state.saved_review_id = review_id
                    st.success("Review saved with timestamp and unique ID.")
                except OSError as error:
                    st.session_state.review_history.pop()
                    st.error(f"Review could not be saved. Check file permissions or hosting storage. Details: {error}")

with memory_tab:
    st.subheader("📚 Approved Brand Facts")
    st.write("Add facts from trusted, approved sources. Demo entries are fictional. Facts are stored in a local JSON file where the host permits writes.")
    with st.form("add_fact_form", clear_on_submit=True):
        claim = st.text_input("Claim or topic", placeholder="e.g. charging time")
        value = st.text_input("Approved value", placeholder="e.g. approximately 2 hours")
        source = st.text_input("Source reference", placeholder="e.g. Product Fact Sheet, section 3")
        submitted = st.form_submit_button("Add approved fact")
    if submitted:
        if not all(x.strip() for x in (claim, value, source)):
            st.error("Complete all three fields.")
        else:
            new_fact = {"claim": claim.strip(), "value": value.strip(), "source": source.strip()}
            if any(f["claim"].casefold() == new_fact["claim"].casefold() for f in st.session_state.facts):
                st.error("A fact with this claim/topic already exists. Delete the existing fact first.")
            else:
                candidate = st.session_state.facts + [new_fact]
                try:
                    save_json(FACTS_FILE, candidate)
                    st.session_state.facts = candidate
                    st.success("Fact added and saved.")
                except OSError as error:
                    st.error(f"Could not save the fact: {error}")
    if not st.session_state.facts:
        st.info("No approved facts yet. Add one above.")
    else:
        for i, fact in enumerate(st.session_state.facts):
            with st.container(border=True):
                st.markdown(f"**{fact['claim']}**")
                st.write("Approved value:", fact["value"])
                st.caption("Source: " + fact["source"])
                if st.button("Delete fact", key=f"delete_fact_{i}"):
                    candidate = [f for j, f in enumerate(st.session_state.facts) if j != i]
                    try:
                        save_json(FACTS_FILE, candidate)
                        st.session_state.facts = candidate
                        st.success("Fact deleted.")
                    except OSError as error:
                        st.error(f"Could not save deletion: {error}")
                    st.rerun()
    st.download_button("Download facts as JSON", data=json.dumps(st.session_state.facts, indent=2, ensure_ascii=False), file_name="inkloom_brand_facts.json", mime="application/json")
    st.caption(f"Local storage file: {FACTS_FILE.name}")

with history_tab:
    st.subheader("📝 Review History")
    if not st.session_state.review_history:
        st.info("No reviews saved yet. Analyse a draft and save a review first.")
    else:
        st.caption(f"{len(st.session_state.review_history)} saved review(s)")
        for index, review in enumerate(reversed(st.session_state.review_history), start=1):
            created = review.get("created_at_utc", "Timestamp unavailable")
            with st.expander(f"Review {index} · {created}"):
                st.caption(f"ID: {review.get('review_id', 'Legacy record')}")
                st.write("Draft:", review.get("draft", ""))
                st.write("Summary:", review.get("summary", "Not recorded"))
                for finding in review.get("findings", []):
                    if isinstance(finding, dict):
                        st.write(f"- {finding.get('risk', 'Unknown')}: {finding.get('issue', '')}")
                st.write("Reviewer decisions and notes")
                st.json(review.get("decisions", {}))
    st.download_button("Download review history as JSON", data=json.dumps(st.session_state.review_history, indent=2, ensure_ascii=False), file_name="inkloom_review_history.json", mime="application/json")
    st.caption("Local JSON files may not persist across some hosted restarts or redeployments. Confirm persistence on the target host.")

with testing_tab:
    st.subheader("🧪 Repeatable core checks")
    st.write("These checks cover core analysis logic; they do not replace full browser and deployment testing.")
    if st.button("Run self-tests", type="primary"):
        st.session_state.test_results = run_self_tests()
    if "test_results" in st.session_state:
        st.dataframe(st.session_state.test_results, use_container_width=True, hide_index=True)
        passed = sum(r["Result"] == "PASS" for r in st.session_state.test_results)
        total = len(st.session_state.test_results)
        if passed == total:
            st.success(f"All {passed}/{total} built-in tests passed.")
        else:
            st.error(f"{passed}/{total} tests passed. Investigate failures before submission.")

st.divider()
st.caption("Inkloom BrandShield prototype • Rule-based checks • Human verification required • Demo facts are fictional  • Local JSON persistence depends on the deployment environment")
