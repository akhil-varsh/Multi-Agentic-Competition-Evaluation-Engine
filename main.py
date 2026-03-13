import os
import time
from src.firebase_utils import initialize_firebase, get_pending_submissions, update_submission_status, save_evaluation_results, fetch_and_encode_image
from src.graph import eval_app

def process_pending_submissions():
    """
    Main orchestrator logic to be triggered by cron.
    Fetches pending system designs, runs the LangGraph evaluation pipeline, and updates Firebase.
    """
    try:
        db = initialize_firebase()
    except Exception as e:
        print(f"Failed to initialize Firebase: {e}")
        return

    print("Checking Firebase for pending system design submissions...")
    try:
        pending_docs = get_pending_submissions(db)
        docs = list(pending_docs)
    except Exception as e:
        print(f"Error fetching pending documents: {e}")
        return

    if not docs:
        print("No pending submissions found. Exiting.")
        return

    for doc in docs:
        doc_data = doc.to_dict()
        team_id = doc_data.get("teamid")
        sd_problem = doc_data.get("SD Problem", "")
        image_url = doc_data.get("image_url", "") # Assuming frontend stores URL

        print(f"Processing submission for Team ID: {team_id}")

        if not team_id or not image_url:
            print(f"Skipping document {doc.id} due to missing team_id or image_url.")
            continue

        try:
            update_submission_status(db, doc.id, "processing")
        except Exception as e:
            print(f"Error updating status to processing for {doc.id}: {e}")
            continue

        image_b64 = fetch_and_encode_image(image_url)
        if not image_b64:
            print(f"Failed to fetch image for team {team_id}. Reverting status back to pending.")
            update_submission_status(db, doc.id, "pending")
            continue

        state = {
            "team_id": team_id,
            "sd_problem": sd_problem,
            "image_b64": image_b64,
            "extracted_design": "",
            "score_80": 0,
            "evaluator_feedback": "",
            "edge_cases": [],
            "mcqs": []
        }

        try:
            print(f"Running evaluation pipeline for team {team_id}...")
            # Run LangGraph pipeline
            final_state = eval_app.invoke(state)

            final_results = {
                "teamid": team_id,
                "score_80": final_state.get("score_80", 0),
                "evaluator_feedback": final_state.get("evaluator_feedback", ""),
                "edge_cases": final_state.get("edge_cases", []),
                "mcqs": final_state.get("mcqs", []),
                "total_score_if_passed": final_state.get("score_80", 0) + 20, # 80 + 20
                "status": "evaluated"
            }

            # Save the evaluation output to the new 'evaluations' collection
            save_evaluation_results(db, team_id, final_results, "evaluations")

            # Update final status in the original submission
            update_submission_status(db, doc.id, "completed")
            print(f"Successfully finished processing for Team ID: {team_id}")

        except Exception as e:
            print(f"Pipeline failed for {team_id}: {e}")
            update_submission_status(db, doc.id, "failed")

if __name__ == "__main__":
    start_time = time.time()
    print("--- Starting evaluation cron job ---")
    process_pending_submissions()
    print(f"--- Completed evaluation in {time.time() - start_time:.2f} seconds ---")
