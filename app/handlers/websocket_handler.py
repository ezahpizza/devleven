"""WebSocket handler for outbound calls."""
import asyncio
import json
import logging
from typing import Optional
from fastapi import WebSocket, WebSocketDisconnect
import websockets

from services.elevenlabs_service import ElevenLabsService

logger = logging.getLogger(__name__)


class OutboundWebSocketHandler:
    """Handles WebSocket communication for outbound calls."""
    
    def __init__(self, websocket: WebSocket, client_name: str = "", phone_number: str = ""):
        """
        Initialize the handler.
        
        Args:
            websocket: WebSocket connection from Twilio
            client_name: Client name from query parameters
            phone_number: Phone number from query parameters
        """
        self.websocket = websocket
        self.stream_sid: Optional[str] = None
        self.call_sid: Optional[str] = None
        self.conversation_id: Optional[str] = None
        self.elevenlabs_ws: Optional[websockets.WebSocketClientProtocol] = None
        self.client_name: str = client_name
        self.phone_number: str = phone_number
        self.elevenlabs_closed: bool = False  # Track if ElevenLabs connection is closed
    
    async def handle(self):
        """Handle the WebSocket connection."""
        await self.websocket.accept()
        logger.info("[Handler] Twilio connected to outbound media stream")
        logger.info(f"[Handler] Client: {self.client_name}, Phone: {self.phone_number}")
        
        try:
            # Connect to ElevenLabs immediately using signed URL
            await self._setup_elevenlabs()
            
            # Handle the connection with concurrent tasks
            await self._handle_connection()
        
        except Exception as e:
            logger.error(f"[Handler] Error in outbound media stream: {e}")
        
        finally:
            await self._cleanup()
    
    async def _setup_elevenlabs(self):
        """Set up ElevenLabs connection using authenticated signed URL."""
        try:
            signed_url = await ElevenLabsService.get_signed_url()
            
            self.elevenlabs_ws = await asyncio.wait_for(
                websockets.connect(
                    signed_url,
                    ping_interval=20,
                    ping_timeout=20,
                    close_timeout=10
                ),
                timeout=10.0
            )
            
        except asyncio.TimeoutError:
            logger.error("[ElevenLabs] Connection timeout")
            raise
        except Exception as e:
            logger.error(f"[ElevenLabs] Connection failed: {e}")
            raise
    
    async def _handle_connection(self):
        """Handle the WebSocket connection lifecycle."""
        # Start bidirectional communication
        await asyncio.gather(
            self._handle_elevenlabs_messages(),
            self._handle_twilio_messages()
        )
    
    async def _handle_elevenlabs_messages(self):
        """Handle messages from ElevenLabs and forward to Twilio."""
        try:
            async for message in self.elevenlabs_ws:
                try:
                    data = json.loads(message)
                    msg_type = data.get("type")
                    
                    # Handle ping/pong
                    if msg_type == "ping":
                        event_id = data.get("ping_event", {}).get("event_id")
                        if event_id:
                            pong_response = {
                                "type": "pong",
                                "event_id": event_id
                            }
                            await self.elevenlabs_ws.send(json.dumps(pong_response))
                            continue
                    
                    await self._process_elevenlabs_message(data)
                
                except json.JSONDecodeError as e:
                    logger.error(f"[ElevenLabs] JSON decode error: {e}")
                except Exception as e:
                    logger.error(f"[ElevenLabs] Error processing message: {e}")
        
        except websockets.exceptions.ConnectionClosed as e:
            self.elevenlabs_closed = True  # Mark ElevenLabs as closed
            
            # Give Twilio time to flush audio
            await asyncio.sleep(1)
            try:
                # Only try to send if websocket is still connected
                if self.websocket.client_state.name == "CONNECTED":
                    await self.websocket.send_text(json.dumps({"event": "stop"}))
                    await self.websocket.close()
            except Exception:
                pass
        
        except Exception as e:
            logger.error(f"[ElevenLabs] Error: {e}")
    
    async def _handle_twilio_messages(self):
        """Handle messages from Twilio and forward to ElevenLabs."""
        try:
            while True:
                # Check if ElevenLabs connection is closed
                if self.elevenlabs_closed:
                    break
                
                message = await self.websocket.receive_text()
                data = json.loads(message)
                
                event = data.get("event")
                
                if event == "start":
                    self.stream_sid = data["start"]["streamSid"]
                    self.call_sid = data["start"]["callSid"]
                
                elif event == "media":
                    # Only forward audio if ElevenLabs is still connected
                    if self.elevenlabs_ws and not self.elevenlabs_closed:
                        try:
                            # Forward audio to ElevenLabs
                            audio_payload = data["media"]["payload"]
                            audio_message = {
                                "user_audio_chunk": audio_payload
                            }
                            await self.elevenlabs_ws.send(json.dumps(audio_message))
                        except websockets.exceptions.ConnectionClosed:
                            # ElevenLabs closed, mark it and stop forwarding
                            self.elevenlabs_closed = True
                            break
                        except Exception as e:
                            logger.error(f"[ElevenLabs] Failed to send audio: {e}")
                            # Don't continue if there's a persistent error
                            if "received 1000" in str(e) or "then sent 1000" in str(e):
                                self.elevenlabs_closed = True
                                break
                
                elif event == "stop":
                    if self.elevenlabs_ws and not self.elevenlabs_closed:
                        try:
                            await self.elevenlabs_ws.close()
                            self.elevenlabs_closed = True
                        except:
                            pass
                    break
        
        except WebSocketDisconnect:
            pass
        except Exception as e:
            logger.error(f"[Twilio] Error: {e}")
    
    async def _process_elevenlabs_message(self, message: dict):
        """
        Process messages from ElevenLabs.
        
        Args:
            message: Message from ElevenLabs
        """
        msg_type = message.get("type")
        
        if msg_type == "conversation_initiation_metadata":
            metadata = message.get("conversation_initiation_metadata_event", {})
            if metadata.get("conversation_id"):
                self.conversation_id = metadata["conversation_id"]
                logger.info(f"[ElevenLabs] Conversation ID: {self.conversation_id}")
        
        elif msg_type == "audio":
            # Handle audio chunks
            audio_base64 = None
            if message.get("audio", {}).get("chunk"):
                audio_base64 = message["audio"]["chunk"]
            elif message.get("audio_event", {}).get("audio_base_64"):
                audio_base64 = message["audio_event"]["audio_base_64"]
            
            if audio_base64 and self.stream_sid:
                audio_data = {
                    "event": "media",
                    "streamSid": self.stream_sid,
                    "media": {
                        "payload": audio_base64
                    }
                }
                await self.websocket.send_text(json.dumps(audio_data))
        
        elif msg_type == "interruption":
            if self.stream_sid:
                clear_message = {
                    "event": "clear",
                    "streamSid": self.stream_sid
                }
                await self.websocket.send_text(json.dumps(clear_message))
        
        elif msg_type == "user_transcript":
            user_text = message.get("user_transcription_event", {}).get("user_transcript", "")
            if user_text:
                logger.info(f"[User] {user_text}")
        
        elif msg_type == "agent_response":
            agent_text = message.get("agent_response_event", {}).get("agent_response", "")
            if agent_text:
                logger.info(f"[Agent] {agent_text}")
    
    async def _cleanup(self):
        """Cleanup resources."""
        if self.elevenlabs_ws and not self.elevenlabs_closed:
            try:
                await self.elevenlabs_ws.close()
                self.elevenlabs_closed = True
            except:
                pass
        try:
            await self.websocket.close()
        except:
            pass
        logger.info("[Handler] Connections closed")
