from strands import Agent

# Create an agent using Anthropic's API instead of Bedrock
agent = Agent(
    model="claude-3-haiku-20240307",
    provider="anthropic",
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
        print("\nTo use this agent with Anthropic, you need to:")
        print("1. Get an API key from: https://console.anthropic.com/")
        print("2. Set environment variable: set ANTHROPIC_API_KEY=your_key")
        print("\nAlternatively, you can use other providers like:")
        print("- OpenAI: provider='openai', model='gpt-4'")
        print("- Gemini: provider='gemini', model='gemini-pro'")
        print("- Local models: provider='ollama', model='llama2'")