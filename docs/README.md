# DevFuzzion ElevenLabs-Twilio Voice Agent

A FastAPI-based integration for connecting Twilio phone calls to ElevenLabs Conversational AI agents with real-time dashboard monitoring, automatic call record management, and RAG-powered knowledge base support.

## Features

- **Outbound Calls**: Initiate single or bulk calls with personalized greetings using ElevenLabs conversational AI
- **Bulk Call Support**: CSV upload and batch processing for bulk outbound campaigns
- **Real-time Dashboard**: WebSocket-powered React dashboard with live call monitoring
- **Call Analytics**: Comprehensive call records with transcripts, sentiment analysis, and conversion tracking
- **Knowledge Base / RAG**: Upload documents to ElevenLabs knowledge base with automatic RAG indexing and agent attachment
- **Secure Webhooks**: HMAC signature verification for ElevenLabs webhooks
- **Post-Call Notifications**: Email and WhatsApp notifications after call completion
- **MongoDB Database**: Persistent storage for call records and analytics
- **Modular Architecture**: Clean separation of concerns for maintainability

## Project Structure

```
eleventwilio/
├── app/
│   ├── config.py                      # Configuration management
│   ├── main.py                        # Application entry point
│   ├── Dockerfile                     # Container configuration
│   ├── models/                        # Data models
│   │   ├── call_models.py             # Request models for API
│   │   └── call_record_models.py      # Call record and webhook models
│   ├── services/                      # Business logic
│   │   ├── elevenlabs_service.py      # ElevenLabs API (calls, knowledge base, RAG)
│   │   ├── twilio_service.py          # Twilio API interactions
│   │   ├── call_record_service.py     # Call record CRUD operations
│   │   ├── email_service.py           # Email notifications (Resend)
│   │   ├── whatsapp_service.py        # WhatsApp notifications (Twilio)
│   │   └── gemini_service.py          # Google Gemini AI integration
│   ├── db/                            # Database layer
│   │   ├── __init__.py                # DB lifecycle management
│   │   └── mongo.py                   # MongoDB connection & collections
│   ├── routes/                        # API routes
│   │   ├── dashboard.py               # Dashboard, calls, and knowledge base APIs
│   │   ├── outbound_calls.py          # TwiML generation endpoints
│   │   └── webhooks.py                # ElevenLabs webhook handlers
│   ├── handlers/                      # WebSocket handlers
│   │   ├── dashboard_ws.py            # Dashboard WebSocket manager
│   │   └── websocket_handler.py       # Twilio-ElevenLabs media stream handler
│   └── utils/                         # Utilities
│       ├── csv_processor.py           # CSV parsing for bulk calls
│       └── webhook_security.py        # HMAC verification
├── client/                            # React frontend (Vite + TypeScript)
│   ├── src/
│   │   ├── components/
│   │   │   ├── calls/                 # Call initiation components
│   │   │   ├── dashboard/             # Dashboard UI components
│   │   │   ├── knowledge-base/        # Knowledge base upload modal
│   │   │   └── ui/                    # shadcn/ui components
│   │   ├── hooks/                     # React hooks (WebSocket, forms)
│   │   ├── pages/                     # Page components
│   │   ├── services/                  # API client services
│   │   └── types/                     # TypeScript type definitions
│   └── package.json                   # Frontend dependencies
├── docs/
│   ├── README.md                      # This file
│   └── AGENT_SYSTEM_PROMPT.md         # ElevenLabs agent configuration
└── pyproject.toml                     # Python dependencies
```

## Setup

### Prerequisites

- Python 3.13+
- Node.js 18+ and pnpm (for frontend)
- MongoDB (local or Atlas)
- Twilio account with phone number
- ElevenLabs account with conversational AI agent
- ngrok or similar tunneling service

### Backend Installation

1. **Clone and navigate to the project:**
   ```bash
   cd eleventwilio
   ```

2. **Install dependencies using uv (recommended) or pip:**
   ```bash
   uv sync
   # or
   pip install -e .
   ```

