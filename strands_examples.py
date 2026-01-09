"""
Strands Agent Examples - Different ways to create and use AI agents

This file demonstrates various configurations of Strands agents:
1. Basic agent with different providers
2. Agent with custom tools
3. Agent with conversation context
4. Different model configurations
"""

from strands import Agent, tool
from strands.models.openai import OpenAIModel
from strands.models.anthropic import AnthropicModel
import datetime
import os

# Example 1: Basic agents with different providers
def create_basic_agents():
    """Create basic agents with different model providers."""
    
    # Bedrock (AWS) - Default
    bedrock_agent = Agent(
        system_prompt="You are a helpful AI assistant."
    )
    
    # OpenAI
    openai_model = OpenAIModel(
        client_args={"api_key": os.environ.get("OPENAI_API_KEY", "your_key_here")},
        model_id="gpt-4o-mini",
    )
    openai_agent = Agent(
        model=openai_model,
        system_prompt="You are a helpful AI assistant."
    )
    
    # Anthropic
    anthropic_model = AnthropicModel(
        client_args={"api_key": os.environ.get("ANTHROPIC_API_KEY", "your_key_here")},
        model_id="claude-3-haiku-20240307",
        max_tokens=1028,
        params={"temperature": 0.7}
    )
    anthropic_agent = Agent(
        model=anthropic_model,
        system_prompt="You are a helpful AI assistant."
    )
    
    return {
        "bedrock": bedrock_agent,
        "openai": openai_agent,
        "anthropic": anthropic_agent
    }

# Example 2: Custom tools using the @tool decorator
@tool
def get_current_time() -> str:
    """Get the current time and date.
    
    Returns:
        Current date and time as a string
    """
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

@tool
def simple_calculator(expression: str) -> str:
    """Evaluate a simple mathematical expression safely.
    
    Args:
        expression: Mathematical expression to evaluate (e.g., "2 + 3 * 4")
        
    Returns:
        Result of the calculation or error message
    """
    try:
        # Only allow basic math operations for safety
        allowed_chars = set('0123456789+-*/.() ')
        if not all(c in allowed_chars for c in expression):
            return "Error: Only basic math operations are allowed"
        
        result = eval(expression)
        return f"{expression} = {result}"
    except Exception as e:
        return f"Error calculating {expression}: {str(e)}"

@tool
def get_weather_info(city: str) -> str:
    """Mock weather function - in real use, this would call a weather API.
    
    Args:
        city: Name of the city to get weather for
        
    Returns:
        Weather information for the city
    """
    return f"The weather in {city} is sunny with a temperature of 72°F"

def create_agent_with_tools():
    """Create an agent with custom tools."""
    # Use OpenAI if available, otherwise default to Bedrock
    if os.environ.get("OPENAI_API_KEY"):
        model = OpenAIModel(
            client_args={"api_key": os.environ["OPENAI_API_KEY"]},
            model_id="gpt-4o-mini",
        )
        return Agent(
            model=model,
            tools=[get_current_time, simple_calculator, get_weather_info],
            system_prompt="You are a helpful assistant with access to time, calculator, and weather tools."
        )
    else:
        return Agent(
            tools=[get_current_time, simple_calculator, get_weather_info],
            system_prompt="You are a helpful assistant with access to time, calculator, and weather tools."
        )

# Example 3: Specialized agents
def create_specialized_agents():
    """Create agents specialized for different tasks."""
    
    # Use OpenAI if available, otherwise default to Bedrock
    if os.environ.get("OPENAI_API_KEY"):
        model = OpenAIModel(
            client_args={"api_key": os.environ["OPENAI_API_KEY"]},
            model_id="gpt-4o-mini",
        )
        
        # Geography expert
        geography_agent = Agent(
            model=model,
            system_prompt="You are a geography expert with deep knowledge of countries, capitals, landmarks, and geographical features."
        )
        
        # Math tutor
        math_agent = Agent(
            model=model,
            tools=[simple_calculator],
            system_prompt="You are a friendly math tutor who helps students understand mathematical concepts and solve problems step by step."
        )
        
        # Code assistant
        code_agent = Agent(
            model=model,
            system_prompt="You are a helpful programming assistant who can help with code review, debugging, and explaining programming concepts."
        )
    else:
        # Use Bedrock defaults
        geography_agent = Agent(
            system_prompt="You are a geography expert with deep knowledge of countries, capitals, landmarks, and geographical features."
        )
        
        math_agent = Agent(
            tools=[simple_calculator],
            system_prompt="You are a friendly math tutor who helps students understand mathematical concepts and solve problems step by step."
        )
        
        code_agent = Agent(
            system_prompt="You are a helpful programming assistant who can help with code review, debugging, and explaining programming concepts."
        )
    
    return {
        "geography": geography_agent,
        "math": math_agent,
        "code": code_agent
    }

def test_agent(agent, test_name, question):
    """Test an agent with a question."""
    print(f"\n=== {test_name} ===")
    print(f"Question: {question}")
    try:
        response = agent(question)
        print(f"Response: {response}")
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False

def main():
    """Main function to demonstrate different agent configurations."""
    print("Strands Agent Examples")
    print("=" * 50)
    
    # Test basic functionality
    print("\n1. Testing basic agent functionality...")
    
    try:
        # Create a simple agent (will use Bedrock by default)
        agent = Agent(
            system_prompt="You are a helpful AI assistant."
        )
        
        success = test_agent(agent, "Basic Agent Test", "What is 2 + 2?")
        
        if success:
            print("\n2. Testing agent with tools...")
            tool_agent = create_agent_with_tools()
            test_agent(tool_agent, "Tool Agent - Time", "What time is it?")
            test_agent(tool_agent, "Tool Agent - Math", "Calculate 15 * 7 + 23")
            test_agent(tool_agent, "Tool Agent - Weather", "What's the weather like in Paris?")
            
            print("\n3. Testing specialized agents...")
            specialized = create_specialized_agents()
            test_agent(specialized["geography"], "Geography Expert", "What is the capital of Australia?")
            test_agent(specialized["math"], "Math Tutor", "Explain how to solve 2x + 5 = 15")
            test_agent(specialized["code"], "Code Assistant", "How do I create a list in Python?")
        
    except Exception as e:
        print(f"Could not test agents: {e}")
        print("\nThis is expected if you don't have API keys set up.")
    
    print("\n" + "=" * 50)
    print("Setup Instructions:")
    print("=" * 50)
    print("To use these agents, you need to set up API credentials:")
    print("\nFor OpenAI:")
    print("1. Get API key from: https://platform.openai.com/api-keys")
    print("2. Set environment variable: set OPENAI_API_KEY=your_key")
    print("\nFor Anthropic:")
    print("1. Get API key from: https://console.anthropic.com/")
    print("2. Set environment variable: set ANTHROPIC_API_KEY=your_key")
    print("\nFor AWS Bedrock (default):")
    print("1. Configure AWS credentials: aws configure")
    print("2. Enable model access in Bedrock console")
    print("3. Ensure proper IAM permissions for Bedrock")
    print("   OR use Bedrock API key: set AWS_BEDROCK_API_KEY=your_key")
    
    print("\nExample usage:")
    print("set OPENAI_API_KEY=sk-your-key-here")
    print("py strands_examples.py")

if __name__ == "__main__":
    main()