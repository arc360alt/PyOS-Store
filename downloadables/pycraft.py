# PLEASE INSTALL ursina, numpy, and perlin_noise, FROM PIP FOR THIS TO WORK AT ALL

from ursina import *
from ursina.prefabs.first_person_controller import FirstPersonController
import numpy as np
import time
import random
from perlin_noise import PerlinNoise  # Make sure to pip install perlin-noise

# Render settings for better performance
from ursina.shaders import lit_with_shadows_shader

# Set some application optimizations
app = Ursina(title="Minecraft Clone", vsync=False)
window.borderless = False
window.fullscreen = False
window.exit_button.visible = False
window.fps_counter.enabled = True

# Reduce shadow quality for better performance
DirectionalLight(y=2, z=3, shadows=True, shadow_resolution=512)

# Global variables
BLOCK_TYPES = {
    'GRASS': color.rgba(0, 0.8, 0.1, 1),
    'DIRT': color.rgba(0.6, 0.3, 0, 1),
    'STONE': color.rgba(0.5, 0.5, 0.5, 1),
    'SAND': color.rgba(0.9, 0.8, 0.2, 1),
    'WATER': color.rgba(0, 0.3, 0.8, 0.6),
    'WOOD': color.rgba(0.3, 0.2, 0, 1),
    'BEDROCK': color.rgba(0.2, 0.2, 0.2, 1),  # Added bedrock type
}

# Chunk system settings
CHUNK_SIZE = 8  # Reduced for better performance
RENDER_DISTANCE = 1  # Reduced for better performance
WORLD_HEIGHT = 20

# Performance optimization
MAX_BLOCKS_PER_FRAME = 50  # Limit blocks created per frame
CHUNK_LOAD_INTERVAL = 0.5  # Time in seconds between chunk updates

# Global objects
player = None
pause_menu = None
chunks = {}  # Dictionary to store chunks: key = (chunk_x, chunk_z)
active_blocks = {}  # Dictionary to store only active blocks: key = position tuple, value = block entity

# Generate terrain with Perlin noise
terrain_noise = PerlinNoise(octaves=2, seed=random.randint(1, 1000))
tree_noise = PerlinNoise(octaves=3, seed=random.randint(1, 1000))
water_noise = PerlinNoise(octaves=4, seed=random.randint(1, 10))  # Add water noise


def get_height(x, z):
    # Get value from noise function
    noise_val = terrain_noise([x / 30, z / 30])

    # Scale and offset to get reasonable heights (0-10)
    height = int((noise_val + 0.5) * 6) + 1
    return max(1, height)  # Ensure minimum height of 1


def is_water_area(x, z):
    # Use water noise to determine if this location should have water
    water_val = water_noise([x / 40, z / 40])
    # Water areas where noise value is high and terrain is low
    height = get_height(x, z)
    return water_val > 0.1 and height <= 2