3. **Configure environment variables:**
   
   Create `.env` file in the `app/` directory with:
   ```env
   # ElevenLabs Configuration
   ELEVENLABS_API_KEY=your_api_key
   ELEVENLABS_AGENT_ID=your_agent_id
   ELEVENLABS_WEBHOOK_SECRET=your_webhook_secret
   
   # Twilio Configuration
   TWILIO_ACCOUNT_SID=your_account_sid
   TWILIO_AUTH_TOKEN=your_auth_token
   TWILIO_PHONE_NUMBER=+1234567890
   
   # Database
   MONGO_URI=mongodb://localhost:27017
   
   # Server
   PORT=8000
   NGROK_URL=https://your-domain.ngrok.io
   ENV=dev
   
   # Optional: Email notifications (Resend)
   RESEND_API_KEY=your_resend_api_key
   ```

4. **Start the backend server:**
   ```bash
   cd app
   uvicorn main:app --reload --port 8000
   ```

5. **Expose with ngrok:**
   ```bash
   ngrok http 8000
   ```
   
   Update `NGROK_URL` in `.env` with the URL provided by ngrok.

### Frontend Installation

1. **Navigate to client directory:**
   ```bash
   cd client
   ```

2. **Install dependencies:**
   ```bash
   pnpm install
   ```

3. **Start development server:**
   ```bash
   pnpm dev
   ```

   The dashboard will be available at `http://localhost:5173`

## Making Outbound Calls

### Single Call

**POST** `/api/initiate_call`

**Request Body:**
```json
{
  "number": "+1234567890",
  "client_name": "John Smith"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Call initiated",
  "callSid": "CA1234567890abcdef",
  "clientName": "John Smith",
  "phoneNumber": "+1234567890"
}
```

### Bulk Calls (JSON)

**POST** `/api/outbound-calls/bulk`

**Request Body:**
```json
{
  "recipients": [
    { "client_name": "John Smith", "number": "+1234567890" },
    { "client_name": "Jane Doe", "number": "+0987654321" }
  ]
}
```

### Bulk Calls (CSV Upload)

**POST** `/api/outbound-calls/bulk-csv`

Upload a CSV file with columns: `name` (or `client_name`) and `phone` (or `number`).

### How It Works

1. Client name and phone number are passed to `/api/initiate_call`
2. System creates a Twilio call with TwiML URL containing these parameters
3. TwiML endpoint establishes WebSocket connection to ElevenLabs
4. ElevenLabs agent receives client context and personalizes the conversation
5. Real-time updates are broadcast to the dashboard via WebSocket

## Knowledge Base / RAG

Upload documents to enhance your ElevenLabs agent with custom knowledge using RAG (Retrieval-Augmented Generation).

### Supported File Types

- PDF (.pdf)
- Text (.txt)
- Word Documents (.doc, .docx)
- Markdown (.md)
- HTML (.html, .htm)

### Upload Document

**POST** `/api/knowledge-base/upload`

Upload a file (multipart/form-data). The document will be:
1. Uploaded to ElevenLabs knowledge base
2. Automatically indexed for RAG
3. Attached to your configured agent

**Response:**
```json
{
  "success": true,
  "message": "Document uploaded, indexing started, and attached to agent",
  "document_id": "abc123",
  "document_name": "product-info.pdf",
  "indexing_status": "in_progress",
  "progress_percentage": 0,
  "attached_to_agent": true,
  "agent_id": "your-agent-id"
}
```

### Check Indexing Status

**GET** `/api/knowledge-base/status/{document_id}`

Poll this endpoint to track RAG indexing progress.

### List Documents

- **GET** `/api/knowledge-base/documents` - List all account documents
- **GET** `/api/knowledge-base/agent-documents` - List documents attached to agent
- **GET** `/api/knowledge-base/document/{document_id}` - Get specific document details

## Setting Up ElevenLabs Webhook

1. Go to ElevenLabs Console → Webhooks
2. Create a new webhook with:
   - **Name**: DevFuzzion Call Complete
   - **URL**: `https://your-ngrok-url.ngrok.io/webhook/call_complete`
   - **Auth Method**: HMAC
   - **Events**: Select `post_call_transcription`

