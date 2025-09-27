# 🧠 MANAS AI Chat History System

## Overview
The enhanced MANAS AI Chat History system provides comprehensive conversation storage, retrieval, and synchronization between Django database and Supabase for persistent chat experiences.

## ✨ Features

### 1. Enhanced Message Storage
- **Django Database**: Primary storage for all chat messages
- **Supabase Sync**: Automatic synchronization for enhanced persistence
- **Message Metadata**: Tracks AI model used, companion type, timestamps
- **Conversation Context**: Maintains conversation flow and context

### 2. Chat History Retrieval
- **Individual Session History**: Get complete conversation for specific session
- **All Sessions Overview**: List all chat sessions with metadata
- **Message Filtering**: Retrieve messages by type, companion, or time range
- **Companion Detection**: Automatic companion type detection from session titles

### 3. Supabase Integration
- **Bidirectional Sync**: Django ↔ Supabase message synchronization
- **Session Metadata**: Sync session information and statistics
- **Error Resilience**: Continues working even if Supabase is unavailable
- **Automatic Backfill**: Syncs missing messages when retrieving history

## 🛠 API Endpoints

### Get Chat History
```
GET /api/v1/chat/manas/sessions/{session_id}/history/
```
**Response:**
```json
{
  "success": true,
  "session": {
    "id": "uuid",
    "title": "Session Title",
    "companion": {
      "name": "Priya",
      "emoji": "💖",
      "color": "#FF6B9D"
    },
    "message_count": 10,
    "last_activity": "2024-01-01T12:00:00Z",
    "created_at": "2024-01-01T10:00:00Z",
    "status": "active"
  },
  "messages": [
    {
      "id": "uuid",
      "content": "Hello, I'm feeling anxious...",
      "sender": "user",
      "message_type": "user",
      "timestamp": "2024-01-01T10:01:00Z",
      "ai_model_used": null
    },
    {
      "id": "uuid", 
      "content": "I understand you're feeling anxious...",
      "sender": "ai",
      "message_type": "ai",
      "timestamp": "2024-01-01T10:01:30Z",
      "ai_model_used": "gemini-1.5-flash"
    }
  ],
  "supabase_synced": true
}
```

### Get All Chat Sessions
```
GET /api/v1/chat/manas/sessions/all/
```
**Response:**
```json
{
  "success": true,
  "total_sessions": 5,
  "sessions": [
    {
      "id": "uuid",
      "title": "Priya - Emotional Support Chat",
      "companion": {
        "name": "Priya",
        "emoji": "💖",
        "color": "#FF6B9D",
        "type": "priya"
      },
      "message_count": 12,
      "created_at": "2024-01-01T10:00:00Z",
      "updated_at": "2024-01-01T12:00:00Z",
      "last_message": {
        "content": "Thank you for sharing that with me...",
        "timestamp": "2024-01-01T12:00:00Z",
        "type": "ai"
      },
      "status": "active"
    }
  ]
}
```

## 🔧 Implementation Details

### Database Schema
- **ChatSession**: Session metadata, companion info, timestamps
- **Message**: Individual messages with type, content, AI model info
- **Supabase Tables**: Mirror Django structure for enhanced features

### Companion Detection
The system detects companion types from session titles:
- "Arjun" → Academic support companion
- "Priya" → Emotional support companion  
- "Vikram" → Crisis support companion
- Default → Priya for emotional support

### Message Types
- `user`: Messages from the user
- `ai`: Responses from AI companions
- `system`: System messages (welcome, notifications)

### Supabase Tables Structure

#### manas_messages
```sql
CREATE TABLE manas_messages (
  id UUID PRIMARY KEY,
  session_id UUID NOT NULL,
  content TEXT NOT NULL,
  message_type VARCHAR(10) NOT NULL,
  companion_type VARCHAR(20),
  ai_model_used VARCHAR(50),
  timestamp TIMESTAMPTZ NOT NULL,
  user_id UUID
);
```

#### manas_sessions
```sql
CREATE TABLE manas_sessions (
  id UUID PRIMARY KEY,
  title TEXT,
  companion_type VARCHAR(20),
  message_count INTEGER DEFAULT 0,
  last_activity TIMESTAMPTZ,
  user_id UUID
);
```

## 🧪 Testing

Run the comprehensive test suite:
```bash
python test_chat_history.py
```

The test covers:
- ✅ Session creation with different companions
- ✅ Message sending and AI responses
- ✅ Chat history retrieval with full metadata
- ✅ Session listing and overview
- ✅ Supabase synchronization verification

## 🚀 Usage Examples

### Frontend Integration
```javascript
// Get chat history
const response = await fetch(`/api/v1/chat/manas/sessions/${sessionId}/history/`);
const history = await response.json();

// Display messages
history.messages.forEach(msg => {
  displayMessage(msg.content, msg.sender, msg.timestamp);
});

// Show session info
displaySessionInfo({
  companion: history.session.companion,
  messageCount: history.session.message_count,
  lastActivity: history.session.last_activity
});
```

### Get All Sessions for History Panel
```javascript
// Get all sessions for history sidebar
const response = await fetch('/api/v1/chat/manas/sessions/all/');
const { sessions } = await response.json();

// Create history list
const historyList = sessions.map(session => ({
  id: session.id,
  title: session.title,
  companion: session.companion,
  lastMessage: session.last_message?.content,
  messageCount: session.message_count
}));
```

## 🔐 Security & Permissions

- **Public Access**: Currently allows public access for testing
- **Authentication**: Can be enabled by changing `@permission_classes([permissions.IsAuthenticated])`
- **Session Isolation**: Sessions are isolated by user when authentication is enabled
- **Data Privacy**: Messages are stored securely with proper user association

## 📊 Monitoring & Logging

The system includes comprehensive logging:
- Message creation and retrieval
- Supabase synchronization status
- Error handling and recovery
- Performance metrics for history retrieval

## 🔄 Synchronization Process

1. **Message Creation**: New messages saved to Django DB
2. **Immediate Sync**: Attempt to sync to Supabase
3. **History Retrieval**: Check for missing messages in Supabase
4. **Backfill Sync**: Sync any missing messages during history requests
5. **Error Handling**: Continue operation even if Supabase is unavailable

## 🎯 Benefits

- **Persistent History**: Messages survive across sessions and deployments
- **Enhanced Features**: Supabase enables advanced analytics and features
- **Reliability**: Dual storage ensures data persistence
- **Performance**: Efficient retrieval with proper indexing
- **Scalability**: Prepared for future enhancements and multi-user support

## 🔮 Future Enhancements

- **Search**: Full-text search across conversation history
- **Export**: Export conversations in various formats
- **Analytics**: Conversation insights and statistics
- **Backup**: Automated backup and recovery systems
- **Multi-user**: Enhanced user isolation and permissions