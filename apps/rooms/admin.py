from django.contrib import admin
from django.utils.html import format_html
from .models import Room, Transcript


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ["room_code", "name", "host", "guest", "status_badge", "created_at"]
    list_filter = ["is_active", "created_at"]
    search_fields = ["name", "host__username", "guest__username"]
    readonly_fields = ["id", "room_code", "created_at"]
    ordering = ["-created_at"]
    date_hierarchy = "created_at"

    fieldsets = (
        ("Room Info", {
            "fields": ("id", "name", "is_active")
        }),
        ("Participants", {
            "fields": ("host", "guest")
        }),
        ("Timestamps", {
            "fields": ("created_at",)
        }),
    )

    def status_badge(self, obj):
        if obj.is_active:
            return format_html(
                '<span style="background:#22c55e;color:#fff;padding:2px 10px;border-radius:12px;font-size:11px;font-weight:600;">● LIVE</span>'
            )
        return format_html(
            '<span style="background:#6b7280;color:#fff;padding:2px 10px;border-radius:12px;font-size:11px;font-weight:600;">Ended</span>'
        )
    status_badge.short_description = "Status"


@admin.register(Transcript)
class TranscriptAdmin(admin.ModelAdmin):
    list_display = ["speaker", "room", "short_original", "error_badge", "timestamp"]
    list_filter = ["has_errors", "timestamp", "room"]
    search_fields = ["original_text", "corrected_text", "speaker__username"]
    readonly_fields = ["room", "speaker", "original_text", "corrected_text",
                       "has_errors", "correction_explanation", "timestamp"]
    ordering = ["-timestamp"]
    date_hierarchy = "timestamp"

    fieldsets = (
        ("Spoken", {
            "fields": ("room", "speaker", "timestamp")
        }),
        ("Transcript", {
            "fields": ("original_text", "has_errors", "corrected_text", "correction_explanation")
        }),
    )

    def short_original(self, obj):
        return obj.original_text[:70] + ("…" if len(obj.original_text) > 70 else "")
    short_original.short_description = "Spoken Text"

    def error_badge(self, obj):
        if obj.has_errors:
            return format_html(
                '<span style="background:#ef4444;color:#fff;padding:2px 10px;border-radius:12px;font-size:11px;font-weight:600;">✗ Error</span>'
            )
        return format_html(
            '<span style="background:#22c55e;color:#fff;padding:2px 10px;border-radius:12px;font-size:11px;font-weight:600;">✓ Good</span>'
        )
    error_badge.short_description = "Grammar"