class Chunk:
    def __init__(self, position):
        self.position = position  # (chunk_x, chunk_z)
        self.blocks = {}  # Local dictionary of blocks within this chunk
        self.generated = False
        self.entity = Entity(model=None, position=Vec3(0, 0, 0))  # Parent entity for the chunk

    def generate(self):
        if self.generated:
            return

        chunk_x, chunk_z = self.position
        world_x_start = chunk_x * CHUNK_SIZE
        world_z_start = chunk_z * CHUNK_SIZE

        # Generate terrain for this chunk using Perlin noise
        for x in range(CHUNK_SIZE):
            for z in range(CHUNK_SIZE):
                # Calculate absolute world position
                world_x = world_x_start + x
                world_z = world_z_start + z

                # Use Perlin noise for height
                height = get_height(world_x, world_z)

                # Check if this should be a water area
                is_water = is_water_area(world_x, world_z)

                if is_water:
                    # Create water block at level 2
                    water_pos = Vec3(world_x, 2, world_z)
                    water_local_pos = (x, 2, z)

                    self.blocks[water_local_pos] = {
                        'position': water_pos,
                        'type': 'WATER',
                        'entity': None
                    }

                    # Create sand under water
                    sand_pos = Vec3(world_x, 1, world_z)
                    sand_local_pos = (x, 1, z)

                    self.blocks[sand_local_pos] = {
                        'position': sand_pos,
                        'type': 'SAND',
                        'entity': None
                    }
                else:
                    # Create top block
                    block_type = 'GRASS'
                    # Sometimes add sand patches
                    if height <= 2 and terrain_noise([world_x / 15, world_z / 15]) > 0.3:
                        block_type = 'SAND'

                    world_pos = Vec3(world_x, height, world_z)
                    local_pos = (x, height, z)

                    # Store block in chunk's local dictionary
                    self.blocks[local_pos] = {
                        'position': world_pos,
                        'type': block_type,
                        'entity': None
                    }

                    # Create dirt blocks below surface
                    for y in range(max(0, height - 1), max(0, height - 3), -1):
                        dirt_pos = Vec3(world_x, y, world_z)
                        dirt_local_pos = (x, y, z)

                        self.blocks[dirt_local_pos] = {
                            'position': dirt_pos,
                            'type': 'DIRT',
                            'entity': None
                        }

                    # Stone at bottom layers
                    for y in range(max(0, height - 3), 1, -1):
                        stone_pos = Vec3(world_x, y, world_z)
                        stone_local_pos = (x, y, z)

                        self.blocks[stone_local_pos] = {
                            'position': stone_pos,
                            'type': 'STONE',
                            'entity': None
                        }

                    # Occasionally add trees or wood blocks (simplified)
                    tree_value = tree_noise([world_x / 20, world_z / 20])
                    if block_type == 'GRASS' and tree_value > 0.6 and random.random() > 0.8:
                        # Add a simple tree trunk (just a column of wood blocks)
                        tree_height = random.randint(3, 5)
                        for y in range(1, tree_height + 1):
                            wood_pos = Vec3(world_x, height + y, world_z)
                            wood_local_pos = (x, height + y, z)

                            self.blocks[wood_local_pos] = {
                                'position': wood_pos,
                                'type': 'WOOD',
                                'entity': None
                            }

                # Add bedrock at y=0 (unbreakable bottom layer)
                bedrock_pos = Vec3(world_x, 0, world_z)
                bedrock_local_pos = (x, 0, z)

                self.blocks[bedrock_local_pos] = {
                    'position': bedrock_pos,
                    'type': 'BEDROCK',
                    'entity': None
                }

        self.generated = True

    def load(self):
        """Create actual block entities for this chunk"""
        if not self.generated:
            self.generate()

        # Performance optimization: limit blocks created per frame
        blocks_created = 0

        for local_pos, block_data in self.blocks.items():
            if block_data['entity'] is None:
                if blocks_created >= MAX_BLOCKS_PER_FRAME:
                    # Limit reached, will continue loading in next frame
                    return False

                world_pos = block_data['position']
                block_type = block_data['type']

                # Create block entity
                block = Block(position=world_pos, block_type=block_type, parent=self.entity)
                block_data['entity'] = block

                # Store in active blocks dictionary
                active_blocks[tuple(world_pos)] = block

                blocks_created += 1

        return True  # All blocks loaded

    def unload(self):
        """Remove all block entities from this chunk to free memory"""
        for local_pos, block_data in self.blocks.items():
            if block_data['entity'] is not None:
                # Remove from active blocks dictionary
                world_pos = block_data['position']
                if tuple(world_pos) in active_blocks:
                    del active_blocks[tuple(world_pos)]

                # Destroy entity
                destroy(block_data['entity'])
                block_data['entity'] = None

    def is_position_in_chunk(self, position):
        """Check if a world position is within this chunk"""
        chunk_x, chunk_z = self.position
        world_x_start = chunk_x * CHUNK_SIZE
        world_z_start = chunk_z * CHUNK_SIZE

        return (world_x_start <= position.x < world_x_start + CHUNK_SIZE and
                world_z_start <= position.z < world_z_start + CHUNK_SIZE)

    def get_block_at(self, position):
        """Get block at a world position if it's in this chunk"""
        if not self.is_position_in_chunk(position):
            return None

        # Convert world position to local position
        chunk_x, chunk_z = self.position
        world_x_start = chunk_x * CHUNK_SIZE
        world_z_start = chunk_z * CHUNK_SIZE

        local_x = int(position.x - world_x_start)
        local_y = int(position.y)
        local_z = int(position.z - world_z_start)

        local_pos = (local_x, local_y, local_z)
        return self.blocks.get(local_pos)

    def add_block(self, position, block_type):
        """Add a block at the specified world position if it's in this chunk"""
        if not self.is_position_in_chunk(position):
            return False

        # Convert world position to local position
        chunk_x, chunk_z = self.position
        world_x_start = chunk_x * CHUNK_SIZE
        world_z_start = chunk_z * CHUNK_SIZE

        local_x = int(position.x - world_x_start)
        local_y = int(position.y)
        local_z = int(position.z - world_z_start)

        local_pos = (local_x, local_y, local_z)

        # Check if there's already a block here
        if local_pos in self.blocks:
            return False

        # Create block data and entity
        block = Block(position=position, block_type=block_type, parent=self.entity)

        # Store in chunk's local dictionary
        self.blocks[local_pos] = {
            'position': position,
            'type': block_type,
            'entity': block
        }

        # Store in active blocks dictionary
        active_blocks[tuple(position)] = block
        return True

    def remove_block(self, position):
        """Remove a block at the specified world position if it's in this chunk"""
        if not self.is_position_in_chunk(position):
            return False

        # Convert world position to local position
        chunk_x, chunk_z = self.position
        world_x_start = chunk_x * CHUNK_SIZE
        world_z_start = chunk_z * CHUNK_SIZE

        local_x = int(position.x - world_x_start)
        local_y = int(position.y)
        local_z = int(position.z - world_z_start)

        local_pos = (local_x, local_y, local_z)

        # Check if there's a block here
        if local_pos not in self.blocks or self.blocks[local_pos]['entity'] is None:
            return False

        # Get block data
        block_data = self.blocks[local_pos]

        # Remove from active blocks dictionary
        if tuple(position) in active_blocks:
            del active_blocks[tuple(position)]

        # Destroy entity
        destroy(block_data['entity'])
        block_data['entity'] = None

        # Remove from blocks dictionary
        del self.blocks[local_pos]
        return True


