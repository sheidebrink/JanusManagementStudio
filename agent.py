from strands import Agent

# Create a basic agent (uses Bedrock Claude 4 Sonnet by default)
agent = Agent(
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
        print("\nTo use this agent, you need to set up AWS Bedrock credentials.")
        print("You can either:")
        print("1. Set AWS_BEDROCK_API_KEY environment variable")
        print("2. Configure AWS credentials with 'aws configure'")
        print("3. Use a different model provider (Anthropic, OpenAI, etc.)")
        print("\nFor quick setup with Bedrock:")
        print("- Get API key from: https://console.aws.amazon.com/bedrock")
        print("- Enable model access in Bedrock console")
        print("- Set: set AWS_BEDROCK_API_KEY=your_key")