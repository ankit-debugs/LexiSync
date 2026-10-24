import json
import asyncio
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.conf import settings

logger = logging.getLogger(__name__)


class RoomConsumer(AsyncWebsocketConsumer):
    """
    Handles all WebSocket traffic for a room:
      - WebRTC signalling (offer/answer/ICE) for PeerJS video
      - Transcript lines from Deepgram STT
      - Grammar corrections from Gemini
      - Subtitle broadcasts to both peers
    """

    async def connect(self):
        self.room_id = self.scope["url_route"]["kwargs"]["room_id"]
        self.group_name = f"room_{self.room_id}"
        self.user = self.scope["user"]

        if not self.user.is_authenticated:
            await self.close()
            return

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

        # Announce arrival to the other peer
        await self.channel_layer.group_send(
            self.group_name,
            {
                "type": "peer_joined",
                "username": self.user.username,
                "channel": self.channel_name,
            },
        )

    async def disconnect(self, close_code):
        await self.channel_layer.group_send(
            self.group_name,
            {"type": "peer_left", "username": self.user.username},
        )
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    # ------------------------------------------------------------------ #
    #  Receive from browser                                                #
    # ------------------------------------------------------------------ #

    async def receive(self, text_data):
        data = json.loads(text_data)
        msg_type = data.get("type")
        if msg_type == "transcript":
            logger.warning(
                "[grammar-debug] Transcript received from browser [%s] msg_id=%s text=%s",
                self.user.username,
                data.get("msg_id", ""),
                data.get("text", "")[:80],
            )

        handlers = {
            # WebRTC signalling
            "webrtc_offer": self.handle_webrtc_relay,
            "webrtc_answer": self.handle_webrtc_relay,
            "webrtc_ice": self.handle_webrtc_relay,
            "peer_ready": self.handle_peer_ready,
            # STT + AI pipeline
            "transcript": self.handle_transcript,
        }

        handler = handlers.get(msg_type)
        if handler:
            await handler(data)
        else:
            logger.warning("Unknown message type: %s", msg_type)

    async def handle_peer_ready(self, data):
        """Broadcast a peer's PeerJS ID to everyone else in the room."""
        await self.channel_layer.group_send(
            self.group_name,
            {
                "type": "peer_ready_broadcast",
                "peer_id": data.get("peer_id"),
                "role": data.get("role"),
                "sender_channel": self.channel_name,
            },
        )

    async def handle_webrtc_relay(self, data):
        """Forward WebRTC signalling packets to the other peer."""
        await self.channel_layer.group_send(
            self.group_name,
            {
                "type": "webrtc_signal",
                "payload": data,
                "sender_channel": self.channel_name,
            },
        )

    async def handle_transcript(self, data):
        text = data.get("text", "").strip()
        if not text:
            logger.warning("Empty transcript received from [%s]; ignoring", self.user.username)
            return

        username = self.user.username
        msg_id = data.get("msg_id", "")

        # 1. Instant subtitle broadcast
        await self.channel_layer.group_send(
            self.group_name,
            {
                "type": "subtitle_broadcast",
                "username": username,
                "text": text,
            },
        )

        # 2 & 3. Grammar check (non-blocking)
        asyncio.create_task(self._grammar_check_and_broadcast(text, username, msg_id))

    async def _grammar_check_and_broadcast(self, text: str, username: str, msg_id: str = ""):
        logger.warning("[grammar-debug] Grammar check for [%s]: %s", username, text[:80])
        try:
            corrected, explanation, has_errors = await run_grammar_check(text)
            logger.warning("[grammar-debug] Gemini result - errors: %s | corrected: %s", has_errors, corrected[:80])
        except Exception as e:
            logger.error("Gemini error for '%s': %s - %s", text[:50], type(e).__name__, str(e))
            await self.channel_layer.group_send(
                self.group_name,
                {"type": "grammar_correction_error", "msg_id": msg_id},
            )
            return

        await save_transcript(
            room_id=self.room_id,
            user=self.user,
            original=text,
            corrected=corrected,
            has_errors=has_errors,
            explanation=explanation,
        )

        await self.channel_layer.group_send(
            self.group_name,
            {
                "type": "grammar_correction",
                "username": username,
                "original": text,
                "corrected": corrected,
                "explanation": explanation,
                "has_errors": has_errors,
                "msg_id": msg_id,
            },
        )
        logger.warning("[grammar-debug] Correction broadcast to frontend msg_id=%s", msg_id)

    # ------------------------------------------------------------------ #
    #  Send to browser (group_send handlers)                               #
    # ------------------------------------------------------------------ #

    async def peer_ready_broadcast(self, event):
        # Don't echo back to the sender
        if event["sender_channel"] != self.channel_name:
            await self.send(text_data=json.dumps({
                "type": "peer_ready",
                "peer_id": event["peer_id"],
                "role": event["role"],
            }))

    async def peer_joined(self, event):
        await self.send(text_data=json.dumps({"type": "peer_joined", "username": event["username"]}))

    async def peer_left(self, event):
        await self.send(text_data=json.dumps({"type": "peer_left", "username": event["username"]}))

    async def webrtc_signal(self, event):
        # Don't echo back to sender
        if event["sender_channel"] != self.channel_name:
            await self.send(text_data=json.dumps(event["payload"]))

    async def subtitle_broadcast(self, event):
        await self.send(
            text_data=json.dumps(
                {
                    "type": "subtitle",
                    "username": event["username"],
                    "text": event["text"],
                }
            )
        )

    async def grammar_correction(self, event):
        logger.warning("[grammar-debug] Sending correction websocket message msg_id=%s", event.get("msg_id", ""))
        await self.send(
            text_data=json.dumps(
                {
                    "type": "correction",
                    "username": event["username"],
                    "original": event["original"],
                    "corrected": event["corrected"],
                    "explanation": event["explanation"],
                    "has_errors": event.get("has_errors", False),
                    "msg_id": event.get("msg_id", ""),
                }
            )
        )

    async def grammar_correction_error(self, event):
        await self.send(
            text_data=json.dumps(
                {
                    "type": "correction_error",
                    "msg_id": event.get("msg_id", ""),
                    "message": "Grammar correction request failed. Check server logs.",
                }
            )
        )


