/**
 * DynamoDB Agent Integration for Electron App
 * 
 * This module provides easy integration between your Electron app and the DynamoDB agent.
 * Add this to your Electron renderer process to enable natural language DynamoDB queries.
 */

class DynamoDBAgent {
    constructor(serverUrl = 'http://localhost:5000') {
        this.serverUrl = serverUrl;
        this.isReady = false;
        this.checkHealth();
    }

    /**
     * Check if the DynamoDB agent server is ready
     */
    async checkHealth() {
        try {
            const response = await fetch(`${this.serverUrl}/api/health`);
            const data = await response.json();
            this.isReady = data.agent_ready;
            return data;
        } catch (error) {
            console.error('DynamoDB agent health check failed:', error);
            this.isReady = false;
            return { status: 'error', error: error.message };
        }
    }

    /**
     * Send a natural language query to the DynamoDB agent
     * @param {string} query - Natural language query about DynamoDB data
     * @returns {Promise<Object>} Response from the agent
     */
    async query(query) {
        if (!this.isReady) {
            throw new Error('DynamoDB agent is not ready. Check server connection and AWS credentials.');
        }

        try {
            const response = await fetch(`${this.serverUrl}/api/query`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ query })
            });

            const data = await response.json();
            
            if (!data.success) {
                throw new Error(data.error || 'Query failed');
            }

            return data;
        } catch (error) {
            console.error('DynamoDB query failed:', error);
            throw error;
        }
    }

    /**
     * Get example queries that users can try
     * @returns {Promise<Array>} Array of example query strings
     */
    async getSuggestions() {
        try {
            const response = await fetch(`${this.serverUrl}/api/suggestions`);
            const data = await response.json();
            return data.suggestions;
        } catch (error) {
            console.error('Failed to get suggestions:', error);
            return [];
        }
    }
}

/**
 * Create a chat interface for DynamoDB queries
 * @param {HTMLElement} container - Container element to render the chat interface
 * @param {DynamoDBAgent} agent - DynamoDB agent instance
 */
