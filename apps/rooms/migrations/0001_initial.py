from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("auth", "0012_alter_user_first_name_max_length"),
    ]

    operations = [
        migrations.CreateModel(
            name="Room",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("name", models.CharField(blank=True, max_length=100)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("is_active", models.BooleanField(default=True)),
                ("host", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="hosted_rooms", to="auth.user")),
                ("guest", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="joined_rooms", to="auth.user")),
            ],
        ),
        migrations.CreateModel(
            name="Transcript",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("original_text", models.TextField()),
                ("corrected_text", models.TextField(blank=True)),
                ("has_errors", models.BooleanField(default=False)),
                ("correction_explanation", models.TextField(blank=True)),
                ("timestamp", models.DateTimeField(auto_now_add=True)),
                ("room", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="transcripts", to="rooms.room")),
                ("speaker", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="auth.user")),
            ],
            options={"ordering": ["timestamp"]},
        ),
    ]