class Block(Button):
    def __init__(self, position, block_type='GRASS', parent=scene):
        # Use Entity instead of Button for better performance
        super().__init__(
            parent=parent,
            position=position,
            model='cube',
            color=BLOCK_TYPES[block_type],
            highlight_color=color.rgba(1, 1, 1, 0.2),
            texture='white_cube',
            collider='box',
            scale=0.999,  # Slightly smaller to see edges
            shader=lit_with_shadows_shader  # Use simpler shader for performance
        )
        self.block_type = block_type

    def input(self, key):
        if self.hovered:
            if key == 'left mouse down' and not player.ignore_input:
                # Don't allow breaking bedrock
                if self.block_type != 'BEDROCK':
                    remove_block(self.position)
            elif key == 'right mouse down' and not player.ignore_input:
                # Calculate position based on normal
                new_pos = self.position + mouse.normal
                # Check player position to avoid trapping
                player_pos = player.position
                if not (abs(new_pos.x - player_pos.x) < 0.7 and
                        abs(new_pos.y - player_pos.y) < 1.7 and
                        abs(new_pos.z - player_pos.z) < 0.7):
                    add_block(new_pos, player.current_block)


class MinecraftPlayer(FirstPersonController):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.speed = 8
        self.jump_height = 2.5
        self.gravity = 1
        self.inventory = list(BLOCK_TYPES.keys())
        self.current_block_index = 0
        self.current_block = self.inventory[self.current_block_index]
        self.ignore_input = False

        # Initialize empty lists for UI components
        self.hotbar_buttons = []
        self.hotbar_texts = []

        # Create UI for inventory - simplified for performance
        self.inventory_ui = Text(
            text=f"Selected: {self.current_block}",
            position=(0, -0.45),
            origin=(0, 0),
            scale=1.5,
            color=color.white
        )

        # Create hotbar background with simpler styling
        self.hotbar_bg = Entity(
            parent=camera.ui,
            model='quad',
            color=color.rgba(0, 0, 0, 0.7),
            scale=(0.8, 0.12),
            position=(0, -0.45)
        )

        # Create text-based hotbar for performance
        for i, block_type in enumerate(self.inventory):
            # Create colored text for each block type
            block_text = Text(
                parent=camera.ui,
                text=block_type[0],  # First letter of block type
                color=BLOCK_TYPES[block_type],
                scale=2,
                position=(-0.35 + i * 0.18, -0.45),
                origin=(0, 0)
            )

            # Add selection indicator
            block_frame = Button(
                parent=camera.ui,
                model='quad',
                color=color.rgba(0, 0, 0, 0),
                highlight_color=color.rgba(1, 1, 1, 0.2),
                scale=(0.09, 0.09),
                position=(-0.35 + i * 0.18, -0.45),
                z=-0.05
            )

            def make_select_func(idx):
                def select_block():
                    self.current_block_index = idx
                    self.current_block = self.inventory[idx]
                    self.inventory_ui.text = f"Selected: {self.current_block}"
                    self.update_hotbar()

                return select_block

            block_frame.on_click = make_select_func(i)
            self.hotbar_buttons.append(block_frame)
            self.hotbar_texts.append(block_text)

        # Highlight initial selection
        self.update_hotbar()

    def update(self):
        # Check for pause menu toggle
        if held_keys['escape'] and not hasattr(self, 'escape_pressed_last_frame'):
            pause_menu.toggle()
            self.escape_pressed_last_frame = True
        elif not held_keys['escape']:
            self.escape_pressed_last_frame = False

        # Don't update player controls if game is paused
        if self.ignore_input:
            return

        # Check if player fell through the world
        if self.position.y < -10:
            self.position = Vec3(0, 10, 0)  # Respawn above

        super().update()

        # Switch blocks with number keys
        for i in range(min(9, len(self.inventory))):
            if held_keys[str(i + 1)]:
                self.current_block_index = i
                self.current_block = self.inventory[i]
                self.inventory_ui.text = f"Selected: {self.current_block}"
                self.update_hotbar()
                break

        # Or switch with scroll wheel
        if held_keys['scroll up']:
            self.current_block_index = (self.current_block_index - 1) % len(self.inventory)
            self.current_block = self.inventory[self.current_block_index]
            self.inventory_ui.text = f"Selected: {self.current_block}"
            self.update_hotbar()

        if held_keys['scroll down']:
            self.current_block_index = (self.current_block_index + 1) % len(self.inventory)
            self.current_block = self.inventory[self.current_block_index]
            self.inventory_ui.text = f"Selected: {self.current_block}"
            self.update_hotbar()

    def update_hotbar(self):
        # Update the hotbar to show the current selection
        for i, block_btn in enumerate(self.hotbar_buttons):
            if i == self.current_block_index:
                block_btn.scale = (0.09, 0.09)
                block_btn.color = color.rgba(1, 1, 1, 0.2)
                self.hotbar_texts[i].scale = 2.5  # Make text bigger for selected item
            else:
                block_btn.scale = (0.07, 0.07)
                block_btn.color = color.rgba(0, 0, 0, 0)
                self.hotbar_texts[i].scale = 2  # Normal size for unselected items