function createDynamoDBChatInterface(container, agent) {
    container.innerHTML = `
        <div class="dynamodb-chat">
            <div class="chat-header">
                <h3>🗃️ DynamoDB Assistant</h3>
                <div class="status" id="agent-status">Checking connection...</div>
            </div>
            
            <div class="suggestions-container" id="suggestions-container">
                <div class="suggestions-label">Try these examples:</div>
                <div class="suggestions" id="suggestions"></div>
            </div>
            
            <div class="chat-messages" id="chat-messages"></div>
            
            <div class="chat-input-container">
                <input type="text" id="chat-input" placeholder="Ask about your DynamoDB data..." />
                <button id="send-button">Send</button>
            </div>
        </div>
    `;

    // Add CSS styles
    const style = document.createElement('style');
    style.textContent = `
        .dynamodb-chat {
            display: flex;
            flex-direction: column;
            height: 100%;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        }
        
        .chat-header {
            padding: 15px;
            background: #f8f9fa;
            border-bottom: 1px solid #dee2e6;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .chat-header h3 {
            margin: 0;
            color: #495057;
        }
        
        .status {
            font-size: 12px;
            padding: 4px 8px;
            border-radius: 12px;
            background: #ffc107;
            color: #000;
        }
        
        .status.ready {
            background: #28a745;
            color: white;
        }
        
        .status.error {
            background: #dc3545;
            color: white;
        }
        
        .suggestions-container {
            padding: 10px 15px;
            background: #f8f9fa;
            border-bottom: 1px solid #dee2e6;
        }
        
        .suggestions-label {
            font-size: 12px;
            color: #6c757d;
            margin-bottom: 8px;
        }
        
        .suggestions {
            display: flex;
            flex-wrap: wrap;
            gap: 6px;
        }
        
        .suggestion {
            font-size: 11px;
            padding: 4px 8px;
            background: #e9ecef;
            border-radius: 12px;
            cursor: pointer;
            transition: background-color 0.2s;
        }
        
        .suggestion:hover {
            background: #dee2e6;
        }
        
        .chat-messages {
            flex: 1;
            overflow-y: auto;
            padding: 15px;
            background: white;
        }
        
        .message {
            margin-bottom: 15px;
            max-width: 80%;
        }
        
        .message.user {
            margin-left: auto;
            text-align: right;
        }
        
        .message-content {
            padding: 10px 15px;
            border-radius: 18px;
            font-size: 14px;
            line-height: 1.4;
        }
        
        .message.user .message-content {
            background: #007bff;
            color: white;
        }
        
        .message.agent .message-content {
            background: #f8f9fa;
            color: #495057;
            white-space: pre-wrap;
            font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
            font-size: 12px;
        }
        
        .chat-input-container {
            padding: 15px;
            background: #f8f9fa;
            border-top: 1px solid #dee2e6;
            display: flex;
            gap: 10px;
        }
        
        #chat-input {
            flex: 1;
            padding: 10px 15px;
            border: 1px solid #ced4da;
            border-radius: 20px;
            outline: none;
            font-size: 14px;
        }
        
        #chat-input:focus {
            border-color: #007bff;
            box-shadow: 0 0 0 2px rgba(0, 123, 255, 0.25);
        }
        
        #send-button {
            padding: 10px 20px;
            background: #007bff;
            color: white;
            border: none;
            border-radius: 20px;
            cursor: pointer;
            font-size: 14px;
            transition: background-color 0.2s;
        }
        
        #send-button:hover {
            background: #0056b3;
        }
        
        #send-button:disabled {
            background: #6c757d;
            cursor: not-allowed;
        }
    `;
    document.head.appendChild(style);

    // Get DOM elements
    const statusEl = container.querySelector('#agent-status');
    const suggestionsEl = container.querySelector('#suggestions');
    const messagesEl = container.querySelector('#chat-messages');
    const inputEl = container.querySelector('#chat-input');
    const sendButton = container.querySelector('#send-button');

    // Initialize
    async function initialize() {
        try {
            const health = await agent.checkHealth();
            
            if (health.agent_ready) {
                statusEl.textContent = 'Ready';
                statusEl.className = 'status ready';
                
                // Load suggestions
                const suggestions = await agent.getSuggestions();
                suggestions.slice(0, 6).forEach(suggestion => {
                    const span = document.createElement('span');
                    span.className = 'suggestion';
                    span.textContent = suggestion;
                    span.onclick = () => {
                        inputEl.value = suggestion;
                        sendQuery();
                    };
                    suggestionsEl.appendChild(span);
                });
                
                addMessage('👋 Hi! I can help you query your DynamoDB data. Try asking me something!', false);
            } else {
                statusEl.textContent = 'Not Ready';
                statusEl.className = 'status error';
                addMessage('⚠️ DynamoDB agent is not ready. Please check AWS credentials and server connection.', false);
            }
        } catch (error) {
            statusEl.textContent = 'Connection Error';
            statusEl.className = 'status error';
            addMessage(`❌ Connection error: ${error.message}`, false);
        }
    }

    function addMessage(content, isUser = false) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${isUser ? 'user' : 'agent'}`;
        
        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        contentDiv.textContent = content;
        
        messageDiv.appendChild(contentDiv);
        messagesEl.appendChild(messageDiv);
        messagesEl.scrollTop = messagesEl.scrollHeight;
    }

    async function sendQuery() {
        const query = inputEl.value.trim();
        if (!query) return;

        addMessage(query, true);
        inputEl.value = '';
        sendButton.disabled = true;

        // Show thinking message
        addMessage('🤔 Analyzing your request...');

        try {
            const response = await agent.query(query);
            
            // Remove thinking message
            messagesEl.removeChild(messagesEl.lastChild);
            
            addMessage(response.response);
        } catch (error) {
            // Remove thinking message
            messagesEl.removeChild(messagesEl.lastChild);
            
            addMessage(`❌ Error: ${error.message}`);
        } finally {
            sendButton.disabled = false;
            inputEl.focus();
        }
    }

    // Event listeners
    sendButton.onclick = sendQuery;
    inputEl.onkeypress = (e) => {
        if (e.key === 'Enter') {
            sendQuery();
        }
    };

    // Initialize the interface
    initialize();
}

// Export for use in Electron app
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { DynamoDBAgent, createDynamoDBChatInterface };
} else {
    window.DynamoDBAgent = DynamoDBAgent;
    window.createDynamoDBChatInterface = createDynamoDBChatInterface;
}

// Example usage:
/*
// In your Electron renderer process:
const agent = new DynamoDBAgent('http://localhost:5000');
const container = document.getElementById('dynamodb-container');
createDynamoDBChatInterface(container, agent);
*/