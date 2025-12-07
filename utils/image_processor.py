from PIL import Image
import io
import os
from typing import Tuple

class ImageProcessor:
    """Handle image preprocessing and validation"""

    @staticmethod
    def validate_image(image_path: str) -> Tuple[bool, str]:
        """
        Validate image meets requirements
        Returns: (is_valid, message)
        """
        try:
            img = Image.open(image_path)

            # Check format
            if img.format not in ['JPEG', 'JPG', 'PNG']:
                return False, "Image must be JPEG or PNG format"

            # Check size
            width, height = img.size
            if width < 200 or height < 200:
                return False, "Image resolution too low (minimum 200x200 pixels)"

            # Check file size
            file_size = os.path.getsize(image_path)
            if file_size > 10 * 1024 * 1024:  # 10MB
                return False, "Image file too large (maximum 10MB)"

            return True, "Image valid"

        except Exception as e:
            return False, f"Invalid image file: {str(e)}"

    @staticmethod
    def preprocess_image(image_path: str, max_size: Tuple[int, int] = (1024, 1024)) -> str:
        """
        Preprocess image for optimal analysis
        - Resize if too large
        - Convert to RGB if needed
        Returns: path to preprocessed image
        """
        img = Image.open(image_path)

        # Convert to RGB if necessary
        if img.mode != 'RGB':
            img = img.convert('RGB')

        # Resize if too large
        if img.size[0] > max_size[0] or img.size[1] > max_size[1]:
            img.thumbnail(max_size, Image.Resampling.LANCZOS)

        # Save preprocessed image
        preprocessed_path = image_path.replace('.', '_processed.')
        img.save(preprocessed_path, quality=85, optimize=True)

        return preprocessed_path

    @staticmethod
    def get_image_metadata(image_path: str) -> dict:
        """Extract image metadata"""
        img = Image.open(image_path)
        return {
            "format": img.format,
            "size": img.size,
            "mode": img.mode,
            "file_size": os.path.getsize(image_path)
        }

