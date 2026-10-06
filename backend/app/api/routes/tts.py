import logging
from fastapi import APIRouter, Query, HTTPException, Response
from app.services.tts_service import tts_service

logger = logging.getLogger("medivoice.tts_route")
router = APIRouter()

@router.get("/tts", summary="Synthesize Text to Speech Audio")
async def get_tts_audio(
    text: str = Query(..., description="Text to synthesize into speech"),
    language: str = Query("en", description="Language code (e.g., ta, hi, te, kn, ml, bn, mr, gu)")
):
    """
    Returns an MP3 audio stream for the given text in the requested Indian language.
    Supports: ta (Tamil), hi (Hindi), te (Telugu), kn (Kannada), ml (Malayalam),
    bn (Bengali), mr (Marathi), gu (Gujarati), pa (Punjabi), en (English), etc.
    """
    if not text.strip():
        raise HTTPException(status_code=400, detail="Text parameter cannot be empty")

    audio_bytes = await tts_service.get_audio_bytes(text=text, language=language)
    if not audio_bytes:
        raise HTTPException(status_code=502, detail="Failed to synthesize audio for this language")

    return Response(
        content=audio_bytes,
        media_type="audio/mpeg",
        headers={
            "Content-Type": "audio/mpeg",
            "Cache-Control": "public, max-age=86400",  # Cache for 24 hours
            "Accept-Ranges": "bytes"
        }
    )
