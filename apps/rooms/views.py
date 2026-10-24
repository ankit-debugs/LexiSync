import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.conf import settings
from .models import Room


@login_required
def lobby(request):
    """Landing page — shows active rooms you host or joined."""
    hosted = Room.objects.filter(host=request.user, is_active=True).order_by("-created_at")
    joined = Room.objects.filter(guest=request.user, is_active=True).order_by("-created_at")
    return render(request, "rooms/lobby.html", {"hosted_rooms": hosted, "joined_rooms": joined})


@login_required
@require_POST
def create_room(request):
    """Create a new room and redirect the host into it."""
    name = request.POST.get("name", "").strip() or f"{request.user.username}'s Room"
    room = Room.objects.create(host=request.user, name=name)
    return redirect("rooms:room_detail", room_id=room.id)


@login_required
def join_room(request):
    """Join a room by entering its 8-char code."""
    if request.method == "POST":
        code = request.POST.get("code", "").strip().upper()
        # Find rooms whose UUID starts with that code
        rooms = Room.objects.filter(is_active=True)
        matched = None
        for room in rooms:
            if room.room_code == code:
                matched = room
                break

        if not matched:
            return render(request, "rooms/join.html", {"error": "Room not found. Check the code and try again."})

        if matched.host == request.user:
            # Host rejoining their own room
            return redirect("rooms:room_detail", room_id=matched.id)

        if matched.guest and matched.guest != request.user:
            return render(request, "rooms/join.html", {"error": "This room is already full."})

        matched.guest = request.user
        matched.save()
        return redirect("rooms:room_detail", room_id=matched.id)

    return render(request, "rooms/join.html")


@login_required
def room_detail(request, room_id):
    """The actual video call room."""
    room = get_object_or_404(Room, id=room_id, is_active=True)

    # Only host and guest may enter
    if request.user != room.host and request.user != room.guest:
        # Treat as a new guest joining
        if room.guest is None:
            room.guest = request.user
            room.save()
        else:
            return redirect("rooms:lobby")

    is_host = request.user == room.host
    transcripts = room.transcripts.select_related("speaker").order_by("timestamp")

    return render(
        request,
        "rooms/room.html",
        {
            "room": room,
            "is_host": is_host,
            "transcripts": transcripts,
            "deepgram_api_key": settings.DEEPGRAM_API_KEY,
        },
    )


@login_required
def end_room(request, room_id):
    """Host ends the session — works via POST or GET for robustness."""
    room = get_object_or_404(Room, id=room_id, host=request.user)
    room.is_active = False
    room.save()

    total = room.transcripts.count()
    errors = room.transcripts.filter(has_errors=True).count()
    messages.success(
        request,
        f"Session ended. {total} sentences captured, {errors} grammar corrections made."
    )
    return redirect("rooms:lobby")


@login_required
def test_gemini(request):
    """Quick Gemini API test — visit /test-gemini/ to diagnose."""
    import urllib.request, urllib.error
    from django.http import HttpResponse

    key = settings.GEMINI_API_KEY
    if not key:
        return HttpResponse("❌ GEMINI_API_KEY is empty in .env", content_type="text/plain")

    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"{settings.GEMINI_MODEL}:generateContent"
    )
    payload = json.dumps({
        "contents": [{"parts": [{"text": "Say hello in one word."}]}]
    }).encode("utf-8")

    try:
        req = urllib.request.Request(url, data=payload,
                                     headers={"Content-Type": "application/json", "x-goog-api-key": key},
                                     method="POST")
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())
            text = data["candidates"][0]["content"]["parts"][0]["text"]
            return HttpResponse(f"✅ Gemini works! Response: {text}", content_type="text/plain")
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        return HttpResponse(f"❌ HTTP {e.code}: {body}", content_type="text/plain")
    except Exception as e:
        return HttpResponse(f"❌ Error: {e}", content_type="text/plain")
