import os
import tempfile
import pandas as pd
import json
import time
import argparse
import signal
from openai import OpenAI

# Global variable to track fine-tune job ID
current_job_id = None


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


def fine_tune_model(client: OpenAI, file):
    """Fine-tune the OpenAI model with a JSONL file and track the job status."""
    global current_job_id

    # Upload the file for fine-tuning
    file_response = client.files.create(
        file=open(file, "rb"),
        purpose="fine-tune"
    )

    # Create the fine-tuning job
    fine_tune_job = client.fine_tuning.jobs.create(
        training_file=file_response.id,
        model="gpt-4o-2024-08-06"
    )

    current_job_id = fine_tune_job.id
    print(f"Fine-tuning job started. Job ID: {current_job_id}")

    # Poll the job status until completion
    try:
        while True:
            job_status = client.fine_tuning.jobs.retrieve(current_job_id)
            status = job_status.status

            if status == "succeeded":
                print("Fine-tuning completed successfully!")
                break
            elif status == "cancelled":
                print("Fine-tuning job was cancelled!")
                break
            elif status == "failed":
                error_message = job_status.error.message
                print(f"Fine-tuning failed! Error: {error_message}")
                break
            else:
                time.sleep(10)
    except KeyboardInterrupt:
        print("\nCancellation requested by user.")
        client.fine_tuning.jobs.cancel(current_job_id)
        print("Fine-tuning job cancellation requested!")


def handle_exit_signal(signal_number, frame):
    """Handle user interrupt signal (Ctrl+C)."""
    global current_job_id
    if current_job_id:
        print("\nInterrupt detected. Sending cancellation request to OpenAI...")
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        client.fine_tuning.jobs.cancel(current_job_id)
        print("Fine-tuning job cancelled.")
    exit(0)


def main():
    parser = argparse.ArgumentParser(description="Convert an Excel or CSV file to JSONL format and fine-tune a model.")
    parser.add_argument("filename", type=str, help="Input file name (Excel or CSV)")
    parser.add_argument("sheetname", type=str, default=None, help="Sheet name in Excel file (optional)")
    parser.add_argument("question_column", type=str, help="Column name for questions")
    parser.add_argument("answer_column", type=str, help="Column name for answers")
    # parser.add_argument("output_filename", type=str, default="output.jsonl", help="Output file name (JSONL)")

    args = parser.parse_args()

    # Load environment variables
    import dotenv
    dotenv.load_dotenv()

    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    # Register the signal handler for Ctrl+C
    signal.signal(signal.SIGINT, handle_exit_signal)

    # Process the file
    if args.filename.endswith("xlsx"):
        if args.sheetname:
            csv_file = create_temp_file(".csv")
            jsonl_file = create_temp_file(".jsonl")

            convert_excel_to_csv(args.filename, args.sheetname, csv_file)
            convert_csv_to_jsonl(csv_file, args.question_column, args.answer_column, jsonl_file)

            fine_tune_model(client, jsonl_file)
        else:
            print("Error: Sheet name is required for Excel files.")
    elif args.filename.endswith("csv"):
        jsonl_file = create_temp_file(".jsonl")
        convert_csv_to_jsonl(args.filename, args.question_column, args.answer_column, jsonl_file)

        fine_tune_model(client, jsonl_file)
    else:
        print("Error: Unsupported file format. Only Excel (.xlsx) and CSV files are supported.")


if __name__ == "__main__":
    print("Starting data generator...")
    main()
    # python data_generator.py "Generative RKS.xlsx" "ready" "Input_Requirements" "Output_Documents" output.jsonl
