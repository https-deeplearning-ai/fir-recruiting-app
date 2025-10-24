#!/usr/bin/env python3
"""
Create minimal placeholder PNG icons for the Chrome extension.
These are valid PNG files that will allow the extension to load.
"""

import base64

# Minimal valid PNG files in different sizes (these are solid color squares)
# Each is a valid PNG that Chrome will accept

# 16x16 purple square
icon16_base64 = "iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAABHNCSVQICAgIfAhkiAAAAAlwSFlzAAAAbwAAAG8B8aLcQwAAABl0RVh0U29mdHdhcmUAd3d3Lmlua3NjYXBlLm9yZ5vuPBoAAABJSURBVDiN7dAxDgAgCAPA/v+zOlhaWjQZDBpD4gklIiLyqqo6M3Nn5vZ9H5xzYmYQEVhroaoopeC9h4ig1gohBIwxkFLCGPMBF/YID3vN5eoAAAAASUVORK5CYII="

# 48x48 purple square
icon48_base64 = "iVBORw0KGgoAAAANSUhEUgAAADAAAAAwCAYAAABXAvmHAAAABHNCSVQICAgIfAhkiAAAAAlwSFlzAAAA0gAAANIBBp0MHQAAABl0RVh0U29mdHdhcmUAd3d3Lmlua3NjYXBlLm9yZ5vuPBoAAABuSURBVGiB7dihDcAgFATQF4YwBROwAiOwEiM0E7ACA5iAISqrqKr+dyTvJZdc7vI/+Z8kSVrVOeecUsqw3jnnGGPgnIMxBt57CCFASglVRa0VIgLWWpgZ3nsQEbTWwMxYa4GZsZaCiGCMgYh+AXdaFA/r1V8yAAAAAElFTkSuQmCC"

# 128x128 purple square
icon128_base64 = "iVBORw0KGgoAAAANSUhEUgAAAIAAAACACAYAAADDPmHLAAAABHNCSVQICAgIfAhkiAAAAAlwSFlzAAAC1AAAAtQBhSijVgAAABl0RVh0U29mdHdhcmUAd3d3Lmlua3NjYXBlLm9yZ5vuPBoAAACOSURBVHic7dyhEYAgFADQBxMwgatwE1fBSdyEVXASN9FJLBYLgfeSezngyH0OkiRJkiRJkiRJkiRJkiRJkiRJkiT9p845xxiDiCCEgKqilIKIwHuPGGNQVdRaISIQEXjvYYyBtRbOOWit4b2HMQbGGKSUgJkxxkBVkVLCnBPMjDEGmBlzTlRVfd8vxJkSkGT4iZsAAAAASUVORK5CYII="

def create_icon(filename, base64_data):
    """Create an icon file from base64 data"""
    with open(filename, 'wb') as f:
        f.write(base64.b64decode(base64_data))
    print(f"Created {filename}")

def main():
    """Create all placeholder icons"""
    create_icon('icon16.png', icon16_base64)
    create_icon('icon48.png', icon48_base64)
    create_icon('icon128.png', icon128_base64)

    print("\nPlaceholder icons created successfully!")
    print("These are minimal valid PNG files that will allow the extension to load.")
    print("For production, replace these with proper branded icons.")

if __name__ == "__main__":
    main()