import streamlit as st
import requests
import time

# =========================================================================
# CONFIGURATION
# Tell your friends to paste your Ngrok URL here!
# (Keep the '/evaluate' at the end)
BACKEND_API_URL = "<NGROK_URL>/evaluate"
# =========================================================================

st.set_page_config(page_title="Remote Sys Design Evaluator", layout="centered")

# Ensure Streamlit state variables are initialized
if 'eval_result' not in st.session_state:
    st.session_state.eval_result = None
if 'mcq_submitted' not in st.session_state:
    st.session_state.mcq_submitted = False
if 'user_answers' not in st.session_state:
    st.session_state.user_answers = {}

st.title("🌐 Remote System Design Evaluator")
st.markdown("Automated evaluation engine connected to the Cloud via API.")

# STEP 1: UPLOAD DESIGN
if st.session_state.eval_result is None:
    st.header("Step 1: Submit Your Design Phase")
    
    team_id = st.text_input("Team ID")
    problem = st.text_area("System Design Problem Statement", height=150)
    uploaded_image = st.file_uploader("Upload System Design Diagram", type=["png", "jpg", "jpeg"])
    
    if uploaded_image is not None:
        st.success("✅ Image selected!")
        with st.expander("👁️ View Uploaded Diagram"):
            st.image(uploaded_image, caption="System Design to be Evaluated", use_container_width=True)
    
    if st.button("Submit Design to AI Backend", type="primary"):
        if team_id and problem and uploaded_image:
            with st.spinner("Uploading to Backend... AI Agents are actively analyzing Architecture, Grading, and Generating Edge Cases."):
                
                # Prepare the Payload for the API
                # Reset file pointer just in case
                uploaded_image.seek(0)
                
                files = {'image': (uploaded_image.name, uploaded_image, uploaded_image.type)}
                data = {
                    'team_id': team_id,
                    'sd_problem': problem
                }
                
                try:
                    # Send API Request to your Ngrok backend
                    response = requests.post(BACKEND_API_URL, data=data, files=files)
                    
                    if response.status_code == 200:
                        result = response.json()
                        st.session_state.eval_result = result
                        st.success("Analysis Complete!")
                        time.sleep(1)
                        st.rerun() # Refresh to jump to Step 2
                    else:
                        st.error(f"Backend Server Error: {response.status_code} - {response.text}")
                except Exception as e:
                    st.error(f"Failed to connect to the backend server. Make sure the API_URL is correct. Error: {e}")
        else:
            st.warning("Please fill out all inputs before submitting.")

# STEP 2: ANSWER MCQS GENERATED DYNAMICALLY
elif not st.session_state.mcq_submitted:
    st.header(f"Step 2: Edge Case Scenario Questions (Team: {st.session_state.eval_result.get('team_id', 'Unknown')})")
    st.info("The architectural evaluation is complete. based on edge cases found in your design, please answer the following scenarios to accumulate your remaining 20 points.")
    
    # We must properly grab the mcqs array from the response dict
    questions = st.session_state.eval_result.get("mcqs", [])
    
    if type(questions) is not list or len(questions) == 0:
        st.error("No questions were received from the server. Please check the backend outputs.")
        st.write(st.session_state.eval_result) # Debugging step to see what actually arrived
        if st.button("Reset"):
            st.session_state.clear()
            st.rerun()
    else:
        with st.form("mcq_form"):
            for i, q in enumerate(questions):
                st.write(f"**Q{i+1}: {q.get('question', 'Missing Question Text')}**")
                options = q.get('options', [])
                
                # We add a default non-option so users are forced to choose
                display_options = ["Select an option..."] + options 
                
                selected = st.radio(f"Options for Q{i}", display_options, key=f"ans_{i}", label_visibility="collapsed")
                st.session_state.user_answers[i] = selected
                st.markdown("---")
            
            submit_answers = st.form_submit_button("Submit Answers & Reveal Final Score")
            if submit_answers:
                # Check if all questions are answered
                unanswered = [i for i in range(len(questions)) if st.session_state.user_answers[i] == "Select an option..."]
                if unanswered:
                    st.warning("Please answer all questions before submitting.")
                else:
                    st.session_state.mcq_submitted = True
                    st.rerun()

# STEP 3: REVEAL FINAL SCORE & BREAKDOWN
else:
    st.header("Step 3: Final Evaluation & Report")
    
    result = st.session_state.eval_result
    questions = result.get("mcqs", [])
    
    # Calculate MCQ Score
    mcq_score = 0
    for i, q in enumerate(questions):
        if st.session_state.user_answers.get(i) == q.get("correct_answer"):
            mcq_score += 1
            
    base_score = result.get("score_out_of_80", 0)
    final_score = base_score + mcq_score
    
    st.success(f"## Final Team Score: {final_score} / 100")
    
    # Visual Metrics
    col1, col2 = st.columns(2)
    with col1:
        st.metric("System Design Evaluation", f"{base_score} / 80")
    with col2:
        st.metric("Edge Case Handling", f"{mcq_score} / 20")
        
    st.markdown("---")
    
    # Show Original Feedback
    st.subheader("Architectural Feedback")
    st.write(result.get("evaluator_feedback", "No feedback provided by Agent 2."))
    
    st.subheader("Identified Architecture Edge Cases:")
    for ec in result.get("edge_cases", []):
        st.markdown(f"- {ec}")
        
    st.markdown("---")
    
    # MCQ Review
    st.subheader("MCQ Review")
    for i, q in enumerate(questions):
        correct_ans = q.get("correct_answer")
        user_ans = st.session_state.user_answers.get(i)
        is_correct = (user_ans == correct_ans)
        
        icon = "✅" if is_correct else "❌"
        
        with st.expander(f"Q{i+1}: {q.get('question')} {icon}"):
            st.write(f"**Your Answer:** {user_ans}")
            st.write(f"**Correct Answer:** {correct_ans}")
            if not is_correct:
                st.info(f"**Explanation:** {q.get('explanation')}")
            else:
                st.success("Correct!")
    
    if st.button("Start Over"):
        st.session_state.clear()
        st.rerun()