#!/usr/bin/env python3
import os
import sys
import json
import math
import argparse
import random

import folium
from folium.plugins import HeatMap

import matplotlib.cm as cm
import matplotlib.colors as mcolors

def get_gradient(cmap_name, n=10, lower_bound=0.4, upper_bound=1.0):
    """
    Generate a gradient dictionary from a matplotlib colormap.

    Parameters:
        cmap_name (str): Name of the matplotlib colormap.
        n (int): Number of stops in the gradient.
        lower_bound (float): Lower bound for the gradient keys.
        upper_bound (float): Upper bound for the gradient keys.

    Returns:
        dict: A gradient dictionary with keys as formatted strings.
    """
    try:
        cmap = cm.get_cmap(cmap_name, n)
    except ValueError:
        print(f"Invalid colormap name '{cmap_name}'. Falling back to default 'binary'. If you are sure the colormap exists, try updating matplotlib.")
        cmap = cm.get_cmap('binary', n)
    gradient = {}
    for i in range(n):
        # Compute key in the desired subrange:
        norm_val = lower_bound + (upper_bound - lower_bound) * (i / (n - 1))
        key = f"{norm_val:.2f}"  # format key as string, e.g., "0.40", "0.55", etc.
        # For the color, sample the colormap over the full 0-1 range:
        hex_color = mcolors.to_hex(cmap(i / (n - 1)))
        gradient[key] = hex_color
    return gradient

def add_noise(lat, lon, noise_level=0.001):
    """Add random noise to latitude and longitude."""
    lat += random.uniform(-noise_level, noise_level)
    lon += random.uniform(-noise_level, noise_level)
    return lat, lon

def parse_latlng(latlng_str):
    """
    Convert a coordinate string like "41.0080692°, 28.6558817°" 
    into a tuple of floats (latitude, longitude).
    """
    cleaned = latlng_str.replace('°', '')
    try:
        lat_str, lon_str = cleaned.split(',')
        return float(lat_str.strip()), float(lon_str.strip())
    except ValueError:
        raise ValueError(f"Could not parse latlng string: {latlng_str}")

def main():
    # Set up command-line argument parsing.
    parser = argparse.ArgumentParser(
        description="Generate a smooth heatmap from Google Maps timeline data using a customizable grid. "
                    "Also puts the data into grids and adds noise for some privacy in the output file."
    )
    parser.add_argument("file", help="Path to JSON data file (Google Maps timeline)")
    parser.add_argument("-o", "--output", default="heatmap.html",
                        help="Output HTML file for the heatmap (default: heatmap.html)")
    parser.add_argument("--min-zoom", type=int, default=3,
                        help="Minimum zoom level allowed (default: 3)")
    parser.add_argument("--max-zoom", type=int, default=12,
                        help="Maximum zoom level allowed (default: 12)")
    parser.add_argument("--grid-size", type=int, default=500,
                        help="Grid size in meters (default: 500m)")
    parser.add_argument("--grid-capacity", type=int, default=10,
                        help="Maximum capacity for each grid cell (default: 10)")
    parser.add_argument("--colormap", type=str, default="gist_ncar",
                        help="Matplotlib colormap name for the heatmap gradient (default: gist_ncar)")
    parser.add_argument("--colormap-max", type=float, default=1.0,
                        help="Maximum normalized value for the colormap (default: 1.0, e.g. set to 0.7 to limit)")
    args = parser.parse_args()

    filename = args.file
    if not os.path.isfile(filename):
        print(f"Error: File '{filename}' not found.")
        sys.exit(1)

    # --- Part 1: Load JSON Data ---
    print("Loading JSON data...")
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        print("Error decoding JSON:", e)
        sys.exit(1)

    segments = data.get("semanticSegments", [])
    if not segments:
        print("No 'semanticSegments' found in the JSON data.")
        sys.exit(1)

    # --- Part 2: Process segments ---
    print("Processing segments...")
    points = []
    for segment in segments:
        # Process points from "timelinePath" if available.
        if "timelinePath" in segment:
            for point_info in segment["timelinePath"]:
                point_str = point_info.get("point")
                if point_str:
                    try:
                        lat, lon = parse_latlng(point_str)
                        points.append((lat, lon))
                    except ValueError as e:
                        print(e)
        # Process a point from a "visit" if available.
        if "visit" in segment:
            visit = segment["visit"]
            top_candidate = visit.get("topCandidate", {})
            place_location = top_candidate.get("placeLocation", {})
            latlng_str = place_location.get("latLng")
            if latlng_str:
                try:
                    lat, lon = parse_latlng(latlng_str)
                    points.append((lat, lon))
                except ValueError as e:
                    print(e)

    if not points:
        print("No valid points extracted from data.")
        sys.exit(1)

    print(f"Total points extracted: {len(points)}")

    # --- Part 3: Aggregate points into a grid with customizable size and capacity ---
    # Compute bounding box.
    min_lat = min(lat for lat, _ in points)
    max_lat = max(lat for lat, _ in points)
    min_lon = min(lon for _, lon in points)
    max_lon = max(lon for _, lon in points)

    # Convert grid size from meters to degrees.
    grid_size_m = args.grid_size
    grid_lat = grid_size_m / 111111.0  # 1 degree latitude is roughly 111,111 meters.
    avg_lat = sum(lat for lat, _ in points) / len(points)
    grid_lon = grid_size_m / (111111.0 * math.cos(math.radians(avg_lat)))  # Adjust for longitude.

    # Aggregate points into grid cells with capacity limitation.
    grid_capacity = args.grid_capacity
    grid_counts = {}
    for lat, lon in points:
        # Add noise to the coordinates.
        lat, lon = add_noise(lat, lon)
        
        i = int((lat - min_lat) / grid_lat)
        j = int((lon - min_lon) / grid_lon)
        key = (i, j)
        
        # Limit the capacity of each grid cell.
        if grid_counts.get(key, 0) < grid_capacity:
            grid_counts[key] = grid_counts.get(key, 0) + 1

    # Prepare heatmap data: each grid cell is represented by its center coordinate
    # and weighted by the number of points in that cell.
    heat_data = []
    for (i, j), count in grid_counts.items():
        cell_center_lat = min_lat + (i + 0.5) * grid_lat
        cell_center_lon = min_lon + (j + 0.5) * grid_lon
        heat_data.append([cell_center_lat, cell_center_lon, count])

    # --- Part 4: Generate a smooth heatmap ---
    # Center the map at the midpoint of the bounding box.
    center_lat = (min_lat + max_lat) / 2
    center_lon = (min_lon + max_lon) / 2

    # Create a Folium map with limited zoom levels and an initial view of Europe.
    m = folium.Map(location=[54.5260, 15.2551],  # Centered on Europe
                   tiles="Cartodb Positron",     # Use a light basemap
                   zoom_start=args.min_zoom,     # Start at the minimum zoom level
                   min_zoom=args.min_zoom,       # Enforce minimum zoom
                   max_zoom=args.max_zoom,       # Enforce maximum zoom
                   control_scale=True)           # Add a scale control

    # Generate the custom gradient using the specified colormap and maximum normalized value.
    custom_gradient = get_gradient(args.colormap, n=10, lower_bound=0.4, upper_bound=1.0)

    # Add a heatmap overlay (adjust radius and blur for smooth blending).
    HeatMap(heat_data, radius=15, blur=20, gradient=custom_gradient).add_to(m)

    # --- Part 5: Save the map ---
    m.save(args.output)
    print(f"Heatmap saved to {args.output}")

if __name__ == "__main__":
    main()
