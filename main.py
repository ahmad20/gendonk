import streamlit as st
import pyperclip  # To handle clipboard copying

# Streamlit layout configuration
st.set_page_config(layout="wide")

# Initialize session state for output text
if "output_text" not in st.session_state:
    st.session_state["output_text"] = ""

# Columns for input and output
col1, col2 = st.columns(2)

# Input Text Area (Left)
with col1:
    st.markdown("### Input")
    input_text = st.text_area("Enter your text here", height=200, label_visibility="collapsed")
    generate_button = st.button("Generate", key="generate")

# Logic for Generate Button
if generate_button:
    if input_text.strip():
        # Generate output immediately and update session state
        generated_text = f"{input_text}, from me"
        st.session_state["output_text"] = generated_text
    else:
        st.warning("Please enter some text to generate output.")

# Output Text Area (Right)
with col2:
    st.markdown("### Output")
    output_text = st.text_area(
        "Generated output will appear here",
        height=200,
        label_visibility="collapsed",
        value=st.session_state["output_text"],
    )
    copy_button = st.button("Copy to Clipboard", key="copy")

# Logic for Copy Button
if copy_button:
    if st.session_state["output_text"]:
        pyperclip.copy(st.session_state["output_text"])
        st.success("Output text copied to clipboard!")
    else:
        st.warning("No output text to copy.")