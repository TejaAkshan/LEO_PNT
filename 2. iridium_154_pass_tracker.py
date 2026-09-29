from skyfield.api import load, EarthSatellite, wgs84
from datetime import datetime, timezone, timedelta
import requests
import matplotlib.pyplot as plt


# ============================================================
# YOUR OBSERVER LOCATION
# ============================================================

LATITUDE = 17.78169376635964
LONGITUDE = 83.37745758296342
ELEVATION_M = 0


# ============================================================
# CELESTRAK DATA SOURCE
# ============================================================

CELESTRAK_URL = (
    "https://celestrak.org/NORAD/elements/gp.php"
    "?GROUP=IRIDIUM-NEXT&FORMAT=TLE"
)


# ============================================================
# SATELLITE WE WANT TO TRACK
# ============================================================

TARGET_SATELLITE = "IRIDIUM 154"


# ============================================================
# TRACKING SETTINGS
# ============================================================

TRACK_DURATION_MINUTES = 10
STEP_SECONDS = 10


# ============================================================
# LOAD SKYFIELD
# ============================================================

ts = load.timescale()


# ============================================================
# DOWNLOAD TLE DATA
# ============================================================

print()
print("Downloading current Iridium orbital data from CelesTrak...")
print()

try:

    response = requests.get(
        CELESTRAK_URL,
        timeout=20
    )

    response.raise_for_status()

    tle_data = response.text

except requests.exceptions.RequestException as e:

    print("ERROR downloading CelesTrak data:")
    print(e)

    raise SystemExit


# ============================================================
# PARSE TLE DATA
# ============================================================

lines = [
    line.strip()
    for line in tle_data.splitlines()
    if line.strip()
]

satellites = []

i = 0

while i < len(lines) - 2:

    name = lines[i]
    line1 = lines[i + 1]
    line2 = lines[i + 2]

    if line1.startswith("1 ") and line2.startswith("2 "):

        try:

            satellite = EarthSatellite(
                line1,
                line2,
                name,
                ts
            )

            satellites.append(satellite)

        except Exception as e:

            print(
                f"WARNING: Could not parse {name}: {e}"
            )

        i += 3

    else:

        i += 1


print(
    f"Loaded {len(satellites)} Iridium satellites."
)


# ============================================================
# FIND OUR TARGET SATELLITE
# ============================================================

target = None

for satellite in satellites:

    if satellite.name.strip().upper() == TARGET_SATELLITE.upper():

        target = satellite
        break


if target is None:

    print()
    print(
        f"ERROR: Could not find {TARGET_SATELLITE}"
    )

    print()
    print("Available satellite names:")

    for satellite in satellites:

        print(
            f"  {satellite.name}"
        )

    raise SystemExit


print()
print(
    f"Tracking satellite: {target.name}"
)


# ============================================================
# CREATE OBSERVER
# ============================================================

observer = wgs84.latlon(
    LATITUDE,
    LONGITUDE,
    elevation_m=ELEVATION_M
)


# ============================================================
# START TIME
# ============================================================

start_time = datetime.now(timezone.utc)

print()
print(
    "Tracking period:"
)

print(
    f"Start: {start_time.strftime('%Y-%m-%d %H:%M:%S UTC')}"
)

print(
    f"Duration: {TRACK_DURATION_MINUTES} minutes"
)

print(
    f"Sample interval: {STEP_SECONDS} seconds"
)

print()


# ============================================================
# STORAGE FOR RESULTS
# ============================================================

times = []

azimuths = []

elevations = []

distances = []


# ============================================================
# TRACK SATELLITE
# ============================================================

number_of_samples = int(
    (TRACK_DURATION_MINUTES * 60)
    / STEP_SECONDS
) + 1


for sample_number in range(number_of_samples):

    current_datetime = (
        start_time
        + timedelta(
            seconds=sample_number * STEP_SECONDS
        )
    )

    t = ts.from_datetime(current_datetime)


    # Satellite relative to observer
    difference = target - observer

    topocentric = difference.at(t)


    # Convert to sky coordinates
    altitude, azimuth, distance = (
        topocentric.altaz()
    )


    elevation_deg = altitude.degrees

    azimuth_deg = azimuth.degrees

    distance_km = distance.km


    # Store results
    times.append(current_datetime)

    azimuths.append(azimuth_deg)

    elevations.append(elevation_deg)

    distances.append(distance_km)


    # Print result
    elapsed = sample_number * STEP_SECONDS

    print(
        f"T+{elapsed:03d}s | "
        f"Azimuth: {azimuth_deg:7.2f}° | "
        f"Elevation: {elevation_deg:7.2f}° | "
        f"Distance: {distance_km:8.2f} km"
    )


# ============================================================
# FIND MAXIMUM ELEVATION
# ============================================================

max_index = elevations.index(
    max(elevations)
)

max_elevation = elevations[max_index]

max_time = times[max_index]

max_azimuth = azimuths[max_index]

max_distance = distances[max_index]


print()
print("=" * 70)
print("MAXIMUM ELEVATION DURING TRACK")
print("=" * 70)

print(
    f"Time      : "
    f"{max_time.strftime('%Y-%m-%d %H:%M:%S UTC')}"
)

print(
    f"Azimuth   : {max_azimuth:.2f}°"
)

print(
    f"Elevation : {max_elevation:.2f}°"
)

print(
    f"Distance  : {max_distance:.2f} km"
)


# ============================================================
# PLOT ELEVATION
# ============================================================

elapsed_minutes = [
    i * STEP_SECONDS / 60
    for i in range(len(elevations))
]


plt.figure(figsize=(10, 6))

plt.plot(
    elapsed_minutes,
    elevations,
    marker="o"
)

plt.axhline(
    0,
    linestyle="--"
)

plt.xlabel(
    "Time since start (minutes)"
)

plt.ylabel(
    "Elevation (degrees)"
)

plt.title(
    f"{target.name} Elevation vs Time"
)

plt.grid(True)

plt.tight_layout()

plt.show()


# ============================================================
# PLOT DISTANCE
# ============================================================

plt.figure(figsize=(10, 6))

plt.plot(
    elapsed_minutes,
    distances,
    marker="o"
)

plt.xlabel(
    "Time since start (minutes)"
)

plt.ylabel(
    "Distance from receiver (km)"
)

plt.title(
    f"{target.name} Distance vs Time"
)

plt.grid(True)

plt.tight_layout()

plt.show()


# ============================================================
# DONE
# ============================================================

print()
print("=" * 70)
print("TRACKING COMPLETE")
print("=" * 70)