from strands import Agent, tool
import datetime
import json

# Define custom tools using the @tool decorator
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
def get_system_info() -> str:
    """Get basic system information.
    
    Returns:
        System information as a JSON string
    """
    import platform
    import os
    
    info = {
        "platform": platform.system(),
        "platform_version": platform.version(),
        "architecture": platform.architecture()[0],
        "processor": platform.processor(),
        "python_version": platform.python_version(),
        "current_directory": os.getcwd(),
        "username": os.environ.get("USERNAME", "unknown")
    }
    
    return json.dumps(info, indent=2)

@tool
def text_analyzer(text: str) -> str:
    """Analyze text and provide statistics.
    
    Args:
        text: Text to analyze
        
    Returns:
        Analysis results as a formatted string
    """
    words = text.split()
    sentences = text.split('.')
    
    analysis = {
        "character_count": len(text),
        "word_count": len(words),
        "sentence_count": len([s for s in sentences if s.strip()]),
        "average_word_length": sum(len(word) for word in words) / len(words) if words else 0,
        "longest_word": max(words, key=len) if words else "",
        "shortest_word": min(words, key=len) if words else ""
    }
    
    result = "Text Analysis Results:\n"
    for key, value in analysis.items():
        if isinstance(value, float):
            result += f"- {key.replace('_', ' ').title()}: {value:.2f}\n"
        else:
            result += f"- {key.replace('_', ' ').title()}: {value}\n"
    
    return result

# Create an agent with custom tools
agent = Agent(
    tools=[get_current_time, simple_calculator, get_system_info, text_analyzer],
    system_prompt="You are a helpful AI assistant with access to time, calculator, system info, and text analysis tools. Use these tools to help answer user questions."
)

# Test the agent
if __name__ == "__main__":
    print("Testing Strands Agent with Custom Tools")
    print("=" * 50)
    
    test_questions = [
        "What time is it?",
        "Calculate 25 * 4 + 17",
        "What system am I running on?",
        "Analyze this text: 'The quick brown fox jumps over the lazy dog. This is a sample sentence for testing.'"
    ]
    
    for i, question in enumerate(test_questions, 1):
        print(f"\n{i}. Question: {question}")
        try:
            response = agent(question)
            print(f"   Response: {response}")
        except Exception as e:
            print(f"   Error: {e}")
            if i == 1:  # Only show setup instructions once
                print("\n   Setup Instructions:")
                print("   - For Bedrock: Set AWS_BEDROCK_API_KEY or configure AWS credentials")
                print("   - For OpenAI: Set OPENAI_API_KEY and modify the agent to use OpenAI model")
                print("   - For Anthropic: Set ANTHROPIC_API_KEY and modify the agent to use Anthropic model")
                break
    
    print("\n" + "=" * 50)
    print("Agent successfully created with custom tools!")
    print("Tools available:")
    print("- get_current_time: Get current date and time")
    print("- simple_calculator: Perform basic math calculations")
    print("- get_system_info: Get system information")
    print("- text_analyzer: Analyze text statistics")