import logging

from groq import Groq

from src.config import config

logger = logging.getLogger(__name__)

_MODEL = "llama-3.3-70b-versatile"
_MAX_LYRICS_CHARS = 3000  # keep within token limits


def analyze_track(track_name: str, artist_name: str, lyrics: str | None) -> str | None:
    """Return a Turkish emotional analysis of why someone added this track.

    Returns None if GROQ_API_KEY is not configured or the API call fails.
    """
    if not config.groq_api_key:
        logger.warning("GROQ_API_KEY not set — skipping analysis.")
        return None

    if lyrics:
        lyrics_section = f"Şarkı sözleri:\n{lyrics[:_MAX_LYRICS_CHARS]}"
    else:
        lyrics_section = "Şarkı sözlerine ulaşılamadı."

    prompt = (
        f'"{track_name}" adlı şarkı "{artist_name}" sanatçısına ait. '
        f"Bu şarkı bir playliste yeni eklendi.\n\n"
        f"{lyrics_section}\n\n"
        "Bu şarkının duygusal içeriğini ve sözlerini analiz ederek, "
        "bu şarkıyı playliste ekleyen kişinin o an nasıl hissediyor olabileceğini "
        "Türkçe olarak açıkla. Tam olarak 2 cümle yaz. "
        "Yorumunu yaparken pesimist bir bakış açısı benimse: duygulardan yara almış, "
        "olayların hep karanlık tarafını gören biri gibi konuş. "
        "Kaba olma ama umursamamazlık değil, gerçekçi bir karamsarlık olsun. "
        "Klişelerden kaçın, doğal bir dil kullan. "
        '"Bu şarkıyı eklediği için..." veya "Bu kişi şu an..." gibi bir girişle başla.'
    )

    client = Groq(api_key=config.groq_api_key)
    response = client.chat.completions.create(
        model=_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.8,
        max_tokens=300,
    )

    return response.choices[0].message.content.strip()
