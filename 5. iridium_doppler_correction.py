from skyfield.api import load, EarthSatellite, wgs84
from datetime import datetime, timezone, timedelta
import requests
import math
import csv
import matplotlib.pyplot as plt


# ============================================================
# USER LOCATION
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
# RECEIVER / SIGNAL SETTINGS
# ============================================================

# Temporary nominal frequency supplied by Aryan
REFERENCE_FREQUENCY_HZ = 1.621e9

# Speed of light
SPEED_OF_LIGHT_MPS = 299792458.0

# Only consider passes above this elevation
ELEVATION_MASK_DEG = 10.0

# Search this far into the future
SEARCH_HOURS = 3

# Calculate every second
STEP_SECONDS = 1


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

except Exception as e:

    print("ERROR downloading CelesTrak data:")
    print(e)
    raise SystemExit


# ============================================================
# PARSE TLE
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

        except Exception:

            pass

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
# TIME WINDOW
# ============================================================

start_datetime = datetime.now(timezone.utc)

end_datetime = (
    start_datetime
    + timedelta(hours=SEARCH_HOURS)
)

t0 = ts.from_datetime(start_datetime)
t1 = ts.from_datetime(end_datetime)


# ============================================================
# FIND PASSES
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

                # Determine maximum elevation

                t_max = ts.from_datetime(
                    max_time
                )

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
                        "max_elevation":
                            altitude.degrees
                    }
                )


            rise_time = None
            max_time = None


# ============================================================
# CHECK PASSES
# ============================================================

if not passes:

    print()
    print("No suitable Iridium passes found.")
    raise SystemExit


# ============================================================
# SELECT BEST PASS
# ============================================================

passes.sort(
    key=lambda x: x["max_elevation"],
    reverse=True
)

selected = passes[0]

satellite = selected["satellite"]


print()
print("=" * 80)
print("DOPPLER CORRECTION EXPERIMENT")
print("=" * 80)

print()

print(
    f"Satellite        : {selected['name']}"
)

print(
    f"Rise             : "
    f"{selected['rise'].strftime('%Y-%m-%d %H:%M:%S UTC')}"
)

print(
    f"Maximum          : "
    f"{selected['max'].strftime('%Y-%m-%d %H:%M:%S UTC')}"
)

print(
    f"Set              : "
    f"{selected['set'].strftime('%Y-%m-%d %H:%M:%S UTC')}"
)

print(
    f"Maximum elevation: "
    f"{selected['max_elevation']:.2f}°"
)

print(
    f"Reference carrier: "
    f"{REFERENCE_FREQUENCY_HZ / 1e9:.9f} GHz"
)

print()


# ============================================================
# TRACK PASS
# ============================================================

rise = selected["rise"]
set_time = selected["set"]

duration_seconds = int(
    (set_time - rise).total_seconds()
)


results = []


print("=" * 80)
print("PREDICTED FREQUENCY CORRECTION")
print("=" * 80)

print()

print(
    f"{'Time':10}"
    f"{'Elev':>9}"
    f"{'Range':>12}"
    f"{'Range Rate':>14}"
    f"{'Doppler':>14}"
    f"{'Received':>19}"
)

print("-" * 80)


