import uuid
from django.db import models
from django.contrib.auth.models import User


class Room(models.Model):
    """A virtual classroom session between two users."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, blank=True)
    host = models.ForeignKey(User, on_delete=models.CASCADE, related_name="hosted_rooms")
    guest = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name="joined_rooms"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"Room {self.id} — host: {self.host.username}"

    @property
    def room_code(self):
        """Short shareable code (first 8 chars of UUID)."""
        return str(self.id)[:8].upper()


class Transcript(models.Model):
    """One line of speech captured during a session."""

    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name="transcripts")
    speaker = models.ForeignKey(User, on_delete=models.CASCADE)
    original_text = models.TextField()
    corrected_text = models.TextField(blank=True)
    has_errors = models.BooleanField(default=False)
    correction_explanation = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["timestamp"]

    def __str__(self):
        return f"[{self.speaker.username}] {self.original_text[:60]}"
