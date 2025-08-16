# Chat UI to Backend Integration Guide

## Overview
This guide documents the integration between the Chat UI (Next.js frontend) and the Brain LLM backend (FastAPI). The integration enables real-time streaming communication using Server-Sent Events (SSE).

## Architecture

```
Frontend (Next.js) → API Route → Backend (FastAPI) → Database (PostgreSQL)
      ↓                ↓              ↓                    ↓
  Chat Interface → /api/v1/query → /api/v1/query/stream → Chinook DB
```

## Payload Structure

### Frontend to Backend Payload
The frontend sends the following payload structure:

```json
{
  "query_text": "what are the total number of artists",
  "user_id": "b521b8a1-0b9d-45e6-991d-1476c5f6fee8",
  "conversation_id": "cebf932f-addb-48de-91c3-d7d462aa84b8",
  "message_id": "some-new-message-id",
  "chat_history": [
    {
      "role": "user",
      "content": "previous user message"
    },
    {
      "role": "assistant", 
      "content": "previous assistant response"
    }
  ],
  "short_term_memory": [
    "SUMMARY: The table names are case sensitive, use double quotes while generating commands"
  ],
  "model_name": "gemini-2.0-flash",
  "temperature": 0.2,
  "api_key": "xyz",
  "db_connection_info": {
    "db_host": "localhost",
    "db_port": 5432,
    "db_user": "postgres",
    "db_name": "chinook",
    "db_password": "iamaryan15", 
    "db_schema": null
  }
}
```

## Implementation Details

### 1. Frontend Components

#### AnimatedChatPanel.jsx
- **Purpose**: Main chat interface component
- **Key Features**:
  - Real-time message streaming
  - Conversation history management
  - Database connection handling
  - Token usage tracking

#### Key Functions:
- `handleSendMessage()`: Processes user messages and handles streaming responses
- `onUpdateMessage()`: Updates existing messages during streaming
- `onAddMessage()`: Adds new messages to conversation

### 2. API Route (/api/v1/query/route.js)

#### Responsibilities:
- Transform frontend payload to backend format
- Forward requests to FastAPI backend
- Handle streaming responses
- Manage CORS and headers

#### Environment Variables:
```env
NEXT_PUBLIC_BACKEND_URL=http://localhost:8000
GEMINI_API_KEY=your-actual-gemini-api-key-here
DEFAULT_DB_HOST=localhost
DEFAULT_DB_PORT=5432
DEFAULT_DB_USER=postgres
DEFAULT_DB_NAME=chinook
DEFAULT_DB_PASSWORD=iamaryan15
DEFAULT_USER_ID=b521b8a1-0b9d-45e6-991d-1476c5f6fee8
```

### 3. Backend Integration Points

#### Endpoint: `/api/v1/query/stream`
- **Method**: POST
- **Content-Type**: application/json
- **Response**: text/event-stream

#### Response Format:
```javascript
// Content streaming
data: {"type": "content", "content": "partial response text"}

// Token usage tracking
data: {"type": "token_usage", "usage": {"input_tokens": 150, "output_tokens": 75}}

// Processing steps
data: {"type": "processing_step", "step": "Analyzing query intent..."}
```

## Setup Instructions

### 1. Backend Setup
```bash
cd brain_llm
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 2. Frontend Setup
```bash
cd chatUI
npm install
npm run dev
```

### 3. Environment Configuration
Create `.env.local` in chatUI directory with the required environment variables.

## Testing

### Manual Testing
1. Start both backend and frontend servers
2. Open `http://localhost:3000`
3. Send a test message: "what are the total number of artists"
4. Verify streaming response appears in real-time

### Test File
Use `test_connection.html` for direct API testing without the UI.

## Features

### Real-time Streaming
- Server-Sent Events (SSE) for live response streaming
- Incremental message updates
- Processing step indicators

### Conversation Management
- Persistent conversation history
- Auto-generated conversation titles
- Message threading with unique IDs

### Database Integration
- Dynamic database connection configuration
- Support for PostgreSQL Chinook database
- Table name case sensitivity handling

### Token Tracking
- Real-time token usage monitoring
- Input/output token breakdown
- Cost estimation capabilities

## Error Handling

### Frontend Error Handling
- Network connection errors
- Backend service unavailability
- Malformed response handling
- User feedback via toast notifications

### Backend Error Handling
- Database connection failures
- LLM API errors
- Schema introspection fallbacks
- Structured error responses

## Security Considerations

### API Keys
- Environment variable storage
- Server-side key management
- No client-side key exposure

### Database Credentials
- Encrypted storage recommendations
- Connection string security
- User permission restrictions

## Troubleshooting

### Common Issues

1. **CORS Errors**
   - Verify CORS middleware configuration
   - Check allowed origins and headers

2. **Streaming Issues**
   - Ensure correct Content-Type headers
   - Verify SSE parsing logic
   - Check network proxy settings

3. **Database Connection**
   - Verify PostgreSQL service status
   - Check connection credentials
   - Validate database schema access

4. **Environment Variables**
   - Confirm .env.local file presence
   - Verify variable naming (NEXT_PUBLIC_ prefix)
   - Check development vs production environments

## Performance Optimization

### Frontend Optimizations
- Message debouncing
- Efficient re-rendering
- Virtual scrolling for long conversations

### Backend Optimizations
- Connection pooling
- Schema caching
- Response compression

## Future Enhancements

### Planned Features
- User authentication
- Multi-database support
- Custom model selection
- Conversation export/import
- Advanced visualization components

### Scalability Considerations
- Load balancing
- Database sharding
- CDN integration
- Microservice architecture

## Monitoring and Logging

### Frontend Logging
- Console debugging
- Error tracking
- User interaction analytics

### Backend Logging
- Structured JSON logging
- Request/response tracing
- Performance metrics
- Error aggregation

---

## Contact and Support

For technical support or questions about this integration, please refer to the development team or check the project documentation.
