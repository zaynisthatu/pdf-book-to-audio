from google import genai
client = genai.Client(api_key="")
def main():
    conversation = []
    while True:
        user_input = input("You: ").strip()
        if user_input.lower() == "bye":
            break
        response = client.models.generate_content(model="gemini-2.5-pro", contents=user_input)
        print(f"AI: {response.text}")
        conversation.append(f"**You:** {user_input}\n\n**AI:** {response.text}\n\n---\n")
    with open("conversation.md", "w", encoding="utf-8") as f:
        f.writelines(conversation)
