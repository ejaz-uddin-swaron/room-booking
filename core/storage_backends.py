import os
import uuid
from django.conf import settings
from supabase import create_client, Client


class SupabaseStorage:
    def __init__(self):
        self.supabase_url = getattr(settings, 'SUPABASE_URL', None)
        self.service_role_key = getattr(settings, 'SUPABASE_SERVICE_ROLE_KEY', None)
        self._client = None

    @property
    def client(self) -> Client:
        if self._client is None and self.supabase_url and self.service_role_key:
            self._client = create_client(self.supabase_url, self.service_role_key)
        return self._client

    def upload_image(self, file, bucket_name: str = 'images', folder: str = '') -> str:
        if not self.client:
            raise Exception("Supabase client not configured. Check SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY.")

        file_ext = os.path.splitext(file.name)[1].lower()
        allowed_extensions = {'.jpg', '.jpeg', '.png', '.webp', '.gif'}

        if file_ext not in allowed_extensions:
            raise Exception(f"Unsupported file type: {file_ext}")

        file_content = file.read()
        file_size = len(file_content)
        max_size = getattr(settings, 'MAX_FILE_SIZE', 5 * 1024 * 1024)

        if file_size > max_size:
            raise Exception(f"File too large. Max size: {max_size} bytes")

        file_name = f"{uuid.uuid4().hex}{file_ext}"
        if folder:
            file_path = f"{folder}/{file_name}"
        else:
            file_path = file_name

        response = self.client.storage.from_(bucket_name).upload(
            path=file_path,
            data=file_content,
            file_options={"content-type": self._get_content_type(file_ext)}
        )

        if hasattr(response, 'path'):
            public_url = self.client.storage.from_(bucket_name).get_public_url(response.path)
            return public_url
        elif hasattr(response, 'data') and response.data:
            public_url = self.client.storage.from_(bucket_name).get_public_url(response.data.get('path', file_path))
            return public_url
        else:
            raise Exception(f"Upload failed: {response}")

    def delete_image(self, file_path: str, bucket_name: str = 'images') -> bool:
        if not self.client:
            raise Exception("Supabase client not configured.")

        try:
            self.client.storage.from_(bucket_name).remove([file_path])
            return True
        except Exception as e:
            print(f"Delete failed: {e}")
            return False

    def _get_content_type(self, ext: str) -> str:
        content_types = {
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.webp': 'image/webp',
            '.gif': 'image/gif',
        }
        return content_types.get(ext, 'application/octet-stream')

    def upload_document(self, file, bucket_name: str, folder: str = '') -> str:
        if not self.client:
            raise Exception("Supabase client not configured. Check SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY.")

        file_ext = os.path.splitext(file.name)[1].lower()
        allowed_extensions = {
            '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.csv',
            '.jpg', '.jpeg', '.png', '.webp', '.gif'
        }

        if file_ext not in allowed_extensions:
            raise Exception(f"Unsupported file type: {file_ext}")

        file_content = file.read()
        file_size = len(file_content)
        max_size = getattr(settings, 'MAX_FILE_SIZE', 5 * 1024 * 1024)

        if file_size > max_size:
            raise Exception(f"File too large. Max size: {max_size} bytes")

        file_name = f"{uuid.uuid4().hex}{file_ext}"
        file_path = f"{folder}/{file_name}" if folder else file_name

        response = self.client.storage.from_(bucket_name).upload(
            path=file_path,
            data=file_content,
            file_options={"content-type": self._get_content_type(file_ext)}
        )

        if hasattr(response, 'path'):
            return self.client.storage.from_(bucket_name).get_public_url(response.path)
        if hasattr(response, 'data') and response.data:
            return self.client.storage.from_(bucket_name).get_public_url(response.data.get('path', file_path))
        raise Exception(f"Upload failed: {response}")


supabase_storage = SupabaseStorage()