# ------------------------------------------------------------------ #
#  Async helpers                                                        #
# ------------------------------------------------------------------ #


async def run_grammar_check(text: str):
    """
    Call Gemini via direct REST API (no SDK version issues).
    Returns (corrected_text, explanation, has_errors).
    """
    import urllib.request
    import urllib.error

    prompt = f"""Correct the grammar of this spoken English sentence.

Sentence:
"{text}"

Rules:
- Do not explain anything.
- Do not discuss fragments or incomplete thoughts.
- If the spoken text is grammatically acceptable, set has_errors to false.
- If correction is needed, return only the corrected sentence.
- Keep the correction short and natural.

Respond ONLY with valid JSON:
{{
  "has_errors": true or false,
  "corrected": "corrected sentence or original sentence",
  "explanation": ""
}}"""

    if not settings.GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY is empty")

    model = settings.GEMINI_MODEL
    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"{model}:generateContent"
    )
    payload = json.dumps({
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"responseMimeType": "application/json"},
    }).encode("utf-8")

    def _call():
        logger.warning("[grammar-debug] Calling Gemini model=%s for transcript length=%s", model, len(text))
        req = urllib.request.Request(
            url,
            data=payload,
            headers={
                "Content-Type": "application/json",
                "x-goog-api-key": settings.GEMINI_API_KEY,
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode("utf-8"))

    loop = asyncio.get_running_loop()
    try:
        data = await loop.run_in_executor(None, _call)
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8")
        raise RuntimeError(f"Gemini HTTP {e.code}: {body}")

    raw = data["candidates"][0]["content"]["parts"][0]["text"].strip()
    logger.warning("[grammar-debug] Gemini response received for model=%s", model)

    # Strip markdown fences if present
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]

    result = json.loads(raw.strip())
    return result["corrected"], result["explanation"], result["has_errors"]


@database_sync_to_async
def save_transcript(room_id, user, original, corrected, has_errors, explanation):
    from apps.rooms.models import Room, Transcript

    try:
        room = Room.objects.get(id=room_id)
        Transcript.objects.create(
            room=room,
            speaker=user,
            original_text=original,
            corrected_text=corrected,
            has_errors=has_errors,
            correction_explanation=explanation,
        )
    except Exception as e:
        logger.error("DB save error: %s", e)
