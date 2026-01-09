from strands import Agent

# Create an agent using OpenAI's API
agent = Agent(
    model="gpt-4o-mini",
    provider="openai",
    system_prompt="You are a helpful AI assistant with expertise in geography and space."
)

# Test the agent
if __name__ == "__main__":
    try:
        response = agent("What is the capital of France?")
        print("Agent Response:")
        print(response)
    except Exception as e:
        print(f"Error: {e}")
        print("\nTo use this agent with OpenAI, you need to:")
        print("1. Get an API key from: https://platform.openai.com/api-keys")
        print("2. Set environment variable: set OPENAI_API_KEY=your_key")
        print("\nAlternatively, you can use other providers like:")
        print("- Anthropic: provider='anthropic', model='claude-3-haiku-20240307'")
        print("- Gemini: provider='gemini', model='gemini-pro'")
        print("- Local models: provider='ollama', model='llama2'")