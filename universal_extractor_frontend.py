import streamlit as st
import tempfile
import pandas as pd
import io
from dotenv import load_dotenv
from universal_extractor_backend import process_extraction

load_dotenv()

# ---------------------------
# Sidebar inputs
# ---------------------------
st.sidebar.title("Universal Document Extractor")

uploaded_file = st.sidebar.file_uploader("Upload File (PDF or Image)", type=["pdf", "jpg", "jpeg", "png"])

model_choice = st.sidebar.selectbox(
    "Select LLM Model",
    ["gpt-4o-mini", "gpt-4o", "gpt-5-mini", "gpt-5", "Vision LLM (Ollama LLaVA)"]
)

api_key = st.sidebar.text_input("Enter your OpenAI API Key", type="password")

page_number_to_extract_from = st.sidebar.number_input(
    "Start extraction from page number",
    min_value=1,
    value=1,
    step=1
)

no_of_pages = st.sidebar.selectbox(
    "Number of pages to extract",
    [1, 2, 3, 4, 5, 6, 7, 8, "ALL"]
)

# ---------------------------
# Document Type Dropdown
# ---------------------------
doc_type = st.sidebar.selectbox(
    "Select Document Type",
    [
        "Invoice / Bill",
        "Bank Cheque",
        "Identity Document",
        "Report / Certificate",
        "General Document"
    ]
)

# Auto-fill description prompt based on type
default_prompts = {
    "Invoice / Bill": "Extract invoice details such as item name, product code, quantity, unit rate, total, taxes, and invoice number.",
    "Bank Cheque": "Extract cheque details including account holder name, cheque number, bank name, amount, date, and handwritten text.",
    "Identity Document": "Extract fields like name, date of birth, ID number, nationality, and expiry date.",
    "Report / Certificate": "Extract title, issued date, recipient name, marks or grades, and remarks.",
    "General Document": "Extract all visible text and tabular information in structured JSON format."
}

description = st.sidebar.text_area("Prompt / Description", default_prompts[doc_type])

# ---------------------------
# User-defined fields
# ---------------------------
st.sidebar.subheader("Define Fields for Extraction")

if "fields" not in st.session_state:
    st.session_state["fields"] = []

with st.sidebar.form("field_form", clear_on_submit=True):
    field_name = st.text_input("Field Name")
    field_type = st.selectbox("Data Type", ["str", "int", "float", "bool"])
    field_required = st.checkbox("Compulsory?", value=True)
    field_desc = st.text_area("Field Description", height=80)
    field_example = st.text_input("Example Value(s) (comma separated)")
    add_field = st.form_submit_button("➕ Add Field")

if add_field and field_name:
    examples = [ex.strip() for ex in field_example.split(",") if ex.strip()] if field_example else []
    st.session_state.fields.append({
        "name": field_name,
        "type": field_type,
        "required": field_required,
        "description": field_desc,
        "examples": examples
    })

if st.session_state.fields:
    st.sidebar.write("### Fields Added")
    for idx, f in enumerate(st.session_state.fields):
        examples_str = f" Examples: {', '.join(f['examples'])}" if f['examples'] else ""
        st.sidebar.write(f"{idx+1}. {f['name']} ({f['type']}) - {'Required' if f['required'] else 'Optional'}{examples_str}")
        col1, col2 = st.sidebar.columns(2)
        if col1.button(f"✏️ Edit {idx+1}"):
            st.session_state.edit_index = idx
        if col2.button(f"🗑️ Delete {idx+1}"):
            st.session_state.fields.pop(idx)
            st.rerun()

if "edit_index" in st.session_state:
    edit_idx = st.session_state.edit_index
    field_to_edit = st.session_state.fields[edit_idx]
    with st.sidebar.form("edit_field_form", clear_on_submit=True):
        new_name = st.text_input("Field Name", field_to_edit["name"])
        new_type = st.selectbox("Data Type", ["str", "int", "float", "bool"],
                                index=["str", "int", "float", "bool"].index(field_to_edit["type"]))
        new_required = st.checkbox("Compulsory?", value=field_to_edit["required"])
        new_desc = st.text_area("Field Description", value=field_to_edit["description"], height=80)
        new_example = st.text_input("Example Value(s)", value=", ".join(field_to_edit["examples"]))
        save_changes = st.form_submit_button("💾 Save Changes")

    if save_changes:
        new_examples = [ex.strip() for ex in new_example.split(",") if ex.strip()]
        st.session_state.fields[edit_idx] = {
            "name": new_name,
            "type": new_type,
            "required": new_required,
            "description": new_desc,
            "examples": new_examples
        }
        del st.session_state.edit_index
        st.rerun()

run_extraction = st.sidebar.button("Submit & Run Extraction")

# ---------------------------
# Main App Area
# ---------------------------
st.title("AI-Powered Universal Document Extractor")
st.caption("Extract structured information from PDFs, invoices, cheques, and documents using LLMs and vision models.")

if uploaded_file is not None:
    with tempfile.NamedTemporaryFile(delete=False, suffix=f".{uploaded_file.name.split('.')[-1]}") as tmp_file:
        tmp_file.write(uploaded_file.read())
        file_path = tmp_file.name
    st.success(f"Uploaded file saved to: {file_path}")

    st.subheader("Schema Definition (Dynamic Pydantic-like Schema)")
    if not st.session_state.fields:
        st.info("No fields defined yet.")
    else:
        for f in st.session_state.fields:
            st.markdown(f"**{f['name']}** ({f['type']}) - {'Required' if f['required'] else 'Optional'}")
            st.caption(f"Description: {f['description']}")
            if f["examples"]:
                st.caption(f"Examples: {', '.join(f['examples'])}")

    if run_extraction:
        if not api_key:
            st.error("Please provide an API key in the sidebar.")
        else:
            with st.spinner("Running AI extraction..."):
                result = process_extraction(
                    file_path,
                    st.session_state.fields,
                    api_key,
                    model_choice,
                    description,
                    no_of_pages,
                    start_page=page_number_to_extract_from
                )

            df = pd.DataFrame(result["raw_output"])
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine="openpyxl") as writer:
                df.to_excel(writer, index=False, sheet_name="ExtractedData")

            st.subheader("Extracted Data Table")
            st.dataframe(df)

            st.download_button(
                label="Download as Excel",
                data=output.getvalue(),
                file_name="extracted_data.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

else:
    st.warning("Please upload a PDF or image file to begin.")
