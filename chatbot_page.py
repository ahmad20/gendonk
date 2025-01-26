import os
import streamlit as st
from openai import OpenAI

def get_latest_checkpoint_model(client:OpenAI) -> str:
    """Retrieve the last completed fine-tuning job and its checkpoint model."""
    try:
        # Fetch the list of fine-tuning jobs
        jobs = client.fine_tuning.jobs.list()
        
        # Sort jobs by created timestamp in descending order
        sorted_jobs = sorted(jobs.data, key=lambda x: x.created_at, reverse=True)
        
        # Find the most recent completed job with a checkpoint model
        for job in sorted_jobs:
            if job.status == "succeeded":
                checkpoint_model = job.fine_tuned_model
                if checkpoint_model:
                    return checkpoint_model
        
        return None  # No completed jobs found
    except Exception as e:
        print(f"Error retrieving jobs: {e}")
        return None
    
def index(client: OpenAI):
    # Retrieve the latest fine-tuned model
    checkpoint_model = get_latest_checkpoint_model(client)

    # Initialize session state for output text
    if "output_text" not in st.session_state:
        st.session_state["output_text"] = ""

    # Columns for input and output
    col1, col2 = st.columns(2)

    # Input Text Area (Left)
    with col1:
        st.markdown("### Kualifikasi Calon Pelaksana Pekerjaan")
        input_text = st.text_area("Enter your text here", height=300, label_visibility="collapsed", placeholder="Enter your text here")
        generate_button = st.button("Generate", key="generate")

    # Logic for Generate Button
    if generate_button:
        if input_text.strip():
            try:
                # Call the fine-tuned OpenAI model
                completion = client.chat.completions.create(
                    model=checkpoint_model,
                    messages=[
                        {"role": "system", "content": os.getenv("GENDONK_SYSTEM_PROMPT")},
                        {"role": "user", "content": input_text}
                    ]
                )
                # Extract the generated text
                generated_text = completion.choices[0].message.content
                st.session_state["output_text"] = generated_text
            except Exception as e:
                st.error(f"An error occurred: {e}")
        else:
            st.warning("Please enter some text to generate output.")

    # Output Text Area (Right)
    with col2:
        st.markdown("### Dokumen Penawaran Teknis")
        
        # Handle the Clear button first to avoid delayed state updates
        if st.button("Clear", key="clear"):
            st.session_state["output_text"] = ""  # Clear the output text

        # Display the current output text
        st.code(
            body=st.session_state["output_text"],
            language="plain",
            wrap_lines=True
        )