for seconds in range(
    0,
    duration_seconds + 1,
    STEP_SECONDS
):

    current_time = (
        rise
        + timedelta(seconds=seconds)
    )

    t = ts.from_datetime(
        current_time
    )


    # --------------------------------------------------------
    # Satellite relative to receiver
    # --------------------------------------------------------

    difference = satellite - observer

    topocentric = difference.at(t)


    # --------------------------------------------------------
    # POSITION
    # --------------------------------------------------------

    position_km = topocentric.position.km


    # --------------------------------------------------------
    # VELOCITY
    # --------------------------------------------------------

    velocity_km_s = (
        topocentric.velocity.km_per_s
    )


    # --------------------------------------------------------
    # DISTANCE
    # --------------------------------------------------------

    distance_km = math.sqrt(
        sum(
            x * x
            for x in position_km
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


    range_rate_m_s = (
        range_rate_km_s * 1000
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
        -(
            range_rate_m_s
        )
        / SPEED_OF_LIGHT_MPS
        * REFERENCE_FREQUENCY_HZ
    )


    # --------------------------------------------------------
    # EXPECTED RECEIVED FREQUENCY
    # --------------------------------------------------------

    received_frequency_hz = (
        REFERENCE_FREQUENCY_HZ
        + doppler_hz
    )


    # --------------------------------------------------------
    # REQUIRED RECEIVER CORRECTION
    # --------------------------------------------------------

    frequency_correction_hz = doppler_hz


    # --------------------------------------------------------
    # STORE
    # --------------------------------------------------------

    results.append(
        {
            "time": current_time,
            "elevation": elevation_deg,
            "distance": distance_km,
            "range_rate": range_rate_m_s,
            "doppler": doppler_hz,
            "received_frequency":
                received_frequency_hz,
            "correction":
                frequency_correction_hz
        }
    )


    # --------------------------------------------------------
    # DISPLAY
    # --------------------------------------------------------

    print(
        f"{current_time.strftime('%H:%M:%S'):10}"
        f"{elevation_deg:8.2f}°"
        f"{distance_km:11.1f} km"
        f"{range_rate_m_s:12.1f} m/s"
        f"{doppler_hz / 1000:11.2f} kHz"
        f"{received_frequency_hz / 1e9:18.9f} GHz"
    )


# ============================================================
# SAVE CSV
# ============================================================

filename = "iridium_doppler_correction.csv"


with open(
    filename,
    "w",
    newline=""
) as file:

    writer = csv.writer(file)

    writer.writerow(
        [
            "UTC_Time",
            "Elevation_deg",
            "Distance_km",
            "Range_Rate_mps",
            "Doppler_Hz",
            "Received_Frequency_Hz",
            "Frequency_Correction_Hz"
        ]
    )


    for result in results:

        writer.writerow(
            [
                result["time"].isoformat(),
                result["elevation"],
                result["distance"],
                result["range_rate"],
                result["doppler"],
                result["received_frequency"],
                result["correction"]
            ]
        )


print()
print(
    f"Saved data to: {filename}"
)


# ============================================================
# DOPPLER PLOT
# ============================================================

time_minutes = [
    (
        r["time"] - rise
    ).total_seconds() / 60
    for r in results
]


doppler_khz = [
    r["doppler"] / 1000
    for r in results
]


plt.figure(figsize=(11, 6))

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
    f"{satellite.name} — Predicted Doppler"
)

plt.grid(True)

plt.tight_layout()

plt.show()


# ============================================================
# RECEIVED FREQUENCY PLOT
# ============================================================

received_ghz = [
    r["received_frequency"] / 1e9
    for r in results
]


plt.figure(figsize=(11, 6))

plt.plot(
    time_minutes,
    received_ghz
)

plt.axhline(
    REFERENCE_FREQUENCY_HZ / 1e9,
    linestyle="--"
)

plt.xlabel(
    "Time since satellite rise (minutes)"
)

plt.ylabel(
    "Received frequency (GHz)"
)

plt.title(
    f"{satellite.name} — Predicted Received Frequency"
)

plt.grid(True)

plt.tight_layout()

plt.show()


# ============================================================
# SUMMARY
# ============================================================

maximum_doppler = max(
    results,
    key=lambda r: abs(r["doppler"])
)


closest = min(
    results,
    key=lambda r: r["distance"]
)


print()
print("=" * 80)
print("SUMMARY")
print("=" * 80)

print()

print(
    f"Satellite: {satellite.name}"
)

print()

print(
    f"Closest approach: "
    f"{closest['distance']:.2f} km"
)

print(
    f"Time: "
    f"{closest['time'].strftime('%H:%M:%S UTC')}"
)

print()

print(
    f"Maximum absolute Doppler: "
    f"{maximum_doppler['doppler'] / 1000:.2f} kHz"
)

print(
    f"Time: "
    f"{maximum_doppler['time'].strftime('%H:%M:%S UTC')}"
)

print()

print("=" * 80)
print("DOPPLER CORRECTION MODEL COMPLETE")
print("=" * 80)