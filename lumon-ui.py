import argparse
from PIL import Image, ImageDraw, ImageFont
import os
import numpy as np
import time
import sys
import threading
import random
import pygame
import signal
from whisplay import WhisplayBoard
from utils import ColorUtils, ImageUtils, TextUtils

class NumberMatrixItem:
    def __init__(self, size, font_path, row_index=0, column_index=0):
        self.item_width = 40
        self.item_height = 40
        # Random number from 0-9
        self.number = random.randint(0, 9)
        self.font_path = font_path
        self.font = ImageFont.truetype(self.font_path, 20)
        self.shaking_offset = (0, 0)
        self.is_shaking = True
        self.scale = 0.7  # Initial scale is 1.0
        self.row_index = row_index
        self.column_index = column_index
        self.is_collecting = False
        self.collect_frame_count = 0
        
    def get_collecting_frame_count(self):
        return self.collect_frame_count
        
    def update_scale(self, target_scale, step=0.05):
        if self.scale < target_scale:
            self.scale = min(self.scale + step, target_scale)
        elif self.scale > target_scale:
            self.scale = max(self.scale - step, target_scale)
        
    def tick(self, global_collect=False):
        global is_focused, focus_location, collect_frame_limit
        if self.is_collecting and self.collect_frame_count < collect_frame_limit:
            self.collect_frame_count += 1
            return
        if self.is_collecting:
            self.scale = 0.2
            self.number = random.randint(0, 9)
            self.collect_frame_count = 0
            self.is_collecting = False
        
        # Calculate the linear distance from the focus position
        distance_x = abs(self.row_index - focus_location[0])
        distance_y = abs(self.column_index - focus_location[1])
        distance = (distance_x ** 2 + distance_y ** 2) ** 0.5
    
        if distance <= 1.9:
            self.is_shaking = True
            self.update_scale(1.5, step=0.08)  # Zoom in to 1.5 at the focus position
            if global_collect:
                print(f"[Collect] Collecting number {self.number} at ({self.row_index}, {self.column_index})")
                self.is_collecting = True
                self.shaking_offset = (0, 0)
                self.is_shaking = False
                return
        elif distance <= 2.5:
            self.is_shaking = True
            self.update_scale(0.9, step=0.05)  # Zoom in to 0.9 for distances between 2 and 2.5
        else:
            self.is_shaking = False
            self.update_scale(0.7, step=0.05)  # Zoom in to 0.7 for distances of 5 and above
        
        # Update number and shaking status at each tick
        if self.is_shaking:
            self.shaking_offset = (random.randint(-1, 1), random.randint(-1, 1))
        else:
            self.shaking_offset = (0, 0)
            
    def render_font_image(self):
        global number_image_cache
        if self.number in number_image_cache:
            return number_image_cache[self.number]
        
        text_bbox = self.font.getbbox(str(self.number))
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]
        font_image = Image.new("RGBA", (text_width, text_height + 20), (0, 0, 0, 0))
        draw = ImageDraw.Draw(font_image)
        draw.text((0, 0), str(self.number), font=self.font, fill=(170, 250, 255, 255))
        # Cache the font image, key is the number
        number_image_cache[self.number] = font_image
        return font_image

    def get_item_image(self):
        global item_image_cache
        cache_key = (self.number, int(self.scale * 100))
        if cache_key in item_image_cache:
            return item_image_cache[cache_key]

        img = Image.new("RGBA", (self.item_width, self.item_height), (0, 0, 0, 0))
        font_image = self.render_font_image()
        scaled_width = int(font_image.width * self.scale)
        scaled_height = int(font_image.height * self.scale)

        if scaled_width == 0 or scaled_height == 0:
            return img

        scaled_font_image = font_image.resize((scaled_width, scaled_height), Image.BILINEAR)
        img.paste(scaled_font_image, ((self.item_width - scaled_width) // 2, (self.item_height - scaled_height) // 2), scaled_font_image)
        
        item_image_cache[cache_key] = img
        return img

class RenderThread(threading.Thread):
    def __init__(self, whisplay, font_path, fps=30):
        super().__init__()
        self.whisplay = whisplay
        self.width = whisplay.LCD_HEIGHT
        self.height = whisplay.LCD_WIDTH
        self.font_path = font_path
        self.fps = fps
        
        self.play_start_sound()
        time.sleep(1.5)
        
        self.render_init_screen()
        self.background_image = self.get_background_image()
        self.whisplay.set_rgb(170, 250, 255)
        
        # Clear the logo and start the loop with running = True
        self.whisplay.set_rgb_fade(0, 0, 0, duration_ms=1000)
        self.running = True
        self.main_text_font = ImageFont.truetype(self.font_path, 20)
        self.main_text_line_height = self.main_text_font.getmetrics()[0] + self.main_text_font.getmetrics()[1]
        self.text_cache_image = None
        self.current_render_text = ""
        self.frame_count = 0
        self.collecting = False
        self.collect_destination = (50, 380)  # Default collection position
        self.idle_countdown = 100
        self.show_time = True
        
        # Optimization: Pre-create canvases
        self.canvas = Image.new("RGBA", (self.width * 2, self.height * 2), (0, 0, 0, 0))
        self.final_image = Image.new("RGBA", (self.whisplay.LCD_WIDTH, self.whisplay.LCD_HEIGHT), (0, 0, 0, 255))
        
        # Optimization: Cache for clock
        self.last_time_str = ""
        self.clock_image = None
        self.clock_font = ImageFont.truetype(self.font_path, 60)
        self.title_font = ImageFont.truetype(self.font_path, 32)

    def set_collecting(self, collecting):
        self.idle_countdown = 100
        self.show_time = False
        self.collecting = collecting
        print(f"[Collect] Set collecting to {collecting}")
        if collecting:
            collect_x = random.choice([50, 150, 260, 370, 480])
            self.collect_destination = (collect_x, 380)
            
    def play_start_sound(self):
        start_sound_path = os.path.join("sound", "computer_start.mp3")
        if os.path.exists(start_sound_path):
            pygame.mixer.Sound(start_sound_path).play()

    def render_init_screen(self):
        # Display logo on startup with animation
        logo_path = os.path.join("img", "lumon_logo.jpg")
        if os.path.exists(logo_path):
            logo_image = Image.open(logo_path).convert("RGBA")
            logo_image = logo_image.resize((whisplay.LCD_WIDTH, whisplay.LCD_HEIGHT), Image.BILINEAR)

            animation_duration = 2  # seconds
            num_frames = int(animation_duration * self.fps)
            start_y = whisplay.LCD_HEIGHT
            end_y = 0
            
            background = Image.new("RGBA", (whisplay.LCD_WIDTH, whisplay.LCD_HEIGHT), (0, 0, 0, 255))
            
            whisplay.set_backlight(100)

            for i in range(num_frames + 1):
                progress = i / num_frames
                # Ease-out effect
                progress = 1 - (1 - progress) ** 3
                
                current_y = int(start_y + (end_y - start_y) * progress)
                
                frame = background.copy()
                frame.paste(logo_image, (0, current_y), logo_image)
                
                rgb565_data = ImageUtils.image_to_rgb565(frame, whisplay.LCD_WIDTH, whisplay.LCD_HEIGHT)
                whisplay.draw_image(0, 0, whisplay.LCD_WIDTH, whisplay.LCD_HEIGHT, rgb565_data)
                time.sleep(1 / self.fps)
            
    def get_background_image(self):
        bg_path = os.path.join("img", "mdr_bg.jpg")
        if os.path.exists(bg_path):
            bg_image = Image.open(bg_path).convert("RGBA")
            bg_image = bg_image.resize((self.whisplay.LCD_HEIGHT, self.whisplay.LCD_WIDTH), Image.BILINEAR)
            bg_image = bg_image.rotate(-90, expand=True)
            return bg_image
        return None

    def render_frame(self):
        # Optimization: clear canvas instead of creating a new one
        self.canvas.paste((0, 0, 0, 0), (0, 0, self.canvas.width, self.canvas.height))
        draw = ImageDraw.Draw(self.canvas)

        temp_collecting = self.collecting
        if self.collecting:
            self.collecting = False
        self.render_number_matrix(self.canvas, (24, 106), 12, 6, 40, 40, 4, (170, 250, 255, 255), temp_collecting)
        
        if self.show_time:
            current_time_str = time.strftime("%H:%M:%S")
            if current_time_str != self.last_time_str:
                self.last_time_str = current_time_str
                
                clock_area_width = 370
                clock_area_height = 150
                self.clock_image = Image.new("RGBA", (clock_area_width, clock_area_height), (0,0,0,0))
                clock_draw = ImageDraw.Draw(self.clock_image)
                
                # Draw a black pop-up box with a blue stroke
                clock_draw.rectangle((0, 0, clock_area_width-1, clock_area_height-1), fill=(0, 0, 0, 200), outline=(170, 250, 255, 255), width=2)
                clock_draw.text((40, 10), "History lives in us.", font=self.title_font, fill=(170, 250, 255, 255))
                clock_draw.text((60, 50), current_time_str, font=self.clock_font, fill=(170, 250, 255, 255))

            if self.clock_image:
                self.canvas.paste(self.clock_image, (100, 170), self.clock_image)

        rotated = self.canvas.rotate(-90, expand=True)
        resized = rotated.resize((self.whisplay.LCD_WIDTH, self.whisplay.LCD_HEIGHT), Image.BILINEAR)
        
        # Optimization: reuse final_image
        self.final_image.paste(self.background_image, (0, 0), self.background_image)
        self.final_image.paste(resized, (0, 0), resized)
        
        self.whisplay.draw_image(0, 0, self.whisplay.LCD_WIDTH, self.whisplay.LCD_HEIGHT, ImageUtils.image_to_rgb565(self.final_image, self.whisplay.LCD_WIDTH, self.whisplay.LCD_HEIGHT))

    def render_number_matrix(self, image, position, column_count, line_count, item_width, item_height, spacing, font_color, global_collect=False):
        global collect_frame_limit
        if global_collect:
            print(f"[Render] Rendering number matrix with collect={global_collect}")
        # Plan the width, height, and spacing of the item, the text needs to be rendered in the center of the item
        x, y = position
        for line in range(line_count):
            for column in range(column_count):
                item = matrix_items[line][column]
                item.tick(global_collect)
                item_image = item.get_item_image()
                item_x = x + column * (item_width + spacing) + item.shaking_offset[0]
                item_y = y + line * (item_height + spacing) + item.shaking_offset[1]
                
                if item.get_collecting_frame_count() > 0:
                    dest_x, dest_y = self.collect_destination
                    progress = item.get_collecting_frame_count() / collect_frame_limit
                    item_x = int(item_x + (dest_x - item_x) * progress)
                    item_y = int(item_y + (dest_y - item_y) * progress)
                image.paste(item_image, (item_x, item_y), item_image)
        

    def run(self):
        global is_focused, focus_location
        frame_interval = 1 / self.fps
        while self.running:
            self.render_frame()
            self.frame_count += 1
            if self.idle_countdown > 0:
                self.idle_countdown -= 1
            else:
                self.show_time = True
            if self.frame_count % (2 * self.fps) == 0:  # Randomize the focus position once
                random_focus_location()
            time.sleep(frame_interval)
            
    def stop(self):
        self.running = False
        
pygame.mixer.init()
number_image_cache = {}
item_image_cache = {}
    
# create a 12 x 6 matrix of NumberMatrixItem
matrix_items = []
for i in range(6):
    row = []
    for j in range(12):
        item = NumberMatrixItem((20, 20), "NotoSansSC-Bold.ttf", row_index=j, column_index=i)
        row.append(item)
    matrix_items.append(row)
    
is_focused = True
focus_location = (random.randint(0, 11), random.randint(0, 5))  # Initial focus position
# 50 150 260 370 480
collect_frame_limit = 10

click_sound_effect = pygame.mixer.Sound(os.path.join("sound", "click_sound.mp3"))
click_sound_effect.set_volume(0.1)

# Button hold to restart render process
restart_hold_seconds = 5

def play_click_sound():
    if not pygame.mixer.music.get_busy():
        click_sound_effect.play()

# generate a random is_focused and location
def random_focus_location():
    global focus_location, is_focused
    seed = random.randint(0, 10)
    if seed > 3:
        is_focused = random.choice([True, False])
    else:
        is_focused = True
    focus_location = (random.randint(0, 11), random.randint(0, 5))
    print(f"[Focus] is_focused: {is_focused}, location: {focus_location}")
    
if __name__ == "__main__":
    whisplay = WhisplayBoard()
    
    print(f"[LCD] initial finish: {whisplay.LCD_WIDTH}x{whisplay.LCD_HEIGHT}")
    
    render_thread = RenderThread(whisplay, "NotoSansSC-Bold.ttf", fps=30)
    render_thread.start()

    button_press_time = 0

    def restart_render_process():
        global render_thread
        print("Restarting render process...")
        
        if render_thread and render_thread.is_alive():
            render_thread.stop()
            render_thread.join()
            
        render_thread = RenderThread(whisplay, "NotoSansSC-Bold.ttf", fps=30)
        render_thread.start()

    def hold_check():
        global button_press_time
        # This function will run in a separate thread
        # It checks if the button is still pressed after 8 seconds
        press_time = button_press_time
        while time.time() - press_time < restart_hold_seconds:
            print("Button is held for ", int(time.time() - press_time), "seconds")
            # button press status
            print("Button pressed status:", whisplay.button_pressed())
            # If button is released, whisplay.button_pressed() will be False
            # TODO button_pressed reverse logic
            if whisplay.button_pressed():
                return # Exit if button is released early
            time.sleep(0.1)
        
        print("Button held for 8 seconds, restarting render process...")
        # If we reach here, the button was held for 8 seconds
        restart_render_process()

    def button_press_handler():
        print("Button pressed...")
        global button_press_time
        button_press_time = time.time()
        
        # button press status
        print("Button pressed status:", whisplay.button_pressed())
        
        # Start a thread to check for long press
        hold_thread = threading.Thread(target=hold_check)
        hold_thread.start()

    def button_release_handler():
        global button_press_time
        # button press status
        print("Button pressed status:", whisplay.button_pressed())
        if time.time() - button_press_time < restart_hold_seconds:
            render_thread.set_collecting(True)
            play_click_sound()
    
    whisplay.on_button_press(button_press_handler)
    whisplay.on_button_release(button_release_handler)

    def cleanup_and_exit(signum, frame):
        print("\nShutting down...")
        if render_thread and render_thread.is_alive():
            render_thread.stop()
            render_thread.join()
        whisplay.cleanup()
        sys.exit(0)

    signal.signal(signal.SIGTERM, cleanup_and_exit)
    
    try:
        # Keep the main thread alive
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        cleanup_and_exit(None, None)