class PauseMenu(Entity):
    def __init__(self):
        super().__init__(
            parent=camera.ui,
            model='quad',
            scale=(0.8, 0.9),
            color=color.rgba(0, 0, 0, 0.8),
            enabled=False
        )

        self.title = Text(
            parent=self,
            text="Game Paused",
            scale=3,
            position=(0, 0.35),
            origin=(0, 0),
            color=color.white
        )

        # Instructions text - moved here from main screen
        self.instructions = Text(
            parent=self,
            text="WASD to move, Space to jump\nLeft click to break, Right click to place blocks\nNumber keys (1-6) to select blocks\nEsc to toggle pause menu",
            scale=1.2,
            position=(0, 0.25),
            origin=(0, 0),
            color=color.white
        )

        # Resume button
        self.resume_button = Button(
            parent=self,
            text="Resume Game",
            scale=(0.5, 0.08),
            position=(0, 0.05),
            color=color.azure,
            highlight_color=color.azure.tint(0.2)
        )
        self.resume_button.on_click = self.toggle

        # Window size buttons
        self.window_size_button = Button(
            parent=self,
            text="Toggle Fullscreen",
            scale=(0.5, 0.08),
            position=(0, -0.05),
            color=color.orange,
            highlight_color=color.orange.tint(0.2)
        )
        self.window_size_button.on_click = self.toggle_fullscreen

        # Window size manual buttons
        self.window_size_small = Button(
            parent=self,
            text="800x600",
            scale=(0.15, 0.08),
            position=(-0.25, -0.15),
            color=color.orange,
            highlight_color=color.orange.tint(0.2)
        )
        self.window_size_small.on_click = lambda: self.set_window_size(800, 600)

        self.window_size_medium = Button(
            parent=self,
            text="1024x768",
            scale=(0.15, 0.08),
            position=(0, -0.15),
            color=color.orange,
            highlight_color=color.orange.tint(0.2)
        )
        self.window_size_medium.on_click = lambda: self.set_window_size(1024, 768)

        self.window_size_large = Button(
            parent=self,
            text="1280x720",
            scale=(0.15, 0.08),
            position=(0.25, -0.15),
            color=color.orange,
            highlight_color=color.orange.tint(0.2)
        )
        self.window_size_large.on_click = lambda: self.set_window_size(1280, 720)

        # FOV slider
        self.fov_text = Text(
            parent=self,
            text="FOV: 70",
            position=(-0.3, -0.25),
            origin=(-0.5, 0),
            color=color.white
        )

        # Create a wider FOV slider that's easier to click
        self.fov_slider = Slider(
            parent=self,
            min=40,
            max=120,
            default=70,
            step=1,
            dynamic=True,
            position=(0.1, -0.25),
            scale=(0.5, 0.08),  # Increased height and width
            on_value_changed=lambda value: self.set_fov(value)  # Pass the value correctly
        )

        # Exit button
        self.exit_button = Button(
            parent=self,
            text="Exit Game",
            scale=(0.5, 0.08),
            position=(0, -0.4),
            color=color.red,
            highlight_color=color.red.tint(0.2)
        )
        self.exit_button.on_click = self.exit_game

    def toggle(self):
        self.enabled = not self.enabled
        player.cursor.locked = not self.enabled
        if self.enabled:
            mouse.locked = False
            player.ignore_input = True
        else:
            mouse.locked = True
            player.ignore_input = False

    def toggle_fullscreen(self):
        window.fullscreen = not window.fullscreen

    def set_window_size(self, width, height):
        window.windowed_size = (width, height)
        window.fullscreen = False
        window.center_on_screen()

    def set_fov(self, value):
        camera.fov = value
        self.fov_text.text = f"FOV: {int(value)}"

    def exit_game(self):
        application.quit()


