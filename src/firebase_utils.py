import firebase_admin
from firebase_admin import credentials, firestore
import urllib.request
import base64
import os
from dotenv import load_dotenv

load_dotenv()

def initialize_firebase():
    """Initialize Firebase Admin SDK using environment variables."""
    if not firebase_admin._apps:
        # Create the credential dictionary just like your TypeScript ServiceAccount object
        cred_dict = {
            "type": "service_account",
            "project_id": os.getenv("GOOGLE_CLOUD_PROJECT_ID"),
            "private_key": os.getenv("GOOGLE_CLOUD_PRIVATE_KEY", "").replace('\\n', '\n'),
            "client_email": os.getenv("GOOGLE_CLOUD_CLIENT_EMAIL"),
            "token_uri": "https://oauth2.googleapis.com/token",
        }
        
        # Initialize with the dict instead of a JSON file path
        cred = credentials.Certificate(cred_dict)
        firebase_admin.initialize_app(cred, {
            'storageBucket': os.getenv("STORAGE_BUCKET")
        })
    return firestore.client()

def get_pending_submissions(db, collection_name="team_submissions"):
    """Fetch all pending system design submissions."""
    submissions_ref = db.collection(collection_name)
    query = submissions_ref.where("status", "==", "pending")
    return query.stream()

def update_submission_status(db, doc_id, status, collection_name="team_submissions"):
    """Update the status of a specific submission (e.g., 'processing', 'completed')."""
    db.collection(collection_name).document(doc_id).update({"status": status})

def save_evaluation_results(db, team_id, final_results, collection_name="evaluations"):
    """Save the final evaluation scores and MCQs to a new collection."""
    doc_ref = db.collection(collection_name).document(team_id)
    doc_ref.set(final_results)

def fetch_and_encode_image(image_url):
    """Downloads an image from a URL and encodes it in Base64."""
    try:
        response = urllib.request.urlopen(image_url)
        image_data = response.read()
        return base64.b64encode(image_data).decode("utf-8")
    except Exception as e:
        print(f"Error fetching image: {e}")
        return None
