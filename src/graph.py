from typing import TypedDict, List
import json
import re
from langchain_core.messages import HumanMessage
from langgraph.graph import StateGraph, START, END

from src.llm_config import get_llm, get_multimodal_llm

def safe_json_parse(text: str) -> dict:
    """Helper to safely parse JSON even if wrapped in markdown blocks."""
    text = text.strip()
    # Strip markdown block formatting if present
    text = re.sub(r'^```(?:json)?\n?', '', text)
    text = re.sub(r'\n?```$', '', text)
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        raise ValueError(f"Extracted string is not valid JSON: {e}\nRaw Text: {text}")

class EvaluationState(TypedDict):
    team_id: str
    sd_problem: str
    image_b64: str
    extracted_design: str
    score_80: int
    evaluator_feedback: str
    edge_cases: List[str]
    mcqs: List[dict]

def extract_design_info(state: EvaluationState) -> dict:
    """Agent 1: Extracts system design details from the image."""
    print(f"\n[{'*'*10} AGENT 1: EXTRACTING DESIGN INFO FOR TEAM {state['team_id']} {'*'*10}]")
    llm = get_multimodal_llm()
    
    prompt = f"""You are a Principal Cloud Architect and System Design Expert with 15+ years of experience in distributed systems.
    Your task is to exhaustively analyze a submitted System Design block diagram.

    Context:
    - Problem Statement: {state['sd_problem']}
    
    Instructions:
    Carefully examine every detail in the attached image.
    Provide a comprehensive, purely factual extraction of the architecture depicted. You must capture:
    1. Infrastructure & Networking: All API Gateways, Load Balancers, CDN, Firewalls, DNS routing, and VPC details shown.
    2. Compute & Microservices: Every service/application block. Note if they are serverless, containerized, event-driven, or monolithic.
    3. Data Storage: Databases (SQL/NoSQL/Graph), Caches (Redis/Memcached), Message Queues/Brokers (Kafka/RabbitMQ), and Object Stores (S3).
    4. Interactions & Data Flow: Describe the directional arrows. What talks to what? Is it synchronous (REST/gRPC) or asynchronous? 
    5. Missing obvious components: Note any immediate missing foundational elements (e.g., "There is no load balancer in front of the 5 web servers").
    
    Output strictly detailed technical text. Do not evaluate yet, just map the components.
    """
    
    print("⏳ Agent 1 is analyzing the diagram using multimodal model...")
    message = HumanMessage(
        content=[
            {"type": "text", "text": prompt},
            {
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{state['image_b64']}"}
            }
        ]
    )
    
    response = llm.invoke([message])
    print("\n✅ [AGENT 1 OUTPUT] -> Extracted Components:\n")
    print(response.content)
    return {"extracted_design": response.content}

def evaluate_design(state: EvaluationState) -> dict:
    """Agent 2: Evaluates the design against the problem statement and finds edge cases."""
    print(f"\n[{'*'*10} AGENT 2: EVALUATING DESIGN FOR TEAM {state['team_id']} {'*'*10}]")
    llm = get_llm()
    # using structured output by telling the model to output json
    prompt = f"""You are a Lead Staff Engineer and a notoriously strict, expert System Design Evaluator. You are assessing a candidate's architectural proposal based on a rigorous grading rubric.
    
    Problem Statement Requirements: {state['sd_problem']}
    
    Extracted Architectural Components (from visual diagram):
    {state['extracted_design']}
    
    Evaluation Instructions:
    1. Score the architecture out of a maximum of 80 points based strictly on these dimensions:
       - Scalability (20 pts): Can it handle 10x traffic spikes? Are there bottlenecks?
       - Fault Tolerance & Reliability (20 pts): Are there single points of failure (SPOF)? What happens if a DB goes down?
       - Data Management (20 pts): Is the choice of SQL/NoSQL appropriate? Is caching utilized properly? Is data consistency addressed?
       - Overall Suitability (20 pts): Does the architecture directly solve the user's specific "Problem Statement"?
       
    2. Identify Critical Weaknesses & Edge Cases: Formulate 20 hyper-specific, realistic production edge cases that this specific architecture fails to handle correctly. (e.g., "Cache stampede on the user-metadata Redis cluster upon regional failover").

    CRITICAL RULES:
    - Keep the `feedback` string concise (under 4 sentences) to prevent JSON cutoffs.
    - ESCAPE all internal double quotes inside your string values using backslashes.

    Output MUST be strictly in the following JSON format:
    {{
        "score_out_of_80": <integer_value>,
        "feedback": "<string: concise, professional structured feedback>",
        "edge_cases": ["<detailed_edge_case_1>", "<detailed_edge_case_2>", "<detailed_edge_case_3>"]
    }}
    """
    
    print("⏳ Agent 2 is grading the architecture and generating Edge Cases...")
    response = llm.invoke(prompt)
    
    print("\n✅ [AGENT 2 RAW JSON OUTPUT]:\n")
    print(response.content)
    
    try:
        data = safe_json_parse(response.content)
        return {
            "score_80": data.get("score_out_of_80", 0),
            "evaluator_feedback": data.get("feedback", ""),
            "edge_cases": data.get("edge_cases", [])
        }
    except Exception as e:
        print(f"❌ [ERROR] Agent 2 JSON parsing failed: {e}")
        return {"score_80": 0, "evaluator_feedback": "Failed to evaluate due to model output error.", "edge_cases": []}

