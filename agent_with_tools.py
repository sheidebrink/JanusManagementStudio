from strands import Agent

# Define a simple custom tool
def get_current_time():
    """Get the current time and date."""
    import datetime
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def simple_calculator(expression: str) -> str:
    """Evaluate a simple mathematical expression safely."""
    try:
        # Only allow basic math operations for safety
        allowed_chars = set('0123456789+-*/.() ')
        if not all(c in allowed_chars for c in expression):
            return "Error: Only basic math operations are allowed"
        
        result = eval(expression)
        return f"{expression} = {result}"
    except Exception as e:
        return f"Error calculating {expression}: {str(e)}"

# Create an agent with custom tools
agent = Agent(
    model="gpt-4o-mini",
    provider="openai",
    tools=[get_current_time, simple_calculator],
    system_prompt="You are a helpful AI assistant. You can get the current time and perform simple calculations."
)

# Test the agent
if __name__ == "__main__":
    try:
        print("Testing agent with tools...")
        print("\n1. Asking for current time:")
        response = agent("What time is it?")
        print("Agent Response:", response)
        
        print("\n2. Asking for a calculation:")
        response = agent("What is 15 * 7 + 23?")
        print("Agent Response:", response)
        
    except Exception as e:
        print(f"Error: {e}")
        print("\nTo use this agent, you need to set up API credentials.")
        print("For OpenAI: set OPENAI_API_KEY=your_key")
        print("For Anthropic: set ANTHROPIC_API_KEY=your_key")
        print("Or modify the agent to use Bedrock with proper AWS credentials.")