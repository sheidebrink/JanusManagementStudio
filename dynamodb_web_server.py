"""
Multi-Service Web Server for Electron App Integration

This creates a Flask web server that your Electron app can communicate with
to provide natural language querying capabilities for AWS services:
- DynamoDB
- S3
"""

from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
import json
import sys
import os

# Import your existing agents
from dynamodb_agent import create_dynamodb_agent
from s3_agent import create_s3_agent

app = Flask(__name__)
CORS(app)  # Allow Electron app to make requests

# Initialize the agents
agents = {}

try:
    agents['dynamodb'] = create_dynamodb_agent()
    print("✅ DynamoDB agent initialized successfully")
except Exception as e:
    print(f"❌ Error initializing DynamoDB agent: {e}")
    agents['dynamodb'] = None

try:
    agents['s3'] = create_s3_agent()
    print("✅ S3 agent initialized successfully")
except Exception as e:
    print(f"❌ Error initializing S3 agent: {e}")
    agents['s3'] = None

@app.route('/api/query', methods=['POST'])
def query_service():
    """Handle natural language queries for AWS services."""
    try:
        data = request.get_json()
        query = data.get('query', '')
        service = data.get('service', 'dynamodb')  # Default to DynamoDB for backward compatibility
        
        if not query:
            return jsonify({'error': 'No query provided'}), 400
        
        if service not in agents:
            return jsonify({'error': f'Unknown service: {service}'}), 400
        
        agent = agents[service]
        if not agent:
            return jsonify({'error': f'{service.upper()} agent not initialized. Check AWS credentials.'}), 500
        
        # Use the agent to process the query
        response = agent(query)
        
        # Convert response to string to avoid JSON serialization issues
        response_text = str(response) if response else "No response"
        
        return jsonify({
            'success': True,
            'service': service,
            'query': query,
            'response': response_text
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/query/dynamodb', methods=['POST'])
def query_dynamodb():
    """Handle DynamoDB queries (backward compatibility)."""
    data = request.get_json()
    data['service'] = 'dynamodb'
    return query_service()

@app.route('/api/query/s3', methods=['POST'])
def query_s3():
    """Handle S3 queries."""
    data = request.get_json()
    data['service'] = 's3'
    return query_service()

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'services': {
            'dynamodb': agents['dynamodb'] is not None,
            's3': agents['s3'] is not None
        }
    })

@app.route('/api/suggestions', methods=['GET'])
def get_suggestions():
    """Get example queries users can try."""
    suggestions = {
        'dynamodb': [
            "What DynamoDB tables do I have?",
            "Show me the structure of the users table",
            "Get me 10 items from the products table",
            "Query the orders table for user_id = 12345",
            "Search for items containing 'email'",
            "Analyze the data structure of my logs table"
        ],
        's3': [
            "What S3 buckets do I have?",
            "Show me the contents of my-data bucket",
            "Search for .jpg files in my-photos bucket",
            "Analyze the structure of my-website bucket",
            "What's the size of objects in my-backup bucket?",
            "Show me recent files in my-uploads bucket"
        ]
    }
    
    return jsonify({'suggestions': suggestions})

# Simple test interface (for development)
TEST_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>DynamoDB Agent Test</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
        .chat-container { border: 1px solid #ddd; height: 400px; overflow-y: auto; padding: 10px; margin: 10px 0; }
        .message { margin: 10px 0; padding: 10px; border-radius: 5px; }
        .user-message { background: #e3f2fd; text-align: right; }
        .agent-message { background: #f5f5f5; }
        .input-container { display: flex; gap: 10px; }
        input[type="text"] { flex: 1; padding: 10px; }
        button { padding: 10px 20px; }
        .suggestions { margin: 10px 0; }
        .suggestion { display: inline-block; margin: 5px; padding: 5px 10px; background: #e8f5e8; border-radius: 15px; cursor: pointer; font-size: 12px; }
    </style>
</head>
<body>
    <h1>DynamoDB Natural Language Interface</h1>
    <p>Ask questions about your DynamoDB data in plain English!</p>
    
    <div class="suggestions" id="suggestions">
        <strong>Try these examples:</strong><br>
    </div>
    
    <div class="chat-container" id="chat"></div>
    
    <div class="input-container">
        <input type="text" id="queryInput" placeholder="Ask about your DynamoDB data..." onkeypress="handleKeyPress(event)">
        <button onclick="sendQuery()">Send</button>
    </div>

    <script>
        let suggestions = [];
        
        // Load suggestions
        fetch('/api/suggestions')
            .then(response => response.json())
            .then(data => {
                suggestions = data.suggestions;
                const suggestionsDiv = document.getElementById('suggestions');
                data.suggestions.slice(0, 5).forEach(suggestion => {
                    const span = document.createElement('span');
                    span.className = 'suggestion';
                    span.textContent = suggestion;
                    span.onclick = () => {
                        document.getElementById('queryInput').value = suggestion;
                        sendQuery();
                    };
                    suggestionsDiv.appendChild(span);
                });
            });
        
        function addMessage(content, isUser = false) {
            const chat = document.getElementById('chat');
            const message = document.createElement('div');
            message.className = `message ${isUser ? 'user-message' : 'agent-message'}`;
            message.innerHTML = `<pre>${content}</pre>`;
            chat.appendChild(message);
            chat.scrollTop = chat.scrollHeight;
        }
        
        function sendQuery() {
            const input = document.getElementById('queryInput');
            const query = input.value.trim();
            
            if (!query) return;
            
            addMessage(query, true);
            input.value = '';
            
            // Show loading
            addMessage('🤔 Thinking...');
            
            fetch('/api/query', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ query: query })
            })
            .then(response => response.json())
            .then(data => {
                // Remove loading message
                const chat = document.getElementById('chat');
                chat.removeChild(chat.lastChild);
                
                if (data.success) {
                    addMessage(data.response);
                } else {
                    addMessage(`❌ Error: ${data.error}`);
                }
            })
            .catch(error => {
                // Remove loading message
                const chat = document.getElementById('chat');
                chat.removeChild(chat.lastChild);
                addMessage(`❌ Network error: ${error.message}`);
            });
        }
        
        function handleKeyPress(event) {
            if (event.key === 'Enter') {
                sendQuery();
            }
        }
        
        // Initial health check
        fetch('/api/health')
            .then(response => response.json())
            .then(data => {
                if (data.agent_ready) {
                    addMessage('✅ DynamoDB agent is ready! Ask me anything about your data.');
                } else {
                    addMessage('⚠️ DynamoDB agent not ready. Please check AWS credentials.');
                }
            });
    </script>
</body>
</html>
"""

@app.route('/')
def test_interface():
    """Simple test interface for development."""
    return TEST_HTML

if __name__ == '__main__':
    print("🚀 Starting AWS Services Web Server...")
    print("📊 Your Electron app can now communicate with: http://localhost:5000")
    print("🧪 Test interface available at: http://localhost:5000")
    print("📡 API endpoints:")
    print("  - POST http://localhost:5000/api/query (with service: 'dynamodb' or 's3')")
    print("  - POST http://localhost:5000/api/query/dynamodb")
    print("  - POST http://localhost:5000/api/query/s3")
    print("\nExample API usage:")
    print("curl -X POST http://localhost:5000/api/query \\")
    print("  -H 'Content-Type: application/json' \\")
    print("  -d '{\"service\": \"s3\", \"query\": \"What buckets do I have?\"}'")
    
    app.run(debug=True, host='0.0.0.0', port=5000)