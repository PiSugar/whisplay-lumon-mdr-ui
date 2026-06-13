import numpy as np
from PIL import Image


class ColorUtils:
    @staticmethod
    def rgb565_to_rgb255(color_565):
        red_5bit = (color_565 >> 11) & 0x1F
        green_6bit = (color_565 >> 5) & 0x3F
        blue_5bit = color_565 & 0x1F
        return (
            (red_5bit * 255) // 31,
            (green_6bit * 255) // 63,
            (blue_5bit * 255) // 31,
        )

    @staticmethod
    def hex_to_rgb255(hex_color):
        hex_color = hex_color.lstrip("#")
        if len(hex_color) not in (6, 8):
            return None
        if not all(char in "0123456789abcdefABCDEF" for char in hex_color):
            return None
        return (
            int(hex_color[0:2], 16),
            int(hex_color[2:4], 16),
            int(hex_color[4:6], 16),
        )

    @staticmethod
    def get_rgb255_from_any(color):
        if isinstance(color, int) and 0 <= color <= 0xFFFF:
            return ColorUtils.rgb565_to_rgb255(color)
        if isinstance(color, str):
            return ColorUtils.hex_to_rgb255(color)
        return None

    @staticmethod
    def calculate_luminance(rgb_tuple):
        if rgb_tuple is None:
            return -1
        r, g, b = rgb_tuple
        return 0.299 * r + 0.587 * g + 0.114 * b


class ImageUtils:
    @staticmethod
    def image_to_rgb565(image: Image.Image, width: int, height: int) -> list:
        image = image.convert("RGB")
        image.thumbnail((width, height), Image.LANCZOS)
        background = Image.new("RGB", (width, height), (0, 0, 0))
        x = (width - image.width) // 2
        y = (height - image.height) // 2
        background.paste(image, (x, y))

        np_img = np.array(background)
        r = (np_img[:, :, 0] >> 3).astype(np.uint16)
        g = (np_img[:, :, 1] >> 2).astype(np.uint16)
        b = (np_img[:, :, 2] >> 3).astype(np.uint16)
        rgb565 = (r << 11) | (g << 5) | b
        high_byte = (rgb565 >> 8).astype(np.uint8)
        low_byte = (rgb565 & 0xFF).astype(np.uint8)
        return np.dstack((high_byte, low_byte)).flatten().tolist()


class TextUtils:
    @staticmethod
    def get_text_size(text, font):
        bbox = font.getbbox(text)
        return bbox[2] - bbox[0], bbox[3] - bbox[1]