3. Copy the generated webhook secret and add it to your `.env`:
   ```env
   ELEVENLABS_WEBHOOK_SECRET=your_secret_here
   ```

4. Associate the webhook with your conversational AI agent

## Call Records and Analytics

Call records are automatically saved when a conversation ends:

### Call Record Schema

```python
{
    "call_id": str,              # Unique conversation ID
    "client_name": str,          # Client name from initiation
    "transcript": str,           # Full conversation transcript
    "insights": {
        "sentiment": str,        # positive/negative/neutral
        "topics": [str],         # Key topics discussed
        "duration_sec": int      # Call duration in seconds
    },
    "conversion_status": bool,   # Whether call was successful
    "timestamp": datetime        # Call completion time
}
```

### Dashboard API Endpoints

**Call Management:**
- **GET** `/api/calls?page=1&page_size=20` - Paginated call records
- **GET** `/api/call/{call_id}` - Single call record details
- **GET** `/api/calls/summary` - Summary statistics (total calls, conversions, conversion rate)
- **POST** `/api/initiate_call` - Initiate single call
- **POST** `/api/outbound-calls/bulk` - Initiate bulk calls (JSON)
- **POST** `/api/outbound-calls/bulk-csv` - Initiate bulk calls (CSV upload)

**Knowledge Base:**
- **POST** `/api/knowledge-base/upload` - Upload document for RAG
- **GET** `/api/knowledge-base/status/{document_id}` - Check indexing status
- **GET** `/api/knowledge-base/documents` - List all documents
- **GET** `/api/knowledge-base/agent-documents` - List agent documents
- **GET** `/api/knowledge-base/document/{document_id}` - Get document details

**WebSocket:**
- **WebSocket** `/ws/dashboard` - Real-time updates for dashboard

### WebSocket Events

The dashboard WebSocket broadcasts these events:

```javascript
// Call initiated
{
  "type": "call_in_progress",
  "payload": {
    "call_sid": "CA...",
    "client_name": "John Smith",
    "phone_number": "+1234567890",
    "status": "queued"
  }
}

// Call completed and saved
{
  "type": "call_record_created",
  "payload": {
    "call_id": "conv_...",
    "client_name": "John Smith",
    "timestamp": "2025-10-30T12:34:56Z"
  }
}

// Knowledge base document uploaded
{
  "type": "knowledge_base_upload",
  "payload": {
    "document_id": "abc123",
    "document_name": "product-info.pdf",
    "status": "in_progress",
    "progress": 0,
    "attached_to_agent": true
  }
}
```

## Security

- **HMAC Signature Verification**: All webhooks from ElevenLabs are verified using HMAC-SHA256
- **Environment Variables**: Sensitive credentials stored securely in `.env`
- **MongoDB**: Secure connection with authentication support

## Testing

### Test Single Call

```bash
curl -X POST https://your-ngrok-url.ngrok.io/api/initiate_call \
  -H "Content-Type: application/json" \
  -d '{
    "number": "+1234567890",
    "client_name": "John Smith"
  }'
```

### Test Bulk Calls

```bash
curl -X POST https://your-ngrok-url.ngrok.io/api/outbound-calls/bulk \
  -H "Content-Type: application/json" \
  -d '{
    "recipients": [
      {"client_name": "John Smith", "number": "+1234567890"},
      {"client_name": "Jane Doe", "number": "+0987654321"}
    ]
  }'
```

### Test Knowledge Base Upload

```bash
curl -X POST https://your-ngrok-url.ngrok.io/api/knowledge-base/upload \
  -F "file=@/path/to/document.pdf"
```

### Get Call Records

```bash
# Get paginated calls
curl https://your-ngrok-url.ngrok.io/api/calls?page=1&page_size=10

# Get specific call
curl https://your-ngrok-url.ngrok.io/api/call/conv_abc123

# Get summary statistics
curl https://your-ngrok-url.ngrok.io/api/calls/summary
```

### Health Check

```bash
curl https://your-ngrok-url.ngrok.io/
```

## Monitoring

