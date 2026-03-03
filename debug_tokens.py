import json
import tiktoken

def count_tokens_in_file(file_path):
    try:
        with open(file_path, "r") as f:
            data = json.load(f)

        # Approximate the string representation that would be sent to the LLM
        # This includes all keys and values as a JSON string
        text_payload = json.dumps(data)

        # Use cl100k_base which is a common encoding for modern LLMs (like GPT-4, similar to Gemini)
        encoding = tiktoken.get_encoding("cl100k_base")
        token_count = len(encoding.encode(text_payload))

        print(f"File: {file_path}")
        print(f"Approximate Character Count: {len(text_payload)}")
        print(f"Approximate Token Count: {token_count}")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    count_tokens_in_file("backend/request_body.json")
