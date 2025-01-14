import google.generativeai as genai  # type: ignore
import json
import os
from google.auth.transport.requests import Request  # type: ignore
from google.oauth2.credentials import Credentials  # type: ignore
from google_auth_oauthlib.flow import InstalledAppFlow  # type: ignore
from googleapiclient.discovery import build  # type: ignore
from googleapiclient.errors import HttpError  # type: ignore
import base64
import random
from email.mime.text import MIMEText

phishing_examples = [
    {"Reason": "Account Suspicious Activity", "Fake Link": "https://example.com/secure-login", "Created By": "Sam Sussy"},
    {"Reason": "Password Expiry Notification", "Fake Link": "https://example.com/reset-password", "Created By": "Sally Sneaky"},
    {"Reason": "Exclusive Training Webinar", "Fake Link": "https://example.com/join-webinar", "Created By": "Richard Rascal"},
    {"Reason": "Email Storage Full", "Fake Link": "https://example.com/manage-storage", "Created By": "Bernard Bandit"}
]

# Define the full path to the JSON file
CONFIG_FILE = "c:/Users/kevin/Documents/GitHub/email-generative-ai/gemini_email_sending_demo/config.json"
TOKEN_FILE = "c:/Users/kevin/Documents/GitHub/email-generative-ai/gemini_email_sending_demo/token.json"
CREDENTIALS_FILE = "credentials.json"

# Load configuration
def load_config(config_file):
    if os.path.exists(config_file):
        with open(config_file, "r") as file:
            return json.load(file)
    else:
        raise FileNotFoundError(f"Configuration file '{config_file}' not found.")

# Initialize generative AI model
def initialize_genai(api_key):
    genai.configure(api_key=api_key)
    return genai.GenerativeModel('gemini-pro')

# Generate email content
def generate_email_content(model, name, surname, team_name):
    # Take a random reason from phishing examples
    random_pick = random.choice(phishing_examples)

    # Formulate the prompt, avoiding placeholders like [topic] and [date]
    prompt = f"""Write a professional, well-crafted email from {random_pick["Created By"]} to {name} {surname} from the {team_name} team. 
    The email should be about the theme: {random_pick["Reason"]}. 
    The recipient will need to click on this link: {random_pick["Fake Link"]}.
    The email should not contain any placeholders like [Date and Time] or [Target Audience]. 
    It should sound professional, persuasive, and urgent, making it look like an email ready to send."""
    # Generate the body of the email using the correct method
    body = model.generate_content(prompt)

    # Generate the subject of the email
    subject = model.generate_content(f"Write me the subject of this email:\n{body.text}")
    print(subject.text)
    print(body.text)
    
    return subject.text, body.text  


# Create a message for an email
def create_message(sender, to, subject, message_text):
    message = MIMEText(message_text)
    message["to"] = to
    message["from"] = sender
    message["subject"] = subject
    return {"raw": base64.urlsafe_b64encode(message.as_bytes()).decode()}

# Send an email message
def send_message(service, user_id, message):
    try:
        sent_message = service.users().messages().send(userId=user_id, body=message).execute()
        print(f"Message sent! Message ID: {sent_message['id']}")
    except HttpError as error:
        print(f"An error occurred: {error}")

# Authenticate and get Gmail service
def get_gmail_service(scopes, token_file, credentials_file):
    creds = None
    if os.path.exists(token_file):
        creds = Credentials.from_authorized_user_file(token_file, scopes)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(credentials_file, scopes)
            creds = flow.run_local_server(port=0)
        with open(token_file, "w") as token:
            token.write(creds.to_json())
    return build("gmail", "v1", credentials=creds)

def main():
    config = load_config(CONFIG_FILE)
    GEMINI_API_KEY = config.get("GEMINI_API_KEY")
    model = initialize_genai(GEMINI_API_KEY)
    SCOPES = ["https://www.googleapis.com/auth/gmail.send"]
    service = get_gmail_service(SCOPES, TOKEN_FILE, CREDENTIALS_FILE)

    name = input("Enter the recipient's first name: ")
    surname = input("Enter the recipient's surname: ")
    email = input("Enter the recipient's email address: ")
    team_name = input("Enter the recipient's team name: ")

    subject, body = generate_email_content(model, name, surname, team_name)
    message = create_message("me", email, subject, body)
    send_message(service, "me", message)

if __name__ == "__main__":
    main()
