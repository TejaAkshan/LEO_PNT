from skyfield.api import load, EarthSatellite, wgs84
from datetime import datetime, timezone, timedelta
import requests
import math
import csv
import matplotlib.pyplot as plt


# ============================================================
# YOUR LOCATION
# ============================================================

LATITUDE = 17.78169376635964
LONGITUDE = 83.37745758296342
ELEVATION_M = 0


# ============================================================
# CELESTRAK
# ============================================================

CELESTRAK_URL = (
    "https://celestrak.org/NORAD/elements/gp.php"
    "?GROUP=IRIDIUM-NEXT&FORMAT=TLE"
)


# ============================================================
# SETTINGS
# ============================================================

ELEVATION_MASK_DEG = 10.0

SEARCH_HOURS = 3

# How frequently we calculate the Doppler
STEP_SECONDS = 1

# Temporary reference frequency supplied by Aryan
REFERENCE_FREQUENCY_HZ = 1.621e9

# Speed of light
SPEED_OF_LIGHT_MPS = 299792458.0


# ============================================================
# SKYFIELD
# ============================================================

ts = load.timescale()


# ============================================================
# DOWNLOAD TLE DATA
# ============================================================

print()
print("Downloading current Iridium orbital data...")
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
# OBSERVER
# ============================================================

observer = wgs84.latlon(
    LATITUDE,
    LONGITUDE,
    elevation_m=ELEVATION_M
)


# ============================================================
# SEARCH WINDOW
# ============================================================

start_datetime = datetime.now(timezone.utc)

end_datetime = (
    start_datetime
    + timedelta(hours=SEARCH_HOURS)
)

t0 = ts.from_datetime(start_datetime)
t1 = ts.from_datetime(end_datetime)


# ============================================================
# FIND ALL UPCOMING PASSES
# ============================================================

passes = []


for satellite in satellites:

    try:

        times, events = satellite.find_events(
            observer,
            t0,
            t1,
            altitude_degrees=ELEVATION_MASK_DEG
        )

    except Exception:

        continue


    rise_time = None
    max_time = None

    for time, event in zip(times, events):

        if event == 0:

            rise_time = time.utc_datetime()

        elif event == 1:

            max_time = time.utc_datetime()

        elif event == 2:

            set_time = time.utc_datetime()

            if (
                rise_time is not None
                and max_time is not None
            ):

                # Calculate maximum elevation

                t_max = ts.from_datetime(max_time)

                difference = satellite - observer

                topocentric = difference.at(t_max)

                altitude, azimuth, distance = (
                    topocentric.altaz()
                )

                passes.append(
                    {
                        "satellite": satellite,
                        "name": satellite.name,
                        "rise": rise_time,
                        "max": max_time,
                        "set": set_time,
                        "max_elevation": altitude.degrees
                    }
                )

            rise_time = None
            max_time = None


# ============================================================
# CHECK FOR PASSES
# ============================================================

if not passes:

    print()
    print("No complete passes found.")
    raise SystemExit


# ============================================================
# CHOOSE BEST UPCOMING PASS
# ============================================================

passes.sort(
    key=lambda x: x["max_elevation"],
    reverse=True
)

selected_pass = passes[0]

satellite = selected_pass["satellite"]


print()
print("=" * 75)
print("SELECTED DOPPLER EXPERIMENT")
print("=" * 75)

print()
print(
    f"Satellite : {selected_pass['name']}"
)

print(
    f"Rise      : "
    f"{selected_pass['rise'].strftime('%Y-%m-%d %H:%M:%S UTC')}"
)

print(
    f"Maximum   : "
    f"{selected_pass['max'].strftime('%Y-%m-%d %H:%M:%S UTC')}"
)

print(
    f"Set       : "
    f"{selected_pass['set'].strftime('%Y-%m-%d %H:%M:%S UTC')}"
)

print(
    f"Peak elevation: "
    f"{selected_pass['max_elevation']:.2f}°"
)

print(
    f"Reference frequency: "
    f"{REFERENCE_FREQUENCY_HZ / 1e9:.6f} GHz"
)

print()


# ============================================================
# TRACK ENTIRE PASS
# ============================================================

rise = selected_pass["rise"]
set_time = selected_pass["set"]

duration_seconds = int(
    (set_time - rise).total_seconds()
)


results = []


print("=" * 75)
print("DOPPLER CALCULATION")
print("=" * 75)

print()

print(
    f"{'Time':12}"
    f"{'Elevation':>12}"
    f"{'Distance':>14}"
    f"{'Range Rate':>16}"
    f"{'Doppler':>16}"
    f"{'Received':>18}"
)

print("-" * 88)


