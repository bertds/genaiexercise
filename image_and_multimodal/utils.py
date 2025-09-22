import os
import io
import base64
import matplotlib.pyplot as plt
from PIL import Image
import numpy as np

def save_image(image_data, filename, output_dir="output"):
    """
    Save a base64 encoded image to a file
    
    Args:
        image_data (str): Base64 encoded image data
        filename (str): Filename to save the image as
        output_dir (str): Directory to save the image in
    
    Returns:
        str: Path to the saved image
    """
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Decode the base64 image data
    image_bytes = base64.b64decode(image_data)
    
    # Create a PIL Image from the bytes
    image = Image.open(io.BytesIO(image_bytes))
    
    # Create the full path
    path = os.path.join(output_dir, filename)
    
    # Save the image
    image.save(path)
    
    return path

def plot_images(images, titles=None, figsize=(15, 15), columns=3):
    """
    Plot multiple images in a grid
    
    Args:
        images (list): List of PIL Images or paths to images
        titles (list): Optional list of titles for each image
        figsize (tuple): Figure size (width, height)
        columns (int): Number of columns in the grid
    """
    # Calculate number of rows needed
    rows = (len(images) + columns - 1) // columns
    
    # Create figure and axes
    fig, axes = plt.subplots(rows, columns, figsize=figsize)
    
    # Flatten axes if there are multiple rows
    if rows > 1:
        axes = axes.flatten()
    elif rows == 1 and columns == 1:
        axes = [axes]
    
    # Plot each image
    for i, image in enumerate(images):
        if i < len(axes):
            # Load image if it's a path
            if isinstance(image, str):
                image = Image.open(image)
            
            # Display image
            axes[i].imshow(np.array(image))
            
            # Set title if provided
            if titles and i < len(titles):
                axes[i].set_title(titles[i])
            
            # Remove axis ticks
            axes[i].set_xticks([])
            axes[i].set_yticks([])
    
    # Hide unused axes
    for i in range(len(images), len(axes)):
        axes[i].axis('off')
    
    plt.tight_layout()
    plt.show()
