# 🧠 Universal Document Data Extractor (LLM + Vision)

An **AI-powered Streamlit application** that extracts structured data from **PDFs and image-based documents** such as invoices, cheques, certificates, and reports — using **Large Language Models (LLMs)** and **Vision-Language Models**.

---

## Features

- Supports **PDFs and Image files (JPG, PNG, JPEG)**
- Choose between multiple **LLMs**:
  - GPT-4o, GPT-5 (OpenAI)
  - Offline Vision LLM via **Ollama LLaVA**
- Handles diverse document types:
  - Invoices / Bills  
  - Bank Cheques  
  - Identity Documents  
  - Reports / Certificates  
  - Generic text documents
- Dynamic **schema definition** (Pydantic-style)
- **Excel download** of extracted structured data
- **Offline + Online** modes supported
- Developer-friendly modular backend

---

## Project Structure

📂 universal_extractor/
├── app.py # Streamlit frontend
├── universal_extractor_backend.py # LLM + vision extraction logic
├── requirements.txt # Python dependencies
├── README.md # Project documentation
└── .env # API keys (optional)


---

## Setup Instructions

### Clone the Repository

git clone https://github.com/<your-username>/universal-document-extractor.git
cd universal-document-extractor

### Install Dependencies
pip install -r requirements.txt

### Run the App
streamlit run app.py

Configuration

Add your OpenAI API key in a .env file:

OPENAI_API_KEY=your_key_here


Or manually input it in the Streamlit sidebar.

### Supported Models
Mode	Model	Description
Online	GPT-4o / GPT-5	High-quality structured extraction
Offline	Ollama LLaVA	Vision-based local model for image docs
Example Use Cases
Document Type	Extracted Fields
Invoice / Bill	Product code, description, quantity, rate, amount, taxes
Bank Cheque	Account name, cheque no., amount, handwritten notes
ID Document	Name, DOB, ID number, nationality
Report / Certificate	Name, subject, score, issued date
Author

Aayush Adhikari
Senior/Lead AI & Data Science Engineer
Expertise in LLMs, MLOps, and AI Applications
🌐 LinkedIn
 | 📧 aceraayush@gmail.com

Future Enhancements

RAG-based document context retrieval

Reinforcement-learning feedback for better extraction

🏁 License

MIT License © 2025 Aayush Adhikari