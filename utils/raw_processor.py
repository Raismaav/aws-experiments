import rawpy
import imageio
from PIL import Image
import os
import logging
from typing import Tuple, Optional
import tempfile

logger = logging.getLogger(__name__)

class RawImageProcessor:
    """Process RAW image files and convert them to web-friendly formats"""
    
    # Supported RAW formats
    RAW_EXTENSIONS = {
        '.cr2', '.cr3',  # Canon
        '.nef', '.nrw',  # Nikon
        '.arw', '.sr2',  # Sony
        '.raf',          # Fujifilm
        '.rw2',          # Panasonic
        '.orf',          # Olympus
        '.pef',          # Pentax
        '.dng',          # Adobe
        '.raw',          # Generic
        '.rwz',          # Hasselblad
        '.3fr',          # Hasselblad
        '.fff',          # Hasselblad
        '.hdr',          # Hasselblad
        '.srw',          # Samsung
        '.mrw',          # Minolta
        '.mef',          # Mamiya
        '.mos',          # Leaf
        '.bay',          # Casio
        '.dcr',          # Kodak
        '.kdc',          # Kodak
        '.erf',          # Epson
        '.mdc',          # Minolta
        '.x3f',          # Sigma
        '.r3d',          # Red Digital Cinema
        '.cine',         # Phantom
        '.dpx',          # Digital Picture Exchange
        '.exr',          # OpenEXR
        '.hdr',          # Radiance HDR
        '.tga',          # Targa
        '.tif', '.tiff'  # TIFF
    }
    
    def __init__(self):
        """Initialize the RAW processor"""
        self.max_raw_size = 500 * 1024 * 1024  # 500MB limit for RAW files
        self.quality = 85  # JPEG quality for conversion
    
    def is_raw_format(self, filename: str) -> bool:
        """Check if file is a RAW format"""
        ext = os.path.splitext(filename.lower())[1]
        return ext in self.RAW_EXTENSIONS
    
    def get_file_info(self, raw: rawpy.RawPy) -> dict:
        """Get detailed information about a RAW file using the correct API"""
        try:
            info = {
                'width': raw.sizes.width,
                'height': raw.sizes.height,
                'colors': raw.num_colors,
                'raw_type': str(raw.raw_type),
                'color_desc': raw.color_desc,
                'black_level': raw.black_level_per_channel[0] if raw.black_level_per_channel else 0,
                'white_level': raw.white_level,
                'camera_whitebalance': raw.camera_whitebalance.tolist() if hasattr(raw.camera_whitebalance, 'tolist') else [],
                'daylight_whitebalance': raw.daylight_whitebalance.tolist() if hasattr(raw.daylight_whitebalance, 'tolist') else []
            }
            return info
        except Exception as e:
            logger.error(f"Error reading RAW file info: {e}")
            return {}
    
    def process_raw_to_jpeg(self, file_path: str, max_width: int = 2048, max_height: int = 2048) -> Tuple[bytes, str]:
        """
        Convert RAW file to JPEG with specified dimensions using correct API
        
        Args:
            file_path: Path to RAW file
            max_width: Maximum width for output
            max_height: Maximum height for output
            
        Returns:
            Tuple of (jpeg_bytes, content_type)
        """
        try:
            with rawpy.imread(file_path) as raw:
                # Process RAW with correct API - no parameters for postprocess
                rgb = raw.postprocess()
                
                # Convert to PIL Image for resizing
                pil_image = Image.fromarray(rgb)
                
                # Calculate new dimensions maintaining aspect ratio
                width, height = pil_image.size
                if width > max_width or height > max_height:
                    ratio = min(max_width / width, max_height / height)
                    new_width = int(width * ratio)
                    new_height = int(height * ratio)
                    pil_image = pil_image.resize((new_width, new_height), Image.Resampling.LANCZOS)
                
                # Convert to JPEG
                with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as temp_file:
                    pil_image.save(temp_file.name, 'JPEG', quality=self.quality, optimize=True)
                    temp_file_path = temp_file.name
                
                # Read the converted file
                with open(temp_file_path, 'rb') as f:
                    jpeg_bytes = f.read()
                
                # Clean up temporary file
                os.unlink(temp_file_path)
                
                logger.info(f"RAW file converted to JPEG: {width}x{height} -> {pil_image.size}")
                return jpeg_bytes, 'image/jpeg'
                
        except Exception as e:
            logger.error(f"Error processing RAW file: {e}")
            raise Exception(f"Failed to process RAW file: {str(e)}")
    
    def create_thumbnail(self, file_path: str, size: Tuple[int, int] = (300, 300)) -> bytes:
        """Create a thumbnail from RAW file using correct API"""
        try:
            with rawpy.imread(file_path) as raw:
                # Process RAW with minimal settings for thumbnail
                rgb = raw.postprocess()
                
                # Convert to PIL and resize
                pil_image = Image.fromarray(rgb)
                pil_image.thumbnail(size, Image.Resampling.LANCZOS)
                
                # Convert to JPEG
                with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as temp_file:
                    pil_image.save(temp_file.name, 'JPEG', quality=70, optimize=True)
                    temp_file_path = temp_file.name
                
                # Read thumbnail
                with open(temp_file_path, 'rb') as f:
                    thumbnail_bytes = f.read()
                
                # Clean up
                os.unlink(temp_file_path)
                
                return thumbnail_bytes
                
        except Exception as e:
            logger.error(f"Error creating thumbnail: {e}")
            raise Exception(f"Failed to create thumbnail: {str(e)}")
    
    def validate_raw_file(self, file_path: str) -> bool:
        """Validate that RAW file can be processed"""
        try:
            # Check file size
            file_size = os.path.getsize(file_path)
            if file_size > self.max_raw_size:
                logger.warning(f"RAW file too large: {file_size / (1024*1024):.1f}MB")
                return False
            
            # Try to open with rawpy
            with rawpy.imread(file_path) as raw:
                # Basic validation passed
                return True
                
        except Exception as e:
            logger.error(f"RAW file validation failed: {e}")
            return False
