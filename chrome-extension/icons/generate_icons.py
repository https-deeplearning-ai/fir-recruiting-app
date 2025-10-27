#!/usr/bin/env python3
"""
Generate PNG icons for Chrome extension from base design.
Creates 16x16, 48x48, and 128x128 versions.
"""

from PIL import Image, ImageDraw, ImageFont
import os

def create_icon(size):
    """Create a simple icon with gradient background and text"""
    # Create image with transparent background
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Draw gradient background (approximated with solid color)
    # Using the primary color from our gradient
    primary_color = (102, 126, 234)  # #667eea
    secondary_color = (118, 75, 162)  # #764ba2

    # Simple circular background
    padding = size // 10
    draw.ellipse(
        [padding, padding, size - padding, size - padding],
        fill=(*primary_color, 255)
    )

    # Add "AI" text
    text = "AI"
    try:
        # Try to use a nice font if available
        font_size = size // 3
        font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", font_size)
    except:
        # Fallback to default font
        font = ImageFont.load_default()

    # Calculate text position
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]

    text_x = (size - text_width) // 2
    text_y = (size - text_height) // 2

    # Draw text in white
    draw.text((text_x, text_y), text, fill=(255, 255, 255, 255), font=font)

    return img

def main():
    """Generate all required icon sizes"""
    sizes = [16, 48, 128]

    for size in sizes:
        icon = create_icon(size)
        filename = f"icon{size}.png"
        icon.save(filename, 'PNG')
        print(f"Created {filename}")

    print("\nIcons generated successfully!")
    print("Note: For production, consider using a professional design tool")
    print("or online icon generator for better quality icons.")

if __name__ == "__main__":
    # Check if PIL is installed
    try:
        from PIL import Image, ImageDraw, ImageFont
        main()
    except ImportError:
        print("Pillow library is not installed.")
        print("Creating simple placeholder icons instead...")

        # Create simple placeholder files
        sizes = [16, 48, 128]
        for size in sizes:
            filename = f"icon{size}.png"

            # Create a minimal 1x1 PNG file as placeholder
            # This is the smallest valid PNG file
            png_data = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\rIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00\x05\xb7\xee\xaa\x00\x00\x00\x00IEND\xaeB`\x82'

            with open(filename, 'wb') as f:
                f.write(png_data)
            print(f"Created placeholder {filename}")

        print("\nPlaceholder icons created.")
        print("To create proper icons, install Pillow: pip install Pillow")
        print("Or use an online tool like: https://favicon.io/")