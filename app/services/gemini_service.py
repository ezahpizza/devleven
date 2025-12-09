"""Service layer for Google Gemini AI integration."""
import logging
import re
from datetime import datetime
from typing import Optional, Tuple

from google import genai
from google.genai import types

from config import Config

logger = logging.getLogger(__name__)


class GeminiService:
    """Service for generating call summaries and extracting follow-up dates using Gemini."""
    
    _client: Optional[genai.Client] = None
    
    @classmethod
    def _get_client(cls) -> genai.Client:
        """Get or create the Gemini client."""
        if cls._client is None:
            api_key = Config.GEMINI_API_KEY
            if not api_key:
                raise ValueError("GEMINI_API_KEY is not configured")
            cls._client = genai.Client(api_key=api_key)
        return cls._client
    
    @staticmethod
    async def analyze_transcript(transcript: str) -> Tuple[str, Optional[str]]:
        """
        Analyze a call transcript to generate a summary and extract follow-up date.
        
        Args:
            transcript: The full call transcript text.
            
        Returns:
            Tuple of (summary, follow_up_date) where follow_up_date is ISO format string or None.
        """
        if not transcript or not transcript.strip():
            logger.warning("[Gemini] Empty transcript provided")
            return "No transcript available for analysis.", None
        
        try:
            client = GeminiService._get_client()
            
            prompt = f"""Analyze the following call transcript and provide:
1. A concise summary (2-3 sentences max) of the key points discussed and outcome.
2. Extract any follow-up date mentioned in the conversation. If a specific date is mentioned, return it. If a relative date like "next week", "tomorrow", "in 3 days" etc. is mentioned, calculate the actual date based on today being {datetime.now().strftime('%Y-%m-%d')}.

Respond in the following exact format:
SUMMARY: <your summary here>
FOLLOW_UP_DATE: <YYYY-MM-DD or NONE if no follow-up date mentioned>

Transcript:
{transcript}"""

            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.3,
                    max_output_tokens=500,
                )
            )
            
            response_text = response.text.strip()
            logger.info(f"[Gemini] Raw response: {response_text}")
            
            # Parse the response
            summary = ""
            follow_up_date = None
            
            # Extract summary
            summary_match = re.search(r'SUMMARY:\s*(.+?)(?=FOLLOW_UP_DATE:|$)', response_text, re.DOTALL)
            if summary_match:
                summary = summary_match.group(1).strip()
            else:
                # Fallback: use the entire response as summary
                summary = response_text[:500] if len(response_text) > 500 else response_text
            
            # Extract follow-up date
            date_match = re.search(r'FOLLOW_UP_DATE:\s*(\d{4}-\d{2}-\d{2}|NONE)', response_text, re.IGNORECASE)
            if date_match:
                date_str = date_match.group(1).upper()
                if date_str != "NONE":
                    try:
                        # Validate the date format
                        datetime.strptime(date_str, '%Y-%m-%d')
                        follow_up_date = date_str
                    except ValueError:
                        logger.warning(f"[Gemini] Invalid date format: {date_str}")
                        follow_up_date = None
            
            logger.info(f"[Gemini] Parsed summary: {summary[:100]}...")
            logger.info(f"[Gemini] Parsed follow_up_date: {follow_up_date}")
            
            return summary, follow_up_date
            
        except Exception as exc:
            logger.error(f"[Gemini] Analysis failed: {exc}")
            return "Unable to generate summary due to an error.", None
