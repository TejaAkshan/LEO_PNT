from skyfield.api import load, EarthSatellite, wgs84
from datetime import datetime, timezone
import requests


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
# SETTINGS
# ============================================================

# Satellites below this elevation are considered not visible.
ELEVATION_MASK_DEG = 0.0


# ============================================================
# LOAD SKYFIELD TIME SCALE
# ============================================================

ts = load.timescale()


# ============================================================
# DOWNLOAD CURRENT IRIDIUM ORBITAL DATA
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

    print("ERROR: Could not download data from CelesTrak.")
    print()
    print(e)
    raise SystemExit


# ============================================================
# CHECK WHAT CELESTRAK ACTUALLY RETURNED
# ============================================================

if not tle_data.strip():

    print("ERROR: CelesTrak returned an empty response.")
    raise SystemExit


print(f"Received {len(tle_data)} characters from CelesTrak.")
print()


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

    # A valid TLE consists of:
    #
    # Satellite name
    # Line 1 → starts with "1 "
    # Line 2 → starts with "2 "

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

            print(f"WARNING: Could not parse satellite: {name}")
            print(e)

        i += 3

    else:

        i += 1


# ============================================================
# CHECK PARSING RESULT
# ============================================================

print(f"Loaded {len(satellites)} Iridium satellites.")
print()


if len(satellites) == 0:

    print("=" * 70)
    print("ERROR: NO SATELLITES WERE PARSED")
    print("=" * 70)

    print()
    print("The first 20 lines received from CelesTrak were:")
    print("-" * 70)

    for line in lines[:20]:
        print(repr(line))

    print("-" * 70)

    raise SystemExit


# ============================================================
# SHOW FIRST SATELLITE AS A SANITY CHECK
# ============================================================

print("First satellite successfully loaded:")
print(f"Name: {satellites[0].name}")
print()


# ============================================================
# CREATE YOUR OBSERVER LOCATION
# ============================================================

observer = wgs84.latlon(
    LATITUDE,
    LONGITUDE,
    elevation_m=ELEVATION_M
)


# ============================================================
# GET CURRENT UTC TIME
# ============================================================

now = datetime.now(timezone.utc)

t = ts.from_datetime(now)


# ============================================================
# CALCULATE SATELLITE POSITIONS
# ============================================================

results = []


for satellite in satellites:

    try:

        # Difference between satellite and observer
        difference = satellite - observer

        # Satellite position relative to observer
        topocentric = difference.at(t)

        # Convert to altitude, azimuth and distance
        altitude, azimuth, distance = topocentric.altaz()

        elevation_deg = altitude.degrees
        azimuth_deg = azimuth.degrees
        distance_km = distance.km

        results.append(
            {
                "name": satellite.name,
                "elevation": elevation_deg,
                "azimuth": azimuth_deg,
                "distance": distance_km,
                "satellite": satellite,
            }
        )

    except Exception as e:

        print(
            f"WARNING: Could not calculate position for "
            f"{satellite.name}"
        )

        print(e)


# ============================================================
# SORT SATELLITES BY ELEVATION
# ============================================================

results.sort(
    key=lambda x: x["elevation"],
    reverse=True
)


# ============================================================
# DISPLAY SATELLITE STATUS
# ============================================================

print("=" * 80)
print("IRIDIUM SATELLITE STATUS")
print("=" * 80)

print(
    f"UTC time : {now.strftime('%Y-%m-%d %H:%M:%S')}"
)

print(
    f"Latitude : {LATITUDE:.8f}°"
)

print(
    f"Longitude: {LONGITUDE:.8f}°"
)

print()

print(
    f"{'Satellite':30}"
    f"{'Azimuth':>12}"
    f"{'Elevation':>14}"
    f"{'Distance':>14}"
    f"{'Status':>12}"
)

print("-" * 80)


# ============================================================
# DISPLAY ALL SATELLITES
# ============================================================

visible_count = 0


for result in results:

    if result["elevation"] >= ELEVATION_MASK_DEG:

        status = "VISIBLE"

        visible_count += 1

    else:

        status = "BELOW"


    print(
        f"{result['name'][:30]:30}"
        f"{result['azimuth']:11.1f}°"
        f"{result['elevation']:13.1f}°"
        f"{result['distance']:12.1f} km"
        f"{status:>12}"
    )


# ============================================================
# SUMMARY
# ============================================================

print("-" * 80)

print()
print(f"Total satellites processed : {len(results)}")
print(f"Visible satellites         : {visible_count}")
print()


# ============================================================
# TOP 5 SATELLITES
# ============================================================

print("=" * 80)
print("TOP 5 SATELLITES BY ELEVATION")
print("=" * 80)


for number, result in enumerate(results[:5], start=1):

    print()

    print(
        f"{number}. {result['name']}"
    )

    print(
        f"   Azimuth   : {result['azimuth']:.2f}°"
    )

    print(
        f"   Elevation : {result['elevation']:.2f}°"
    )

    print(
        f"   Distance  : {result['distance']:.2f} km"
    )

    if result["elevation"] >= ELEVATION_MASK_DEG:

        print(
            "   Status    : VISIBLE"
        )

    else:

        print(
            "   Status    : BELOW HORIZON"
        )


# ============================================================
# FINISHED
# ============================================================

print()
print("=" * 80)
print("Satellite tracking calculation complete.")
print("=" * 80)