"""
Example client code showing how to handle the new token usage event
in the Server-Sent Events stream.
"""

import requests
import json

def stream_query_with_token_tracking():
    """
    Example of how to consume the streaming API and handle token usage.
    """
    
    # Example request payload
    payload = {
        "query_text": "Show me the top 5 customers by total orders",
        "model_name": "gemini-1.5-flash",
        "temperature": 0.1,
        "chat_history": [],
        "short_term_memory": []
    }
    
    # Make streaming request
    url = "http://localhost:8000/api/v1/query/stream"
    
    with requests.post(url, json=payload, stream=True) as response:
        response.raise_for_status()
        
        print("🔄 Streaming response:")
        print("-" * 50)
        
        for line in response.iter_lines(decode_unicode=True):
            if line.startswith("data: "):
                try:
                    data = json.loads(line[6:])  # Remove "data: " prefix
                    
                    # Handle different event types
                    if line.startswith("event: status_update"):
                        print(f"📋 Status: {data.get('message', '')}")
                    
                    elif line.startswith("event: structured_response"):
                        print(f"✅ Answer: {data.get('answer_text', '')[:100]}...")
                        if 'table' in data:
                            print(f"📊 Table with {len(data['table']['rows'])} rows")
                        if 'sql' in data:
                            print(f"🗃️ SQL: {data['sql']}")
                    
                    elif line.startswith("event: token_usage"):
                        # Handle token usage information
                        usage = data.get('token_usage', {})
                        calls_count = data.get('llm_calls_count', 0)
                        
                        print("\n💰 TOKEN USAGE SUMMARY:")
                        print(f"   📝 Prompt tokens: {usage.get('prompt_token_count', 0):,}")
                        print(f"   🤖 Response tokens: {usage.get('candidates_token_count', 0):,}")
                        print(f"   🔢 Total tokens: {usage.get('total_token_count', 0):,}")
                        print(f"   📞 LLM calls made: {calls_count}")
                        print("-" * 50)
                    
                    elif line.startswith("event: error"):
                        print(f"❌ Error: {data.get('message', '')}")
                
                except json.JSONDecodeError:
                    continue

if __name__ == "__main__":
    print("This is an example of how to handle token usage in streaming responses.")
    print("Start your FastAPI server and uncomment the function call below to test.")
    print()
    print("Expected stream format:")
    print("event: status_update")
    print('data: {"message": "Analyzing query..."}')
    print()
    print("event: structured_response") 
    print('data: {"answer_text": "Here are the top 5 customers...", "table": {...}, "sql": "SELECT ..."}')
    print()
    print("event: token_usage")
    print('data: {"token_usage": {"prompt_token_count": 1250, "candidates_token_count": 89, "total_token_count": 1339}, "llm_calls_count": 2}')
    
    # Uncomment to test against running server:
    # stream_query_with_token_tracking()
