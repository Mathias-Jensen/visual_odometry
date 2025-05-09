import csv
import utm
import matplotlib.pyplot as plt
import numpy as np

def convert_to_utm(latitudes, longitudes):
    """
    Convert latitude, longitude, and altitude to UTM coordinates.
    
    Args:
        latitudes (list): List of latitude values.
        longitudes (list): List of longitude values.
        altitudes (list): List of altitude values.
    
    Returns:
        list: List of tuples containing UTM coordinates (easting, northing, zone number, zone letter, altitude).
    """
    utm_coordinates = []
    for lat, lon in zip(latitudes, longitudes):
        easting, northing, zone_number, zone_letter = utm.from_latlon(float(lat), float(lon))
        utm_coordinates.append((easting, northing, zone_number, zone_letter))
    return utm_coordinates

path_csv = "/home/nicklas/Documents/DAS_semester2/lsdp/miniproject2_visual_odometry"

with open(path_csv + "/DJIFlightRecord_2021-03-18_[13-04-51]_TxtLogToCsv.csv", mode='r', encoding='ISO-8859-1') as file:
    csv_reader = csv.reader(file)
    header = next(csv_reader)  # Read the header row

    # Get the indices for the required columns
    lat_idx = header.index("OSD.latitude")
    lon_idx = header.index("OSD.longitude")
    alt_idx = header.index("OSD.altitude [m]")

    # Extract the required columns in a single pass
    lat, lon, alt = [], [], []
    for row in csv_reader:
        lat.append(row[lat_idx])
        lon.append(row[lon_idx])
        alt.append(row[alt_idx])


lat = lat[1077:1748]
lon = lon[1077:1748]
alt = alt[1077:1748]

utm_coor = convert_to_utm(lat, lon)
est = [coord[0] for coord in utm_coor]
nor = [coord[1] for coord in utm_coor]
est -= est[0]
nor -= nor[0]
#alt = [coord[4] for coord in utm_coor]


fig = plt.figure(figsize=(10, 8))

plt.plot(est, nor, 'b-', label='UTM Path')
plt.plot(est[0], nor[0], 'go', label='Start Point', markersize = 10)
plt.plot(est[-1], nor[-1], 'ro', label='End Point', markersize = 10)
plt.title('Reletive flight path in UTM coordinates', fontsize=18)
plt.xlabel('Easting [m]', fontsize=14)
plt.ylabel('Northing [m]', fontsize=14)
plt.legend()
plt.grid()
plt.axis('equal')  # Set equal scaling for both axes

# Show the plot
plt.tight_layout()
plt.savefig(path_csv + "/output/utm_path.png", dpi=300)
plt.close()