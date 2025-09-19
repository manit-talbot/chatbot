# Chatbot API Documentation

This FastAPI application provides REST endpoints for the Knowledge Base Assistant chatbot.

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Set Environment Variables
Create a `.env` file with:
```bash
# Database
POSTGRES_URI=your_postgres_connection_string
DEFAULT_SCHEMA=public

# AWS
KB_ID=your_bedrock_knowledge_base_id
DYNAMODB_TABLE_NAME=chatbot-conversations
AWS_REGION=us-east-1

# API (optional)
API_HOST=0.0.0.0
API_PORT=8000
API_DEBUG=false
```

### 3. Start the API Server
```bash
python chatbot_api.py
```

The server will start at `http://localhost:8000`

### 4. View API Documentation
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 📡 API Endpoints

### POST /chat
Send a message and get a chatbot response.

**Request Body:**
```json
{
  "message": "What is the purpose of this knowledge base?",
  "session_id": "optional-session-id"
}
```

**Response:**
```json
{
  "session_id": "api_session_20241217_143022_abc12345",
  "message": "What is the purpose of this knowledge base?",
  "response": "The knowledge base contains...",
  "timestamp": "2024-12-17T14:30:22.123456",
  "agents_used": ["Knowledge Base", "SQL Assistant"]
}
```

**Usage Examples:**
```bash
# New conversation
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello, how can you help me?"}'

# Continue conversation
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{"message": "Tell me more", "session_id": "api_session_20241217_143022_abc12345"}'
```

### GET /chathistory/{session_id}
Get chat history for a specific session.

**Parameters:**
- `session_id` (path): The session ID to retrieve history for
- `limit` (query, optional): Maximum number of conversations (default: 50)

**Response:**
```json
{
  "session_id": "api_session_20241217_143022_abc12345",
  "conversations": [
    {
      "timestamp": "2024-12-17T14:30:22.123456",
      "user": "What is the purpose of this knowledge base?",
      "ai": "The knowledge base contains..."
    }
  ],
  "total_count": 1
}
```

**Usage Example:**
```bash
curl "http://localhost:8000/chathistory/api_session_20241217_143022_abc12345?limit=10"
```

### GET /health
Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "knowledge_base_agent": "available",
  "sql_agent": "available",
  "timestamp": "2024-12-17T14:30:22.123456"
}
```

### GET /
Root endpoint with API information.

**Response:**
```json
{
  "message": "Chatbot API",
  "version": "1.0.0",
  "endpoints": {
    "chat": "POST /chat - Send a message and get a response",
    "history": "GET /chathistory/{session_id} - Get chat history for a session",
    "health": "GET /health - Health check"
  },
  "documentation": "/docs"
}
```

## 🧪 Testing

### Run Test Client
```bash
python test_api_client.py
```

### Manual Testing with curl
```bash
# Health check
curl http://localhost:8000/health

# Start new conversation
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello!"}'

# Get conversation history (replace with actual session_id)
curl "http://localhost:8000/chathistory/your-session-id"
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `POSTGRES_URI` | PostgreSQL connection string | Required |
| `DEFAULT_SCHEMA` | Default database schema | `public` |
| `KB_ID` | AWS Bedrock Knowledge Base ID | Required |
| `DYNAMODB_TABLE_NAME` | DynamoDB table name | `chatbot-conversations` |
| `AWS_REGION` | AWS region | `us-east-1` |
| `API_HOST` | API server host | `0.0.0.0` |
| `API_PORT` | API server port | `8000` |
| `API_DEBUG` | Enable debug mode | `false` |

### DynamoDB Table Schema

The conversation history is stored in DynamoDB with the following schema:

- **Partition Key**: `session_id` (String)
- **Sort Key**: `timestamp` (String)
- **Attributes**:
  - `user_question` (String)
  - `ai_response` (String)
  - `ttl` (Number) - Time-to-live for automatic cleanup

## 🚨 Error Handling

The API returns appropriate HTTP status codes:

- `200` - Success
- `400` - Bad Request (invalid input)
- `500` - Internal Server Error

Error responses include details:
```json
{
  "error": "Internal server error",
  "detail": "Specific error message"
}
```

## 🔒 Security Notes

- Configure CORS properly for production
- Use proper authentication/authorization
- Validate and sanitize all inputs
- Use HTTPS in production
- Set appropriate AWS IAM permissions

## 📊 Monitoring

- Check `/health` endpoint for service status
- Monitor DynamoDB metrics
- Check application logs for errors
- Monitor API response times

## 🛠️ Development

### Running in Development Mode
```bash
export API_DEBUG=true
python chatbot_api.py
```

### Adding New Endpoints
1. Add the endpoint function to `chatbot_api.py`
2. Define Pydantic models for request/response
3. Add error handling
4. Update this documentation
5. Add tests to `test_api_client.py`