# Performance variables
chunk_update_timer = 0
chunks_to_process = []
loading_text = None


def get_chunk_position(position):
    """Get chunk coordinates from world position"""
    chunk_x = int(position.x) // CHUNK_SIZE
    chunk_z = int(position.z) // CHUNK_SIZE
    return (chunk_x, chunk_z)


def get_chunk(position):
    """Get chunk at the specified world position"""
    chunk_pos = get_chunk_position(position)
    return chunks.get(chunk_pos)


def add_block(position, block_type):
    """Add a block at the specified world position"""
    # Get the chunk for this position
    chunk_pos = get_chunk_position(position)

    # Check if chunk exists
    if chunk_pos not in chunks:
        # Create and generate chunk if it doesn't exist
        chunks[chunk_pos] = Chunk(chunk_pos)
        chunks[chunk_pos].generate()

    # Add block to chunk
    chunk = chunks[chunk_pos]
    return chunk.add_block(position, block_type)


def remove_block(position):
    """Remove a block at the specified world position"""
    # Get the chunk for this position
    chunk_pos = get_chunk_position(position)

    # Check if chunk exists
    if chunk_pos not in chunks:
        return False

    # Remove block from chunk
    chunk = chunks[chunk_pos]
    return chunk.remove_block(position)


def update_chunks():
    """Update chunks based on player position with performance optimizations"""
    global chunk_update_timer, chunks_to_process, loading_text

    # Only update chunks periodically, not every frame
    chunk_update_timer += time.dt
    if chunk_update_timer < CHUNK_LOAD_INTERVAL and not chunks_to_process:
        return

    chunk_update_timer = 0

    if not player:
        return

    # Get player's chunk position
    player_chunk_pos = get_chunk_position(player.position)
    player_chunk_x, player_chunk_z = player_chunk_pos

    # If we still have chunks to process from last frame, continue with those
    if not chunks_to_process:
        # Determine which chunks should be loaded
        for x in range(player_chunk_x - RENDER_DISTANCE, player_chunk_x + RENDER_DISTANCE + 1):
            for z in range(player_chunk_z - RENDER_DISTANCE, player_chunk_z + RENDER_DISTANCE + 1):
                chunk_pos = (x, z)
                if chunk_pos not in chunks:
                    # Create new chunk
                    chunks[chunk_pos] = Chunk(chunk_pos)
                    chunks[chunk_pos].generate()
                    chunks_to_process.append(chunk_pos)
                elif chunks[chunk_pos].generated and any(
                        block_data['entity'] is None for block_data in chunks[chunk_pos].blocks.values()
                ):
                    # Chunk exists but has unloaded blocks
                    chunks_to_process.append(chunk_pos)

        # Unload chunks that are too far away
        for chunk_pos in list(chunks.keys()):
            chunk_x, chunk_z = chunk_pos
            if (abs(chunk_x - player_chunk_x) > RENDER_DISTANCE or
                    abs(chunk_z - player_chunk_z) > RENDER_DISTANCE):
                chunks[chunk_pos].unload()

    # Process a limited number of chunks per frame
    if chunks_to_process:
        # Show loading indicator if there are chunks to process
        if loading_text is None:
            loading_text = Text(
                text="Loading chunks...",
                position=(0, 0.3),
                origin=(0, 0),
                scale=2,
                color=color.white
            )

        # Process one chunk
        chunk_pos = chunks_to_process[0]
        if chunk_pos in chunks:
            fully_loaded = chunks[chunk_pos].load()
            if fully_loaded:
                chunks_to_process.pop(0)
        else:
            chunks_to_process.pop(0)

        # Hide loading text when done
        if not chunks_to_process and loading_text:
            destroy(loading_text)
            loading_text = None


