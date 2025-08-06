__all__ = ["image_manager"]

import traceback
import uuid
import os
from typing import Optional
from app.utils.exceptions import ImageUnclearError, UnsupportedFileTypeError, FileTooLargeError
from werkzeug.datastructures import FileStorage
from PIL import Image
from io import BytesIO
from backgroundremover import bg
from app.utils.logging import get_logger

logger = get_logger()

class ImageManager:

    def remove_background(self, file: Optional[FileStorage]) -> tuple[str, str]:
        if not isinstance(file, FileStorage):
            raise TypeError("Expected file to be an instance of FileStorage.")
        
        try:
            if not file.filename.endswith((".png", ".jpg", ".jpeg")):
                raise UnsupportedFileTypeError("The file provided is not a supported image type. Supported types are PNG, JPG, and JPEG.")
            
            if len(file.read()) > 4*1024*1024:
                raise FileTooLargeError("File is too large (max 4MB)")
        
            file.seek(0)
            
            fileName = str(uuid.uuid4())
            
            image = Image.open(file)
            image = image.convert("RGBA")
            image.thumbnail((512, 512))
            
            pngImage = BytesIO()
            image.save(pngImage, format="PNG")
            pngImage.seek(0)
            
            try:
                without_background = bg.remove(pngImage.read(), model_name="u2netp",
                                        alpha_matting=True,
                                        alpha_matting_foreground_threshold=240,
                                        alpha_matting_background_threshold=10,
                                        alpha_matting_erode_structure_size=10,
                                        alpha_matting_base_size=1000,
                                        )
            except ValueError as e:
                raise ImageUnclearError("The provided image does not contain a foreground.")
            except Exception as e:
                logger.error(f"An unexpected error occured while removing the background of an image: {e}")
                logger.error(traceback.format_exc())
                raise e

            new_image = Image.open(BytesIO(without_background))
            new_image.save("app/static/temp/" + fileName + ".webp", format="WEBP")
            return f"https://api.clothing-booth.com/uploads/temp/{fileName}.webp", fileName + ".webp"
        except (UnsupportedFileTypeError, FileTooLargeError) as e:
            raise e
        except Exception as e:
            logger.error(f"An unexpected error occured while removing the background of an image: {e}")
            logger.error(traceback.format_exc())
            raise e

    def move_preview_image_to_permanent(self, filename: Optional[str], is_clothing: bool = True) -> str:
        if not filename:
            raise ValueError("Filename cannot be empty.")
        
        try:
            src = f"app/static/temp/{filename}"
            dst = f"app/static/clothing_images/{filename}" if is_clothing else f"app/static/profile_pictures/{filename}"
            if not os.path.exists(src):
                raise FileNotFoundError(f"The temporary image {src} does not exist.")
            os.rename(src, dst)
            return dst
        except FileNotFoundError as e:
            logger.error(f"File not found: {e}")
            raise e
        except Exception as e:
            logger.error(f"An unexpected error occurred while moving the image: {e}")
            raise e
            
    # ! DELETION of old temp images
    
image_manager = ImageManager()