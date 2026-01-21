import cloudinary
import cloudinary.uploader

class CloudinaryService:
    def __init__(self, cloud_name, api_key, api_secret):
        cloudinary.config(
            cloud_name=cloud_name,
            api_key=api_key,
            api_secret=api_secret
        )

    def upload(self, file_storage, user_id: str) -> str | None:
        options = {
            "public_id": user_id,
            "folder": "popcco_avatars",
            "transformation": [
                {'width': 400, 'height': 400, 'crop': 'fill', 'gravity': 'face'}
            ],
            "overwrite": True,
            "invalidate": True
        }
        
        try:
            response = cloudinary.uploader.upload(file_storage, **options)
            return response.get('secure_url')
        except Exception as e:
            print(f"Cloudinary Error: {e}")
            return None

    def delete(self, user_id: str):
        try:
            cloudinary.uploader.destroy(f"popcco_avatars/{user_id}")
        except Exception as e:
            print(f"Cloudinary Delete Error: {e}")
