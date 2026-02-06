# Google Maps Timeline Heatmap Generator

This tool generates a smooth heatmap from your Google Maps timeline JSON data. It aggregates location points into a customizable grid and displays the resulting heatmap using Folium.
Inspired by geo-heatmap repo from luka1199; https://github.com/luka1199/geo-heatmap .
This is a simple code created for fun, and will not be updated. For more features and support, use https://github.com/kurupted/google-maps-timeline-viewer .

## Features

- **JSON Data Parsing:** Reads and extracts location data from your Google Maps timeline.
- **Customizable Grid:** Aggregates points into grid cells with adjustable size and capacity.
- **Heatmap Visualization:** Uses a Matplotlib colormap to create a smooth gradient heatmap.
- **Interactive Map:** Generates an HTML file with an interactive map, limited zoom levels, and a minimap.

## Requirements

- Python 3.x
- [Folium](https://python-visualization.github.io/folium/)
- [Matplotlib](https://matplotlib.org/)

Install the required libraries using pip:

```bash
pip install folium matplotlib
```

## Usage

Get your timeline from google by following http://maps.google.com/maps/timeline. With recent changes, timeline is saved on devices, therefore you probably have to check through your phone to get your travel history.
Move the timeline.json from your phone to your computer.

Run the script from the command line:

```bash
python3 heatmap.py path/to/timeline.json -o output_heatmap.html --min-zoom 3 --max-zoom 12 --grid-size 500 --grid-capacity 10 --colormap gist_ncar --colormap-max 1.0
```

### Command-Line Arguments

- **file**: Path to the Google Maps timeline JSON data file.
- **-o, --output**: Output HTML file for the heatmap (default: `heatmap.html`).
- **--min-zoom**: Minimum zoom level allowed (default: 3).
- **--max-zoom**: Maximum zoom level allowed (default: 12).
- **--grid-size**: Grid size in meters (default: 500).
- **--grid-capacity**: Maximum capacity for each grid cell (default: 10).
- **--colormap**: Matplotlib colormap name for the heatmap gradient (default: `gist_ncar`).
- **--colormap-max**: Maximum normalized value for the colormap (default: 1.0).

## Example

If you have a timeline JSON file named `timeline.json`, generate the heatmap by running:

```bash
python3 heatmap.py timeline.json -o my_heatmap.html --min-zoom 3 --max-zoom 12 --grid-size 500 --grid-capacity 10 --colormap gist_ncar --colormap-max 1.0
```

This will create an interactive HTML file (`my_heatmap.html`) that displays your heatmap.

ps. i recommend colormap afmhot
