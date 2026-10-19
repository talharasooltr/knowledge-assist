import getpass
from api_client import ApiClient

BASE_URL = "http://127.0.0.1:8000"
# BASE_URL = "http://40.82.161.202:8000"

def authenticate():
    print("=== Chat Client Login ===")
    while True:
        user_id = input("User ID: ").strip()
        password = getpass.getpass("Password: ")
        try:
            client = ApiClient(BASE_URL)
            res = client.login(user_id, password)
            if res.status_code == 200 and res.json().get("role") == "user":
                print("✅ Authentication successful!\n")
                return user_id, client
            if res.status_code == 200:
                print("❌ This client is for member accounts.\n")
            else:
                print("❌ Incorrect username or password. Please try again.\n")
        except Exception as e:
            print(f"❌ Error connecting to server: {e}\n")

def print_history(client, conversation_id):
    try:
        res = client.get(f"/chat/conversations/{conversation_id}/messages")
        print("*" * 10)
        if res.status_code == 200:
            history = res.json().get("history", [])
            print("\n--- User Message History ---")
            for i, msg in enumerate(history, 1):
                print(f"{i}: {msg}")
            print("----------------------------\n")
        else:
            print("Failed to fetch history.")
    except Exception as e:
        print(f"Error fetching history: {e}")

def chat():
    # Authenticate user first
    user_id, client = authenticate()
    try:
        conversation = client.post("/chat/conversations").json()
        conversation_id = conversation["id"]
    except (KeyError, ValueError) as e:
        print(f"Unable to start a conversation: {e}")
        return
    
    print("Chat started! Type 'exit' or 'quit' to end the session.")
    print("-" * 50)
    
    while True:
        msg = input("You: ")
        if msg.lower() in ("exit", "quit"): 
            print("Goodbye!")
            break
        try:
            res = client.post(
                f"/chat/conversations/{conversation_id}/messages",
                json={"message": msg},
            )
            
            if res.status_code == 200:
                response_data = res.json()
                print_history(client, conversation_id)
                print("Prompt: ", response_data.get("prompt", ""))
                print("*" * 10)
                print("🤖 Predict:", response_data.get("response", ""))
            else:
                try:
                    error_data = res.json()
                    print(f"Error: {error_data.get('error', 'Unknown error')}")
                except:
                    print(f"Error: HTTP {res.status_code} - {res.text}")
        except Exception as e:
            print(f"Error sending message: {e}")

if __name__ == "__main__":
    chat()