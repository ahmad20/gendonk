import os
import tempfile
import streamlit as st
import pandas as pd
import json

def create_temp_file(suffix):
    """Create a temporary file and return its path."""
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    return temp_file.name

def convert_excel_to_csv(file, sheet_name, output_file):
    """Convert an Excel sheet to a CSV file."""
    df = pd.read_excel(file, sheet_name=sheet_name)
    df.to_csv(output_file, index=False)

def convert_csv_to_jsonl(file, question_column, answer_column, output_file):
    """Convert a CSV file to a JSONL file."""
    df = pd.read_csv(file)

    with open(output_file, "w") as f:
        for _, row in df.iterrows():
            question = row.get(question_column, None)
            answer = row.get(answer_column, None)

            if pd.isna(question) or pd.isna(answer):
                continue

            messages = [
                {"role": "system", "content": os.getenv("GENDONK_SYSTEM_PROMPT")},
                {"role": "user", "content": str(question)},
                {"role": "assistant", "content": str(answer)}
            ]
            f.write(json.dumps({"messages": messages}) + "\n")

def serve_file(file_path, download_label):
    """Serve a file as a downloadable link in Streamlit."""
    with open(file_path, "rb") as file:
        file_data = file.read()
    st.download_button(
        label=download_label,
        data=file_data,
        file_name=os.path.basename(file_path),
        mime="application/octet-stream"
    )

import time
import streamlit as st
from openai import OpenAI

def fine_tune_model(client: OpenAI, file):
    """Fine-tune the OpenAI model with a JSONL file and track the job status."""
    # Upload the file for fine-tuning
    file_response = client.files.create(
        file=open(file, "rb"),
        purpose="fine-tune"
    )

    # Create the fine-tuning job
    fine_tune_job = client.fine_tuning.jobs.create(
        training_file=file_response.id,
        model="gpt-4o-mini-2024-07-18"
    )

    job_id = fine_tune_job.id
    st.info(f"Fine-tuning job started. Job ID: {job_id}")
    
    # Poll the job status until completion
    with st.spinner("Please wait..."):
        while True:
            job_status = client.fine_tuning.jobs.retrieve(job_id)
            status = job_status.status

            if status == "succeeded":
                st.success("Fine-tuning completed successfully!")
                checkpoint_model = job_status.fine_tuned_model
                # Save model name to a file
                with open("checkpoint_model", "w") as f:
                    f.write(checkpoint_model)
                    st.write(f"Checkpoint Model: {checkpoint_model}")
                break
            elif status == "cancelled":
                st.error("Fine-tuning job was cancelled!")
                break
            elif status == "failed":
                error_message = job_status.error.message
                st.error(f"Fine-tuning failed! Error: {error_message}")
                break
            else:
                time.sleep(10)


def index(client):
    st.header("Input")
    st.write("Upload your Excel or CSV file with questions and answers.")

    uploaded_file = st.file_uploader("Choose a file", type=["xlsx", "csv"])

    if uploaded_file is not None:
        if str(uploaded_file.name).endswith("xlsx"):
            xls = pd.ExcelFile(uploaded_file)
            sheet_names = xls.sheet_names
            sheet_name = st.selectbox("Select Sheet", sheet_names)

            if sheet_name:
                df = pd.read_excel(uploaded_file, sheet_name=sheet_name)
                st.write("Preview:")
                st.dataframe(df.head())

                columns = df.columns.tolist()
                question_column = st.selectbox("Select Question Column", columns)
                answer_column = st.selectbox("Select Answer Column", columns)

                if st.button("Convert and Fine-tune"):
                    csv_file = create_temp_file(".csv")
                    jsonl_file = create_temp_file(".jsonl")

                    convert_excel_to_csv(uploaded_file, sheet_name, csv_file)
                    convert_csv_to_jsonl(csv_file, question_column, answer_column, jsonl_file)

                    success = st.success("Conversion successful!")
                    time.sleep(1)
                    success.empty()

                    fine_tune_model(client, jsonl_file)

        elif str(uploaded_file.name).endswith("csv"):
            df = pd.read_csv(uploaded_file)
            st.write("Preview:")
            st.dataframe(df.head())

            columns = df.columns.tolist()
            question_column = st.selectbox("Select Question Column", columns)
            answer_column = st.selectbox("Select Answer Column", columns)

            if st.button("Convert and Fine-tune"):
                jsonl_file = create_temp_file(".jsonl")
                convert_csv_to_jsonl(uploaded_file.name, question_column, answer_column, jsonl_file)

                st.success("Conversion successful!")
                fine_tune_model(client, jsonl_file)