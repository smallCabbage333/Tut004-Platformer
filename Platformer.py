# Import necessary libraries
import os
import random
import math
import pygame
from os import listdir
from os.path import isfile, join

# Initialize Pygame
pygame.init()

# Set up the game window
pygame.display.set_caption("Platformer")
WIDTH, HEIGHT = 1000, 800
FPS = 60
PLAYER_VEL = 5
window = pygame.display.set_mode((WIDTH, HEIGHT))

# Function to flip sprites for left/ right movement
def flip(sprites):
    # Flip each sprite in the list horizontally
    return [pygame.transform.flip(sprite, True, False) for sprite in sprites]

# Function to load sprites from sprite sheets
def load_sprite_sheets(dir1, dir2, width, height, direction=False):
    # Construct path to the directory containing sprite sheets
    path = join("assets", dir1, dir2)
    # List all files in the directory
    images = [f for f in listdir(path) if isfile(join(path, f))]
    
    all_sprites = {}
    
    # Load each image, split it into sprites, and add to the dictionary
    for image in images:
        sprite_sheet = pygame.image.load(join(path, image)).convert_alpha()
        
        sprites = []
        # Extract individual sprites from the sheet
        for i in range(sprite_sheet.get_width() // width):
            surface = pygame.Surface((width, height), pygame.SRCALPHA, 32)
            rect = pygame.Rect(i * width, 0, width, height)
            surface.blit(sprite_sheet, (0, 0), rect)
            # Scale sprites to double their size            
            sprites.append(pygame.transform.scale2x(surface))
        
        # Store sprites with direction suffixes if needed
        if direction:
            all_sprites[image.replace(".png", "") + "_right"] = sprites
            all_sprites[image.replace(".png", "") + "_left"] = flip(sprites)
        else:
            all_sprites[image.replace(".png", "")] = sprites
            
    return all_sprites
        
# Function to get a single block sprite
def get_block(size):
    # Load a specific block sprite from the terrain sheet
    path = join("assets", "Terrain", "Terrain.png")
    image = pygame.image.load(path).convert_alpha()
    surface = pygame.Surface((size, size), pygame.SRCALPHA, 32)
    rect = pygame.Rect(96, 0, size, size)
    surface.blit(image, (0, 0), rect)
    # Scale block to double its size
    return pygame.transform.scale2x(surface)

# Player class
class Player(pygame.sprite.Sprite):
    COLOR = (255, 0, 0) # Player color (unused)
    GRAVITY = 1 # Gravity effect on the player
    SPRITES = load_sprite_sheets("MainCharacters", "MaskDude", 32, 32, True)
    ANIMATION_DELAY = 3 # Controls speed of animation
    
    def __init__(self, x, y, width, height):
        super().__init__()
        self.rect = pygame.Rect(x, y, width, height)
        self.x_vel = 0 # Horizontal velocity
        self.y_vel = 0 # Vertical velocity
        self.mask = None # For collision detection
        self.direction = "left" # Initial direction
        self.animation_count = 0 # Tracks animation frames
        self.fall_count = 0 # Tracks falling duration
        self.jump_count = 0 # Tracks number of jumps
        self.hit = False # Tracks if player is hit
        self.hit_count = 0 #  Tracks duration of being hit
        
    # Player's jump function
    def jump(self):
        # Apply an initial velocity upwards
        self.y_vel = -self.GRAVITY * 8
        self.animation_count = 0
        self.jump_count += 1
        if self.jump_count == 1:
            self.fall_count = 0       
        
    # Function to move the player
    def move(self, dx, dy):
        self.rect.x += dx
        self.rect.y += dy
        
    # Handle player being hit
    def make_hit(self):
        self.hit = True
        self.hit_count = 0

    # Functions to handle left/ right movement
    def move_left(self, vel):
        # Move player left
        self.x_vel = -vel
        # Update direction and reset animation
        if self.direction != "left":
            self.direction = "left"
            self.animation_count = 0
    
    def move_right(self, vel):
        # Move player right
        self.x_vel = vel
        # Update direction and reset animation
        if self.direction != "right":
            self.direction = "right"
            self.animation_count = 0
    
    # Main loop function for player actions
    def loop(self, fps):
        # Apply gravity over time
        self.y_vel += min(1, (self.fall_count / fps) * self.GRAVITY)
        self.move(self.x_vel, self.y_vel)
        
        # Handle being hit
        if self.hit:
            self.hit_count += 1
        # Reset hit state after 1 second
        if self.hit_count > fps * 1:
            self.hit = False
            self.hit_count = 0

        self.fall_count += 1
        # Update sprite based on current state
        self.update_sprite()
        
    def landed(self):
        # Reset falling and jumping state when landing
        self.fall_count = 0
        self.y_vel = 0
        self.jump_count = 0
        
    def hit_head(self):
        # Invert vertical velocity on hitting an obstacle above
        self.count = 0
        self.y_vel *= -1

    # Update the player's sprite based on current actions
    def update_sprite(self):
        sprite_sheet = "idle"
        if self.hit:
          sprite_sheet = "hit"  
        elif self.y_vel < 0:
            if self.jump_count == 1:
                sprite_sheet = "jump"
            elif self.jump_count == 2:
                sprite_sheet = "double_jump"
        elif self.y_vel > self.GRAVITY * 2:
            sprite_sheet = "fall"
        elif self.x_vel != 0:
            sprite_sheet = "run"

            
        sprite_sheet_name = sprite_sheet + "_" + self.direction
        sprites = self.SPRITES[sprite_sheet_name]
        sprite_index = (self.animation_count // 
                        self.ANIMATION_DELAY) % len(sprites)
        self.sprite = sprites[sprite_index]
        self.animation_count += 1
        # Update rect and mask for collision detection
        self.update()
        
    # Update the player's rect and mask for collision detection
    def update(self):
        self.rect = self.sprite.get_rect(topleft=(self.rect.x, self.rect.y))
        self.mask = pygame.mask.from_surface(self.sprite)

    # Draw the player on the window
    def draw(self, win, offset_x):
        win.blit(self.sprite, (self.rect.x - offset_x, self.rect.y))

# Base class for objects in the game
class Object(pygame.sprite.Sprite):
    def __init__(self, x, y, width, height, name=None):
        super().__init__()
        self.rect = pygame.Rect(x, y, width, height)
        self.image = pygame.Surface((width, height), pygame.SRCALPHA)
        self.width = width
        self.height = height
        self.name = name
            
    # Draw the object on the window
    def draw(self, win, offset_x):
        win.blit(self.image, (self.rect.x - offset_x, self.rect.y))

# Block class for terrain blocks
class Block(Object):
    def __init__(self, x, y, size):
        super().__init__(x, y, size, size)
        block = get_block(size)
        self.image.blit(block, (0, 0))
        self.mask = pygame.mask.from_surface(self.image)
    
# Class for fire
class Fire(Object):
    ANIMATION_DELAY = 3
    
    def __init__(self, x, y, width, height):
        super().__init__(x, y, width, height, "fire")
        # Load fire animation sprites
        self.fire = load_sprite_sheets("Traps", "Fire", width, height)
        self.image = self.fire["off"][0]
        self.mask = pygame.mask.from_surface(self.image)
        self.animation_count = 0
        self.animation_name = "off"
        
    def on(self):
        # Activate fire animation
        self.animation_name = "on"
        
    def off(self):
        # Deactivate fire animation
        self.animation_name = "off"
        
    def loop(self):
        # Update fire animation based on current state
        sprites = self.fire[self.animation_name]
        sprite_index = (self.animation_count // 
                        self.ANIMATION_DELAY) % len(sprites)
        self.image = sprites[sprite_index]
        self.animation_count += 1
        
        self.rect = self.image.get_rect(topleft=(self.rect.x, self.rect.y))
        self.mask = pygame.mask.from_surface(self.image)
        
        # Reset animation count to loop animation
        if self.animation_count // self.ANIMATION_DELAY > len(sprites):
            self.animation_count = 0
    
# Function to load and tile the background image
def get_background(name):
    image = pygame.image.load(join("assets", "Background", name))
    _, _, width, height = image.get_rect()
    tiles = []
    
    # Create a tiled background
    for i in range(WIDTH // width + 1):
        for j in range(HEIGHT // height + 1):
            pos = (i * width, j * height)
            tiles.append(pos)
            
    return tiles, image

# Function to draw everything on the window
def draw(window, background, bg_image, player, objects, offset_x):
    # Draw background tiles
    for tile in background:
        window.blit(bg_image, tile)
    
    # Draw all objects in the game
    for obj in objects:
        obj.draw(window, offset_x)
    
    # Draw the player
    player.draw(window, offset_x)

    pygame.display.update()
    
# Function to handle vertical collisions
def handle_vertical_collision(player, objects, dy):
    collided_objects = []
    for obj in objects:
        if pygame.sprite.collide_mask(player, obj):
            # Adjust player position on collision and update state
            if dy > 0:
                player.rect.bottom = obj.rect.top
                player.landed()
            elif dy < 0:
                player.rect.top = obj.rect.bottom
                player.hit_head()
                
            collided_objects.append(obj)
        
    return collided_objects

# Function to detect collisions during horizontal movement
def collide(player, objects, dx):
    player.move(dx, 0) # Move the player
    player.update() # Update the player's rect and mask
    collided_object = None
    for obj in objects:
        if pygame.sprite.collide_mask(player, obj):
            collided_object = obj
            break
        
    player.move(-dx, 0) #Move the player back if a collision is detected
    player.update()
    return collided_object

# Function to handle player movement and collisions
def handle_move(player, objects):
    keys = pygame.key.get_pressed()
    
    player.x_vel = 0
    # Check for collisions on both sides
    collide_left = collide(player, objects, -PLAYER_VEL * 2)
    collide_right = collide(player, objects, PLAYER_VEL * 2)
    
    # Move player based on input and collision state
    if keys[pygame.K_LEFT] and not collide_left:
        player.move_left(PLAYER_VEL)
    if keys[pygame.K_RIGHT] and not collide_right:
        player.move_right(PLAYER_VEL)    
        
    # Handle vertical collisions after movement
    vertical_collide = handle_vertical_collision(player, objects, player.y_vel)
    to_check = [collide_left, collide_right, *vertical_collide]
    for obj in to_check:
        if obj and obj.name == "fire":
            player.make_hit()

# Main game loop
def main(window):
    clock = pygame.time.Clock()
    # Load and tile background
    background, bg_image = get_background("Blue.png")
    
    block_size = 96

    # Initialize player and obstacles
    player = Player(100, 100, 50, 50)
    fire = Fire(100, HEIGHT - block_size - 64, 16, 32)
    fire.on()
    # Create floor and other static objects
    floor = [Block(i * block_size, HEIGHT - block_size, block_size)
             for i in range(-WIDTH // block_size, WIDTH * 2 // block_size)]
    objects = [*floor, Block(0, HEIGHT - block_size * 2, block_size), 
               Block(block_size * 3, HEIGHT - block_size * 4, block_size), fire]
    
    offset_x = 0 # For horizontal scrolling
    scroll_area_width = 200 # Scroll trigger area width
    
    run = True
    while run:
        clock.tick(FPS)
        
        # Event handling (input and window close)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
                break
            
            # Handle jump input
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE and player.jump_count < 2:
                    player.jump()

        # Update game state
        player.loop(FPS)
        fire.loop()
        handle_move(player, objects)
        draw(window, background, bg_image, player, objects, offset_x)

        # Scroll the view if the player approaches the edge of the screen
        if ((player.rect.right - offset_x >= WIDTH - scroll_area_width) and player.x_vel > 0) or (
                (player.rect.left - offset_x <= scroll_area_width) and player.x_vel < 0):
            offset_x += player.x_vel

    pygame.quit()
    quit()

if __name__ == "__main__":
    main(window)