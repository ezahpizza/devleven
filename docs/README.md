# DevFusion ElevenLabs-Twilio Voice Agent

A FastAPI-based integration for connecting Twilio phone calls to ElevenLabs Conversational AI agents with automatic lead capture.

## 🚀 Features

- **Outbound Calls**: Initiate calls with personalized Hindi greetings
- **First Message Override**: Inject client name into agent's greeting
- **Lead Management**: Automatic lead capture from conversations
- **Secure Webhooks**: HMAC signature verification for ElevenLabs webhooks
- **PostgreSQL Database**: Persistent storage for lead information
- **Modular Architecture**: Clean separation of concerns for maintainability

## 📁 Project Structure

```
fastapi-implementation/
├── config.py                  # Configuration management
├── main.py                   # Application entry point
├── inbound_calls.py          # Inbound call handlers (legacy)
├── outbound_calls.py         # Outbound call handlers (legacy - kept for reference)
├── models/                   # Data models
│   ├── call_models.py        # Request/response models
│   └── lead_models.py        # Database models
├── services/                 # Business logic
│   ├── elevenlabs_service.py # ElevenLabs API interactions
│   ├── twilio_service.py     # Twilio API interactions
│   └── lead_service.py       # Lead management
├── database/                 # Database layer
│   └── connection.py         # DB connection & session management
├── routes/                   # API routes
│   ├── outbound_calls.py     # Outbound call endpoints
│   └── webhooks.py           # Webhook handlers
├── handlers/                 # WebSocket handlers
│   └── websocket_handler.py  # Outbound call WebSocket logic
└── utils/                    # Utilities
    └── webhook_security.py   # HMAC verification
```

## 🛠️ Setup

### Prerequisites

- Python 3.8+
- PostgreSQL database
- Twilio account with phone number
- ElevenLabs account with conversational AI agent
- ngrok or similar tunneling service

### Installation

1. **Clone and navigate to the project:**
   ```bash
   cd fastapi-implementation
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment variables:**
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env` and add your credentials:
   - `ELEVENLABS_API_KEY`: Your ElevenLabs API key
   - `ELEVENLABS_AGENT_ID`: Your agent ID
   - `ELEVENLABS_WEBHOOK_SECRET`: Secret from ElevenLabs console
   - `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_PHONE_NUMBER`: From Twilio
   - `DATABASE_URL`: PostgreSQL connection string
   - `NGROK_URL`: Your public URL (from ngrok)

4. **Set up PostgreSQL database:**
   
   Create a database:
   ```sql
   CREATE DATABASE devfusion_calls;
   ```
   
   The tables will be created automatically on first run.

5. **Start the server:**
   ```bash
   python main.py
   ```

6. **Expose with ngrok:**
   ```bash
   ngrok http 8000
   ```
   
   Update `NGROK_URL` in `.env` with the URL provided by ngrok.

## 📞 Making Outbound Calls

### API Endpoint

**POST** `/outbound-call`

**Request Body:**
```json
{
  "number": "+917978268815",
  "client_name": "Prateek"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Call initiated",
  "callSid": "CA1234567890abcdef",
  "clientName": "Prateek",
  "phoneNumber": "+917978268815"
}
```

### Personalized Greeting

The agent will greet the caller with:

**"नमस्ते {client_name}! मैं वनिका बोल रही हूँ Dev Fusion एजेंसी से। कैसे हैं आप? क्या आपने हमारी किसी प्रॉपर्टी के बारे में जानकारी ली थी?"**

Example for `client_name: "Prateek"`:
**"नमस्ते Prateek! मैं वनिका बोल रही हूँ Dev Fusion एजेंसी से। कैसे हैं आप? क्या आपने हमारी किसी प्रॉपर्टी के बारे में जानकारी ली थी?"**

## 🪝 Setting Up ElevenLabs Webhook

1. Go to ElevenLabs Console → Webhooks
2. Create a new webhook with:
   - **Name**: DevFusion Lead Capture
   - **URL**: `https://your-ngrok-url.ngrok.io/elevenlabs-webhook`
   - **Auth Method**: HMAC
   - **Events**: Select `conversation.end`

3. Copy the generated webhook secret and add it to your `.env`:
   ```
   ELEVENLABS_WEBHOOK_SECRET=your_secret_here
   ```

4. Associate the webhook with your agent

## 💾 Lead Data Format

Leads are automatically saved to the database when a conversation ends:

```
CALLER_NAME: Prateek
CALLER_NUMBER: +917978268815
CALL_START_TIME: 2025-09-29 22:45:57 Monday
ENQUIRED_PROPERTY: [Extracted from conversation]
REQUIREMENTS: [Extracted from conversation]
SITE_VISIT_DATE: [Extracted from conversation]
FOLLOW_UP_DATE: [Extracted from conversation]
SPECIAL_NOTES: [Summary and key points]
```

### Database Schema

```python
class Lead(SQLModel, table=True):
    id: int (primary key)
    caller_name: str
    caller_number: str (indexed)
    call_start_time: datetime
    enquired_property: str (optional)
    requirements: str (optional)
    site_visit_date: str (optional)
    follow_up_date: str (optional)
    special_notes: str (optional)
    conversation_id: str (optional)
    call_sid: str (optional)
    created_at: datetime
    updated_at: datetime
```

## 🔒 Security

- **HMAC Signature Verification**: All webhooks from ElevenLabs are verified using HMAC-SHA256
- **Environment Variables**: Sensitive credentials stored securely
- **Database**: Connection pooling with secure PostgreSQL

## 🧪 Testing

### Test Outbound Call

```bash
curl -X POST https://your-ngrok-url.ngrok.io/outbound-call \
  -H "Content-Type: application/json" \
  -d '{
    "number": "+917978268815",
    "client_name": "Prateek"
  }'
```

### Health Check

```bash
curl https://your-ngrok-url.ngrok.io/
```

## 📊 Monitoring

Check logs for:
- Call initiation
- WebSocket connections
- Lead capture
- Webhook verification

```bash
# Watch logs in real-time
python main.py
```

## 🔧 Troubleshooting

### Database Connection Issues
- Verify `DATABASE_URL` is correct
- Ensure PostgreSQL is running
- Check firewall rules

### ElevenLabs Connection Issues
- Verify API key and agent ID
- Check agent is active in console
- Ensure first message override is supported

### Webhook Not Receiving Data
- Verify ngrok is running
- Check webhook URL in ElevenLabs console
- Verify webhook secret matches
- Check HMAC signature verification logs

## 📝 API Documentation

Once running, access interactive API docs at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## 🔄 Migration from Old Version

The old files (`outbound_calls.py`, `elevenlabs_client.py`) are kept for reference but are no longer used. The new modular structure provides:

1. **Better organization**: Separate concerns into models, services, routes
2. **Easier testing**: Each module can be tested independently
3. **Cleaner code**: Removed unused webhook logic and parameters
4. **Database integration**: Automatic lead capture and storage
5. **Enhanced security**: HMAC verification for webhooks

## 📄 License

Proprietary - DevFusion Agency

## 👥 Support

For issues or questions, contact DevFusion technical team.