for seconds in range(
    0,
    duration_seconds + 1,
    STEP_SECONDS
):

    current_datetime = (
        rise
        + timedelta(seconds=seconds)
    )

    t = ts.from_datetime(
        current_datetime
    )


    # --------------------------------------------------------
    # Satellite relative to receiver
    # --------------------------------------------------------

    difference = satellite - observer

    topocentric = difference.at(t)


    # --------------------------------------------------------
    # Position vector
    # --------------------------------------------------------

    position_km = topocentric.position.km


    # --------------------------------------------------------
    # Relative velocity vector
    # --------------------------------------------------------

    velocity_km_s = topocentric.velocity.km_per_s


    # --------------------------------------------------------
    # Distance
    # --------------------------------------------------------

    distance_km = math.sqrt(
        sum(
            component ** 2
            for component in position_km
        )
    )


    # --------------------------------------------------------
    # RANGE RATE
    # --------------------------------------------------------

    range_rate_km_s = (
        sum(
            position_km[j]
            * velocity_km_s[j]
            for j in range(3)
        )
        / distance_km
    )


    # Convert km/s → m/s

    range_rate_m_s = (
        range_rate_km_s * 1000.0
    )


    # --------------------------------------------------------
    # ELEVATION
    # --------------------------------------------------------

    altitude, azimuth, distance = (
        topocentric.altaz()
    )

    elevation_deg = altitude.degrees


    # --------------------------------------------------------
    # DOPPLER
    # --------------------------------------------------------

    doppler_hz = (
        -range_rate_m_s
        / SPEED_OF_LIGHT_MPS
        * REFERENCE_FREQUENCY_HZ
    )


    # --------------------------------------------------------
    # RECEIVED FREQUENCY
    # --------------------------------------------------------

    received_frequency_hz = (
        REFERENCE_FREQUENCY_HZ
        + doppler_hz
    )


    # --------------------------------------------------------
    # STORE
    # --------------------------------------------------------

    results.append(
        {
            "time": current_datetime,
            "elevation": elevation_deg,
            "distance_km": distance_km,
            "range_rate_m_s": range_rate_m_s,
            "doppler_hz": doppler_hz,
            "received_frequency_hz":
                received_frequency_hz
        }
    )


    # --------------------------------------------------------
    # DISPLAY
    # --------------------------------------------------------

    print(
        f"{current_datetime.strftime('%H:%M:%S'):12}"
        f"{elevation_deg:11.2f}°"
        f"{distance_km:13.2f} km"
        f"{range_rate_m_s:14.2f} m/s"
        f"{doppler_hz / 1000:14.2f} kHz"
        f"{received_frequency_hz / 1e9:16.9f} GHz"
    )


# ============================================================
# FIND IMPORTANT VALUES
# ============================================================

maximum_elevation_result = max(
    results,
    key=lambda x: x["elevation"]
)


maximum_doppler_result = max(
    results,
    key=lambda x: abs(x["doppler_hz"])
)


closest_result = min(
    results,
    key=lambda x: x["distance_km"]
)


# ============================================================
# SUMMARY
# ============================================================

print()
print("=" * 75)
print("DOPPLER EXPERIMENT SUMMARY")
print("=" * 75)

print()

print(
    f"Satellite: {satellite.name}"
)

print()

print(
    "Maximum elevation:"
)

print(
    f"  {maximum_elevation_result['elevation']:.2f}°"
)

print(
    f"  Time: "
    f"{maximum_elevation_result['time'].strftime('%H:%M:%S UTC')}"
)

print()

print(
    "Closest approach:"
)

print(
    f"  Distance: "
    f"{closest_result['distance_km']:.2f} km"
)

print(
    f"  Range rate: "
    f"{closest_result['range_rate_m_s']:.2f} m/s"
)

print(
    f"  Time: "
    f"{closest_result['time'].strftime('%H:%M:%S UTC')}"
)

print()

print(
    "Maximum absolute Doppler:"
)

print(
    f"  {maximum_doppler_result['doppler_hz'] / 1000:.2f} kHz"
)

print(
    f"  Time: "
    f"{maximum_doppler_result['time'].strftime('%H:%M:%S UTC')}"
)

print()

# ============================================================
# SAVE CSV
# ============================================================

csv_filename = "iridium_doppler_results.csv"


with open(
    csv_filename,
    "w",
    newline=""
) as file:

    writer = csv.writer(file)

    writer.writerow(
        [
            "UTC Time",
            "Elevation_deg",
            "Distance_km",
            "Range_Rate_mps",
            "Doppler_Hz",
            "Received_Frequency_Hz"
        ]
    )

    for result in results:

        writer.writerow(
            [
                result["time"].isoformat(),
                result["elevation"],
                result["distance_km"],
                result["range_rate_m_s"],
                result["doppler_hz"],
                result["received_frequency_hz"]
            ]
        )


print(
    f"Saved results to: {csv_filename}"
)


# ============================================================
# PLOT 1 — DOPPLER
# ============================================================

time_minutes = [
    (
        result["time"] - rise
    ).total_seconds() / 60
    for result in results
]


doppler_khz = [
    result["doppler_hz"] / 1000
    for result in results
]


plt.figure(figsize=(10, 6))

plt.plot(
    time_minutes,
    doppler_khz
)

plt.axhline(
    0,
    linestyle="--"
)

plt.xlabel(
    "Time since satellite rise (minutes)"
)

plt.ylabel(
    "Doppler shift (kHz)"
)

plt.title(
    f"{satellite.name} Predicted Doppler"
)

plt.grid(True)

plt.tight_layout()

plt.show()


# ============================================================
# PLOT 2 — RANGE RATE
# ============================================================

range_rates = [
    result["range_rate_m_s"]
    for result in results
]


plt.figure(figsize=(10, 6))

plt.plot(
    time_minutes,
    range_rates
)

plt.axhline(
    0,
    linestyle="--"
)

plt.xlabel(
    "Time since satellite rise (minutes)"
)

plt.ylabel(
    "Range rate (m/s)"
)

plt.title(
    f"{satellite.name} Range Rate"
)

plt.grid(True)

plt.tight_layout()

plt.show()


# ============================================================
# PLOT 3 — ELEVATION
# ============================================================

elevations = [
    result["elevation"]
    for result in results
]


plt.figure(figsize=(10, 6))

plt.plot(
    time_minutes,
    elevations
)

plt.xlabel(
    "Time since satellite rise (minutes)"
)

plt.ylabel(
    "Elevation (degrees)"
)

plt.title(
    f"{satellite.name} Elevation"
)

plt.grid(True)

plt.tight_layout()

plt.show()


print()
print("=" * 75)
print("DOPPLER CALCULATION COMPLETE")
print("=" * 75)