# Generate world using chunk system
def generate_initial_chunks():
    # Generate chunks around starting position
    player_chunk_pos = get_chunk_position(Vec3(0, 0, 0))
    player_chunk_x, player_chunk_z = player_chunk_pos

    for x in range(player_chunk_x - 1, player_chunk_x + 2):
        for z in range(player_chunk_z - 1, player_chunk_z + 2):
            chunk_pos = (x, z)
            chunks[chunk_pos] = Chunk(chunk_pos)
            chunks[chunk_pos].generate()
            chunks[chunk_pos].load()


# Create player
player = MinecraftPlayer(position=Vec3(0, 10, 0))
camera.fov = 70

# Create pause menu
pause_menu = PauseMenu()

# Generate initial chunks
generate_initial_chunks()

# Create a stronger crosshair for better visibility
crosshair = Entity(
    parent=camera.ui,
    model='quad',
    texture='white_cube',
    scale=0.015,
    color=color.black66
)

# Add FPS counter in the corner
fps_counter = Text(
    text="FPS: 0",
    position=(0.75, 0.45),
    scale=1.2,
    color=color.white
)


def update():
    # Update FPS counter
    if time.dt > 0:  # Avoid division by zero
        fps_counter.text = f"FPS: {round(1 / time.dt)}"

    # Alternative escape key check in global update function
    if held_keys['escape'] and not hasattr(pause_menu, 'escape_pressed_global'):
        pause_menu.toggle()
        pause_menu.escape_pressed_global = True
    elif not held_keys['escape']:
        if hasattr(pause_menu, 'escape_pressed_global'):
            delattr(pause_menu, 'escape_pressed_global')

    # Update chunks if not paused
    if not pause_menu.enabled:
        update_chunks()


# Run the game
app.run()