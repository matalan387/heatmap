!pip install gpxpy
!pip install fitparse 
!pip install tqdm 
!pip install folium 
!pip install os

import folium
import os
import gpxpy
import xml.etree.ElementTree as ET
from fitparse import FitFile
from tqdm import tqdm  # Progress bar
from google.colab import drive, files

# Mount Google Drive
drive.mount('/content/drive')

def parse_gpx(file_path):
    with open(file_path, 'r') as file:
        gpx = gpxpy.parse(file)
    return [{'latitude': point.latitude, 'longitude': point.longitude}
            for track in gpx.tracks
            for segment in track.segments
            for point in segment.points]

def parse_tcx(file_path):
    tree = ET.parse(file_path)
    root = tree.getroot()
    namespace = {'tcx': 'http://www.garmin.com/xmlschemas/TrainingCenterDatabase/v2'}
    return [{'latitude': float(pos.find('tcx:LatitudeDegrees', namespace).text),
             'longitude': float(pos.find('tcx:LongitudeDegrees', namespace).text)}
            for pos in root.findall('.//tcx:Position', namespace)]

def parse_fit(file_path):
    fitfile = FitFile(file_path)
    coords = []
    for record in fitfile.get_messages('record'):
        lat = record.get_value('position_lat')
        lon = record.get_value('position_long')
        if lat is not None and lon is not None:
            # Convert semicircles to degrees
            coords.append({
                'latitude': lat * (180 / 2**31),
                'longitude': lon * (180 / 2**31)
            })
    return coords

def read_gps_files_from_folder(folder_path):
    data = []
    gps_files = [f for f in os.listdir(folder_path) if f.endswith((".gpx", ".tcx", ".fit"))]

    for filename in tqdm(gps_files, desc="Processing GPS Files"):
        file_path = os.path.join(folder_path, filename)
        try:
            if filename.endswith(".gpx"):
                track_data = parse_gpx(file_path)
            elif filename.endswith(".tcx"):
                track_data = parse_tcx(file_path)
            elif filename.endswith(".fit"):
                track_data = parse_fit(file_path)
            else:
                print(f"Unsupported file format: {filename}")
                continue
            
            data.append({
                'file': filename,
                'track': track_data
            })

        except FileNotFoundError:
            print(f"Error: File not found at path: {file_path}")
            continue
        except Exception as e:
            print(f"Error processing {filename}: {e}")
            continue

    return data

# Function to plot multiple GPX tracks on a single map
def plot_multiple_tracks(data):
    if not data:
        print("No data to plot.")
        return

    # Use the first valid point to center the map
    for track in data:
        if track['track']:
            map_center = [track['track'][0]['latitude'], track['track'][0]['longitude']]
            break
    else:
        print("No valid GPS data to center the map.")
        return

    # Create the map
    map_osm = folium.Map(location=map_center, zoom_start=13)

    # Colors for different tracks
    colors = ['purple']
    #, 'green', 'red', 'purple', 'orange', 'darkred', 
    #          'lightred', 'beige', 'darkblue', 'darkgreen', 'cadetblue', 
    #          'darkpurple', 'white', 'pink', 'lightblue', 'lightgreen']

    # Progress bar for plotting
    for idx, track in enumerate(tqdm(data, desc="Plotting Tracks")):
        track_points = track['track']
        if not track_points:
            continue

        latitudes = [point['latitude'] for point in track_points]
        longitudes = [point['longitude'] for point in track_points]

        # Add track as a polyline
        folium.PolyLine(
            list(zip(latitudes, longitudes)),
            color=colors[idx % len(colors)],
            weight=3,
            popup=track['file']
        ).add_to(map_osm)

        # Add start and end markers
        folium.Marker(
            [latitudes[0], longitudes[0]],
            popup=f'Start: {track["file"]}',
            icon=folium.Icon(color='green')
        ).add_to(map_osm)

        folium.Marker(
            [latitudes[-1], longitudes[-1]],
            popup=f'End: {track["file"]}',
            icon=folium.Icon(color='red')
        ).add_to(map_osm)

    return map_osm

# Specify the folder containing GPX files
folder_path = insert file path here

# Call read_gps_files_from_folder to populate the 'data' variable
data = read_gps_files_from_folder(folder_path) # This line is added to call the function and assign the result to 'data'

# Plot the data with progress visualization
map_display = plot_multiple_tracks(data)

# Display and save the map
if map_display:
    map_display.save('heatmap.html')
    files.download('heatmap.html')
    map_display

