import json
from typing import List, Dict, Any, Optional
from pypdf import PdfReader
from pydantic import BaseModel, Field, create_model
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
import os

# Load environment variables (e.g., OPENAI_API_KEY)
load_dotenv()


# ---------------------------
# 1. Build Dynamic Pydantic Schema
# ---------------------------
def build_pydantic_model(fields: List[Dict[str, Any]], model_name: str = "UserDefinedModel"):
    """
    Dynamically builds a Pydantic model from user-specified schema fields.
    """
    annotations = {}
    type_map = {"str": str, "int": int, "float": float, "bool": bool}

    for f in fields:
        dtype = type_map.get(f.get("type", "str"), str)
        required = f.get("required", False)
        default_value = ... if required else None
        final_type = dtype if required else Optional[dtype]

        field_args = {}
        if f.get("description"):
            field_args["description"] = f["description"]
        if f.get("examples"):
            field_args["examples"] = f["examples"]

        annotations[f["name"]] = (final_type, Field(default_value, **field_args))

    DynamicModel = create_model(model_name, **annotations)

    class BatchWrapper(BaseModel):
        items: List[DynamicModel]

    return DynamicModel, BatchWrapper


# ---------------------------
# 2. Extract Text from PDF
# ---------------------------
def extract_text_from_pdf(pdf_path: str, num_pages: Any = "ALL", start_page: int = 1) -> List[str]:
    """
    Extract text from PDF using pypdf with layout preservation.
    """
    reader = PdfReader(pdf_path)
    total_pages = len(reader.pages)

    start_idx = max(0, start_page - 1)
    end_idx = total_pages if num_pages == "ALL" else min(start_idx + int(num_pages), total_pages)

    page_texts = []
    for pg in range(start_idx, end_idx):
        page = reader.pages[pg]
        try:
            page_text = page.extract_text(extraction_mode="layout")
        except TypeError:
            page_text = page.extract_text() or ""
        page_texts.append(page_text or "")

    if not page_texts:
        raise ValueError("No text could be extracted from the PDF.")
    return page_texts


# ---------------------------
# 3. Run LLM Extraction with Structured Output
# ---------------------------
def run_llm_extraction(
    api_key: str,
    model_choice: str,
    description: str,
    page_texts: List[str],
    BatchWrapper: BaseModel
):
    """
    Uses OpenAI's structured output feature to extract fields from PDF text.
    """
    llm = ChatOpenAI(model=model_choice, api_key=api_key)
    structured_llm = llm.with_structured_output(BatchWrapper)
    extracted_data = []

    for i, page_text in enumerate(page_texts):
        print(f"🧩 Processing page {i+1}/{len(page_texts)}")

        system_prompt = f"""
You are an intelligent data extraction system. Extract structured data from the given PDF text based on the schema below.

### SCHEMA ###
{BatchWrapper.schema_json(indent=2)}

### RULES ###
1. Treat each record/item as a separate entity.
2. Do NOT mix data between items.
3. If a field is missing, leave it empty or null.
4. Return results strictly in JSON format.
"""
        if description:
            system_prompt += f"\nAdditional context: {description}"

        user_prompt = f"""Extract data from this page:\n\n{page_text}\n"""

        try:
            result = structured_llm.invoke([
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ])
            page_data = [item.dict() for item in result.items]
            extracted_data.extend(page_data)

        except Exception as e:
            print(f"⚠️ LLM extraction failed on page {i+1}: {e}")
            # Fallback to raw text in JSON format
            extracted_data.append({
                "page": i + 1,
                "raw_text": page_text,
                "error": str(e)
            })

    return extracted_data


# ---------------------------
# 4. Complete PDF Extraction Pipeline
# ---------------------------
def process_extraction(
    pdf_path: str,
    fields: List[Dict[str, Any]],
    api_key: str,
    model_choice: str,
    description: str,
    num_pages: Any = "ALL",
    start_page: int = 1
):
    """
    Full pipeline: schema → text extraction → LLM structured output → result.
    """
    try:
        # Step 1: Dynamic model build
        DynamicModel, BatchWrapper = build_pydantic_model(fields)

        # Step 2: Extract text
        page_texts = extract_text_from_pdf(pdf_path, num_pages, start_page)
        print(f"✅ Extracted text from {len(page_texts)} pages.")

        # Step 3: Run structured LLM extraction
        results = run_llm_extraction(api_key, model_choice, description, page_texts, BatchWrapper)

        # Step 4: Always return JSON
        json_output = json.dumps(results, indent=2, ensure_ascii=False)

        return {
            "success": True,
            "schema": BatchWrapper.schema(),
            "json_output": json_output,
            "pages_processed": len(page_texts),
            "total_items": len(results)
        }

    except Exception as e:
        print(f"❌ Extraction failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "schema": None,
            "json_output": json.dumps({"error": str(e)}, indent=2),
            "pages_processed": 0,
            "total_items": 0
        }


# ---------------------------
# 5. Optional Debug Utility
# ---------------------------
def test_extraction_only(pdf_path: str, num_pages: Any = "ALL", start_page: int = 1):
    """
    Simple utility to preview PDF text before applying LLM extraction.
    """
    return extract_text_from_pdf(pdf_path, num_pages, start_page)


# ---------------------------
# Example Run (for testing)
# ---------------------------
if __name__ == "__main__":
    pdf_path = "sample_invoice.pdf"
    api_key = os.getenv("OPENAI_API_KEY")
    model_choice = "gpt-4o-mini"
    description = "Extract product details, quantity, rate, and amount from this invoice."

    fields = [
        {"name": "product_name", "type": "str", "required": True, "description": "Name or description of the product"},
        {"name": "product_code", "type": "str", "required": False},
        {"name": "quantity", "type": "float", "required": False},
        {"name": "rate", "type": "float", "required": False},
        {"name": "amount", "type": "float", "required": False}
    ]

    result = process_extraction(pdf_path, fields, api_key, model_choice, description)
    print("\n🧾 Final JSON Output:\n", result["json_output"])
