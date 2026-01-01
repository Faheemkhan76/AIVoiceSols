import os
import json
import boto3 
from datetime import datetime
from dotenv import load_dotenv
from apiclient import ApiClient

load_dotenv()

def updatedatabase():
    startdatetime = datetime.now()
    print(startdatetime)
    client_id = os.environ.get("COGNITO_CLIENT_ID")
    client_secret = os.environ.get("COGNITO_CLIENT_SECRET")
    token_url = os.environ.get("COGNITO_TOKEN_URL")
    api_base_url = os.environ.get("CFI_BASE_URL")
        
    client = ApiClient(
    client_id=client_id,
    client_secret=client_secret,
    token_url=token_url,
    api_base_url=api_base_url
    )
    transcript_object_key = "livekit\fahkhan172@gmail.com\123\transcript.json"
    report_object_key = "livekit\fahkhan172@gmail.com\123\transcript.json"
    minutesconsumed = (datetime.now() - startdatetime).total_seconds()
    #Update user session with session end data
    data = { 
                # "transcriptpath": transcript_object_key,
                # "reportpath": report_object_key,
                # "enddatetime": f'{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}',
                # "MinutesConsumed": minutesconsumed,
                "startdatetime": f'{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}',
                "status": 2 #session end
            }
    response = client.call_api(method="PATCH",path= f"/api/sessions/{int('55')}", json=data)
    return response
    
def getData():
    startdatetime = datetime.now()
    client_id = os.environ.get("COGNITO_CLIENT_ID")
    client_secret = os.environ.get("COGNITO_CLIENT_SECRET")
    token_url = os.environ.get("COGNITO_TOKEN_URL")
    api_base_url = os.environ.get("CFI_BASE_URL")
        
    client = ApiClient(
    client_id=client_id,
    client_secret=client_secret,
    token_url=token_url,
    api_base_url=api_base_url
    )
    
    response = client.call_api(method="GET",path= f"/api/sessions/{int('42')}")
    print(response.json()['JobDescription'])
    return response
    
    import json
import re

def extract_json_object(text: str):
    # Extract JSON-like content from the string
    match = re.search(r'\{.*\}', text, re.DOTALL)
    if not match:
        raise ValueError("No JSON object found in the string.")

    json_str = match.group()

    # Fix improperly escaped quotes inside values
    # This targets quotes inside strings that are not escaped
    def fix_quotes(s):
        def replacer(match):
            content = match.group(1)
            # Escape internal quotes
            fixed = re.sub(r'(?<!\\)"', r'\\"', content)
            return f'"{fixed}"'
        return re.sub(r'"([^"]*?)"', replacer, s)

    fixed_json_str = fix_quotes(json_str)
    print(fixed_json_str)
    try:
        return json.loads(fixed_json_str)
    except json.JSONDecodeError as e:
        raise ValueError(f"Still invalid JSON after fix: {e}")


if __name__ == "__main__":
    # print(getData()['JobDescription'])
    # print(getData().json())
    # print(updatedatabase().status_code)
    # Example usage
    input_str = r'''```json
{
    "items": [
        {
            "questionnumber": "1",
            "question": "Welcome to \"Call for Interview.\" Are you ready to begin the interview?",
            "score": "5",
            "analysis": "The candidate provided a basic confirmation but did not elaborate or show enthusiasm.",
            "comments": "The candidate could improve by expressing enthusiasm or readiness in more detail, such as mentioning their preparation or excitement for the opportunity."
        },
        {
            "questionnumber": "2",
            "question": "Great! Let's start with your experience as a Software Architect. Can you share an example of a project where you designed and implemented a scalable, high-performance system? What were the key challenges you faced, and how did you address them?",
            "score": "3",
            "analysis": "The candidate started describing a project but was interrupted and provided incomplete information. The response lacked detail on challenges and solutions.",
            "comments": "The candidate should prepare a structured response detailing the project, challenges faced, and specific solutions implemented. Avoid interruptions and ensure clarity."
        },
        {
            "questionnumber": "3",
            "question": "That sounds like a significant project! Could you tell me more about the technical challenges you encountered while developing the Azure-based system? Specifically, how did you ensure the system could handle high traffic and maintain high availability?",
            "score": "4",
            "analysis": "The candidate mentioned deploying multiple instances but did not elaborate on technical challenges or strategies for high availability.",
            "comments": "The candidate should provide specific technical details, such as load balancing, auto-scaling, or redundancy strategies used to ensure high availability."
        },
        {
            "questionnumber": "4",
            "question": "It sounds like you implemented a robust architecture. How did you manage data consistency and performance when multiple instances of the application were accessing the SQL RDBMS? Additionally, were there any strategies you used for optimizing the performance of the database?",
            "score": "2",
            "analysis": "The candidate did not address the question and provided an unclear response.",
            "comments": "The candidate should prepare to discuss database optimization techniques, such as indexing, caching, or partitioning, and explain how they ensured data consistency in a distributed system."
        },
        {
            "questionnumber": "5",
            "question": "You're welcome! For the next question, let's discuss your experience with continuous integration and continuous delivery (CI/CD). Can you describe how you implemented CI/CD pipelines in your projects? Specifically, how did you ensure the pipelines supported rapid development while maintaining high quality and reliability?",
            "score": "0",
            "analysis": "The candidate did not respond to the question.",
            "comments": "The candidate should be prepared to discuss CI/CD tools used (e.g., Jenkins, Azure DevOps), pipeline stages, and strategies for ensuring quality (e.g., automated testing, code reviews)."
        }
    ],
    "totalscore": "2.8"
}
```'''
    input_str='''{
                    "items": [
                        {
                            "questionnumber": "1",
                            "question": "Welcome to \"Call for Interview\"! Are you ready to start the interview?",
                            "score": "1",
                            "analysis": "The candidate responded with a very brief and unenthusiastic 'Yes.' This lacks engagement and readiness.",
                            "comments": "The candidate should show more enthusiasm and readiness for the interview. A better response could include a brief statement about their preparedness or excitement for the opportunity."
                        },
                        {
                            "questionnumber": "2",
                            "question": "Great! To begin, could you please provide the job description for the position you're preparing for? This will help me tailor the interview questions accordingly.",
                            "score": "0",
                            "analysis": "The candidate did not provide the requested job description and instead indicated they would 'miss it' and asked to end the session.",
                            "comments": "The candidate should be prepared with the job description or at least communicate their inability to provide it in a professional manner. Ending the session abruptly is not advisable."
                        }
                    ],
                    "totalscore": "0.5"
                }'''
    response = json.loads(input_str)
    
    # data = extract_json_object(input_str)
    # print(json.dumps(data, indent=4))  # Pretty print extracted JSON

    
