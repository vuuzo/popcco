import os
import cloudinary
import cloudinary.uploader

class CloudinaryService:
    def __init__(self):
        cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
        api_key=os.getenv("CLOUDINARY_API_KEY"),
        api_secret=os.getenv("CLOUDINARY_API_SECRET")

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
