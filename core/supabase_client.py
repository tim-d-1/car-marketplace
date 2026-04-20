import os
from supabase import create_client, Client

url: str = os.getenv("SUPABASE_URL")
key: str = os.getenv("SUPABASE_ANON_KEY")

supabase: Client = create_client(url, key)


def upload_image(file, bucket: str, folder: str):
    try:
        ext = file.name.split(".")[-1]
        filename = f"{os.urandom(8).hex()}.{ext}"
        path = f"{folder}/{filename}"

        file_content = file.read()
        supabase.storage.from_(bucket).upload(
            path, file_content, {"content-type": file.content_type}
        )

        public_url = supabase.storage.from_(bucket).get_public_url(path)
        return public_url
    except Exception as e:
        print(f"Supabase upload error: {e}")
        return None