Check logs for:
- Call initiation and status
- WebSocket connection lifecycle
- Call record creation
- Webhook signature verification
- ElevenLabs API interactions
- Knowledge base uploads and RAG indexing

Logs are formatted with timestamps and module names:
```
[2025-10-30 17:01:47] INFO - handlers.websocket_handler - [Handler] Client: John Smith, Phone: +1234567890
[2025-10-30 17:01:48] INFO - handlers.websocket_handler - [ElevenLabs] Conversation ID: conv_abc123
[2025-10-30 17:02:15] INFO - services.call_record_service - [MongoDB] Call record saved: conv_abc123
```

## Troubleshooting

### Database Connection Issues
- Verify `MONGO_URI` is correct
- Ensure MongoDB is running (`mongod --version`)
- Check network connectivity for MongoDB Atlas
- Review connection logs in console

### ElevenLabs Connection Issues
- Verify `ELEVENLABS_API_KEY` and `ELEVENLABS_AGENT_ID` are correct
- Check agent is active in ElevenLabs console
- Ensure signed URL generation is working
- Review WebSocket connection logs

### Twilio Issues
- Verify all Twilio credentials are correct
- Ensure phone number is in E.164 format (+1234567890)
- Check Twilio console for call logs and errors
- Verify ngrok URL is accessible from internet

### Webhook Not Receiving Data
- Verify ngrok is running and URL is up to date
- Check webhook URL in ElevenLabs console matches your endpoint
- Verify webhook secret matches between `.env` and ElevenLabs
- Check HMAC signature verification logs
- Ensure `post_call_transcription` event is selected

### Knowledge Base Issues
- Verify file type is supported (PDF, TXT, DOC, DOCX, MD, HTML)
- Check file size is under 50MB
- Ensure ELEVENLABS_AGENT_ID is set correctly for agent attachment
- Check ElevenLabs console to verify document appears in knowledge base
- Verify document shows the correct dependent agent

### Client Name Shows as [CALLER_NAME]
- This was a known issue - client name needs to be passed via conversation initiation metadata
- Ensure TwiML endpoint properly passes client_name in WebSocket URL
- See AGENT_SYSTEM_PROMPT.md for proper configuration

## API Documentation

Once running, access interactive API docs at:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

## Architecture

### Call Flow

1. **Initiation** (`/api/initiate_call`)
   - Validates request (phone number, client name)
   - Constructs TwiML URL with parameters
   - Calls Twilio API to initiate call
   - Broadcasts "call_in_progress" to dashboard

2. **TwiML Response** (needs to be implemented)
   - Receives call from Twilio
   - Returns TwiML with `<Connect><Stream>` to WebSocket endpoint
   - Passes client_name and phone_number as query params

3. **WebSocket Handler** (`OutboundWebSocketHandler`)
   - Accepts Twilio media stream
   - Gets ElevenLabs signed URL
   - Establishes bidirectional audio streaming
   - Handles conversation lifecycle

4. **Webhook Processing** (`/webhook/call_complete`)
   - Receives ElevenLabs post_call_transcription event
   - Verifies HMAC signature
   - Parses transcript and analysis data
   - Saves call record to MongoDB
   - Broadcasts "call_record_created" to dashboard

### Data Flow

```
Dashboard → POST /api/initiate_call → Twilio API → Phone Call
                                                         ↓
                                                    TwiML URL
                                                         ↓
                                                  WebSocket Handler
                                                         ↓
                                               ElevenLabs ConvAI
                                                         ↓
                                               Conversation Happens
                                                         ↓
                                            POST /webhook/call_complete
                                                         ↓
                                                   MongoDB Storage
                                                         ↓
                                              Dashboard WebSocket Update
```

## Additional Documentation

- **AGENT_SYSTEM_PROMPT.md** - ElevenLabs agent configuration and personality
- **POST_CALL_NOTIFICATIONS.md** - Email and WhatsApp notification setup

## License

Proprietary - DevFuzzion Agency

## Support

For issues or questions, contact DevFuzzion technical team.

---

**Version**: 3.0.0  
**Last Updated**: December 15, 2025
