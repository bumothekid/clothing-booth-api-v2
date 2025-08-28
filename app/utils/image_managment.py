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
        if not isinstance(file, FileStorage) or not file.filename.endswith((".png", ".jpg", ".jpeg")):
            raise UnsupportedFileTypeError("The file provided is not a supported image type. Supported types are PNG, JPG, and JPEG.")
        
        if len(file.read()) > 4*1024*1024:
            raise FileTooLargeError("File is too large (max 4MB)")
        
        file.seek(0)
        fileName = str(uuid.uuid4())
        
        try:
            
            image = Image.open(file)
            image = image.convert("RGBA")
            
            pngImage = BytesIO()
            image.save(pngImage, format="PNG")
            pngImage.seek(0)
            
            try:
                without_background = bg.remove(pngImage.read(), model_name="u2net_cloth_segm",
                                        alpha_matting=True,
                                        alpha_matting_foreground_threshold=200, # 240
                                        alpha_matting_background_threshold=10, #30 # 10
                                        alpha_matting_erode_structure_size=13, #5 # 10
                                        alpha_matting_base_size=512, # 1000
                                        )
            except ValueError as e:
                raise ImageUnclearError("The provided image does not contain a foreground.")
            except Exception as e:
                logger.error(f"An unexpected error occured while removing the background of an image: {e}")
                logger.error(traceback.format_exc())
                raise e

            new_image = Image.open(BytesIO(without_background))
            
            alpha = new_image.getchannel("A")
            bbox = alpha.getbbox()
            
            cropped_image = new_image.crop(bbox)
            cropped_image.save("app/static/temp/" + fileName + ".webp", format="WEBP")
            
            return f"https://api.clothing-booth.com/uploads/temp/{fileName}.webp", fileName
        except Exception as e:
            logger.error(f"An unexpected error occured while removing the background of an image: {e}")
            logger.error(traceback.format_exc())
            raise e

    def move_preview_image_to_permanent(self, filename: Optional[str], is_clothing: bool = True) -> str:
        if not filename:
            raise ValueError("Filename cannot be empty.")
        
        if not filename.endswith(".webp"):
            filename = filename + ".webp"
        
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
    
    def generate_outfit_collage(self, item_images: list[str]) -> tuple:
        size = (500, 500)
        collage = Image.new("RGBA", size, (255, 255, 255, 0))

        num_items = len(item_images[:4])
        
        if num_items == 2:
            cell_size = (size[0] // 2, size[1] // 2)
            grid = [(cell_size[0] // 2, 0), (cell_size[0] // 2, cell_size[1] - 30)]
        elif num_items == 3:
            cell_size = (size[0] // 2, size[1] // 2)
            grid = [(0, 0), (cell_size[0], 0), (size[0]//4, cell_size[1])]
        else:
            cell_size = (size[0] // 2, size[1] // 2)
            grid = [(0, 0), (cell_size[0], 0), (0, cell_size[1]), (cell_size[0], cell_size[1])]

        for idx, img_id in enumerate(item_images[:4]):
            img = Image.open("app/static/clothing_images/" + img_id + ".webp").convert("RGBA")
            img.thumbnail(cell_size, Image.ANTIALIAS)

            offset_x = (cell_size[0] - img.width) // 2
            offset_y = (cell_size[1] - img.height) // 2

            paste_x = grid[idx][0] + offset_x
            paste_y = grid[idx][1] + offset_y

            collage.paste(img, (paste_x, paste_y), img)

            
        filename = str(uuid.uuid4())
            
        alpha = collage.getchannel("A")
        bbox = alpha.getbbox()
            
        cropped_image = collage.crop(bbox)
        cropped_image.save("app/static/outfit_collages/" + filename + ".webp", "WEBP")
        
        return f"https://api.clothing-booth.com/uploads/outfit_collages/{filename}.webp", filename
    
image_manager = ImageManager()