"""
Data migration: convert plain URL strings in `images` column to valid JSON arrays
before changing the field type to JSONField.
"""
import json
from django.db import migrations


def convert_images_to_json(apps, schema_editor):
    """Convert plain URL strings to JSON arrays."""
    Room = apps.get_model('rooms', 'Room')
    db_alias = schema_editor.connection.alias

    for room in Room.objects.using(db_alias).all():
        raw = room.images
        # If it's already a list/dict, it's valid JSON — skip
        if isinstance(raw, (list, dict)):
            continue
        # If it's a string, wrap it in a JSON array
        if isinstance(raw, str):
            raw = raw.strip()
            if not raw:
                room.images = '[]'
            elif raw.startswith('[') or raw.startswith('{'):
                # Already looks like JSON, leave it
                continue
            else:
                # Plain URL string — wrap in a JSON array
                room.images = json.dumps([raw])
            room.save(update_fields=['images'])


def reverse_noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('rooms', '0005_alter_room_images'),
    ]

    operations = [
        migrations.RunPython(convert_images_to_json, reverse_noop),
    ]
