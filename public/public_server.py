import os
import base64
from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS

# Import your existing compiled LangGraph app!
from src.graph import eval_app

app = Flask(__name__)
CORS(app)

# A simple HTML page your friends can use to upload their System Designs
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>System Design Evaluator</title>
    <style>
        body { font-family: system-ui, sans-serif; max-width: 600px; margin: 40px auto; padding: 20px; text-align: center;}
        .card { padding: 20px; border: 1px solid #ccc; border-radius: 8px; background: #f9f9f9; text-align: left; }
        input, textarea, button { width: 100%; margin-bottom: 20px; padding: 10px; box-sizing: border-box;}
        button { background: #0066cc; color: white; border: none; font-weight: bold; cursor: pointer; }
        button:hover { background: #0050a0; }
        pre { background: #222; color: #0f0; padding: 10px; overflow-x: auto; border-radius: 4px; }
    </style>
</head>
<body>
    <h1>System Design Evaluator</h1>
    <p>Upload a diagram and describe the problem you were trying to solve!</p>
    
    <div class="card">
        <form id="evalForm">
            <label><b>Team Name / Your Name:</b></label>
            <input type="text" id="team_id" required placeholder="e.g. My Team">
            
            <label><b>Problem Statement:</b></label>
            <textarea id="sd_problem" rows="4" required placeholder="Describe the system requirements..."></textarea>
            
            <label><b>Architecture Diagram (Image):</b></label>
            <input type="file" id="image" accept="image/*" required>
            
            <button type="submit" id="submitBtn">Analyze via Multi-Agent Graph</button>
        </form>
    </div>
    
    <div id="result" style="display:none; text-align:left; margin-top:20px;">
        <h3>AI Agents Result:</h3>
        <pre id="jsonOutput"></pre>
    </div>

    <script>
        document.getElementById('evalForm').onsubmit = async (e) => {
            e.preventDefault();
            const btn = document.getElementById('submitBtn');
            btn.innerText = "Analyzing Diagram... (This takes a moment)";
            btn.disabled = true;
            
            const formData = new FormData();
            formData.append("team_id", document.getElementById('team_id').value);
            formData.append("sd_problem", document.getElementById('sd_problem').value);
            formData.append("image", document.getElementById('image').files[0]);

            try {
                const response = await fetch('/evaluate', { method: 'POST', body: formData });
                const json = await response.json();
                document.getElementById('result').style.display = 'block';
                document.getElementById('jsonOutput').innerText = JSON.stringify(json, null, 2);
            } catch (err) {
                alert("Error connecting to server!");
            }
            
            btn.innerText = "Analyze via Multi-Agent Graph";
            btn.disabled = false;
        };
    </script>
</body>
</html>
"""

@app.route('/', methods=['GET'])
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/evaluate', methods=['POST'])
def evaluate():
    try:
        # 1. Extract data from request
        team_id = request.form.get('team_id', 'Unknown Team')
        sd_problem = request.form.get('sd_problem', 'No problem description provided.')
        
        if 'image' not in request.files:
            return jsonify({"error": "No image file uploaded"}), 400
            
        file = request.files['image']
        image_bytes = file.read()
        
        # 2. Convert image to base64 for the multimodal LLM
        image_b64 = base64.b64encode(image_bytes).decode('utf-8')
        
        # 3. Create the state exactly as your LangGraph expects it
        state_input = {
            "team_id": team_id,
            "sd_problem": sd_problem,
            "image_b64": image_b64
        }
        
        print(f"\n🚀 Received New Request from {team_id}...")
        
        # 4. Invoke the LangGraph workflow!
        # Because LangSmith is configured in your environment, this invocation 
        # is automatically traced and tracked on your dashboard.
        result = eval_app.invoke(state_input)
        
        print(f"✅ Finished request for {team_id}!")
        
        # 5. Return the relevant extracted fields to the frontend
        return jsonify({
            "status": "success",
            "team_id": result.get("team_id"),
            "score_out_of_80": result.get("score_80"),
            "evaluator_feedback": result.get("evaluator_feedback"),
            "edge_cases": result.get("edge_cases", []),
            "mcqs": result.get("mcqs", []),  # Sending the full MCQs so the Streamlit friend app can render them
            "full_extracted_design": result.get("extracted_design")
        })
        
    except Exception as e:
        print(f"❌ Error during evaluation: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    print("==================================================")
    print("🌐 Public LangGraph Server Started!")
    print("🔗 Local URL: http://localhost:8000")
    print("\n👉 To expose to friends, open a NEW terminal and run:")
    print("   ngrok http 8000")
    print("==================================================")
    
    # Running on port 8000
    app.run(host='0.0.0.0', port=8000, threaded=True)