def generate_mcqs(state: EvaluationState) -> dict:
    """Agent 3: Generates MCQs based on the edge cases."""
    print(f"\n[{'*'*10} AGENT 3: GENERATING MCQS FOR TEAM {state['team_id']} {'*'*10}]")
    llm = get_llm()
    
    prompt = f"""You are a Systems Engineering Mentor crafting an evaluation assessment.
    Your goal is to test the candidates on the flaws and unhandled edge cases found in their System Design. 
    
    Context:
    - Original Problem: {state['sd_problem']}
    - Specific Edge Cases/Flaws Found in Their Design: {state['edge_cases']}
    
    Instructions:
    Generate EXACTLY 20 intermediate-level, scenario-based Multiple-Choice Questions (MCQs).
    The questions MUST directly relate to mitigating or solving the `Edge Cases` listed above. 
    - CRITICAL: Ensure every single question tests a DIFFERENT, UNIQUE concept to avoid redundancy.
    - CRITICAL: DO NOT start your questions by saying "Agent 3's design" or referencing "Agent 3". Talk purely about "The candidate's design", "The proposed architecture", or "The system".
    - Options should include realistic but incorrect solutions to test conceptual understanding.
    - Provide a clear technical explanation for why the `correct_answer` is right.
    
    Output strictly in the following JSON format (an array of objects nested under the "questions" key):
    {{
        "questions": [
            {{
                "question": "<Intermediate scenario-based question text regarding an edge case>",
                "options": ["<option_A>", "<option_B>", "<option_C>", "<option_D>"],
                "correct_answer": "<Must be the FULL EXACT STRING of the correct option, not just 'A', 'B', 'C', or 'D'>",
                "explanation": "<Clear technical reasoning why this handles the given edge case gracefully>"
            }}
        ]
    }}
    Ensure all 20 questions are generated. No more, no less.
    """
    
    print(f"⏳ Agent 3 is generating 20 MCQs based on edge cases: {state['edge_cases']}...")
    response = llm.invoke(prompt)
    
    print("\n✅ [AGENT 3 RAW JSON OUTPUT]:\n")
    print(response.content)
    
    try:
        data = safe_json_parse(response.content)
        print(f"\n🎉 Successfully parsed {len(data.get('questions', []))} questions from Agent 3!")
        return {"mcqs": data.get("questions", [])}
    except Exception as e:
        print(f"❌ [ERROR] Agent 3 JSON parsing failed: {e}")
        return {"mcqs": []}

# Build LangGraph
workflow = StateGraph(EvaluationState)

workflow.add_node("extract_design_info", extract_design_info)
workflow.add_node("evaluate_design", evaluate_design)
workflow.add_node("generate_mcqs", generate_mcqs)

workflow.add_edge(START, "extract_design_info")
workflow.add_edge("extract_design_info", "evaluate_design")
workflow.add_edge("evaluate_design", "generate_mcqs")
workflow.add_edge("generate_mcqs", END)

eval_app = workflow.compile()
