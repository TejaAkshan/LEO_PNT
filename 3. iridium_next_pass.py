from skyfield.api import load, EarthSatellite, wgs84
from datetime import datetime, timezone, timedelta
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

# Practical minimum elevation.
#
# 0 degrees  = geometric horizon
# 10 degrees = our current practical threshold

ELEVATION_MASK_DEG = 10.0


# How far into the future should we search?
SEARCH_HOURS = 3


# ============================================================
# LOAD SKYFIELD TIME SCALE
# ============================================================

ts = load.timescale()


# ============================================================
# DOWNLOAD CURRENT TLE DATA
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

print()


# ============================================================
# CREATE OBSERVER
# ============================================================

observer = wgs84.latlon(
    LATITUDE,
    LONGITUDE,
    elevation_m=ELEVATION_M
)


# ============================================================
# DEFINE SEARCH WINDOW
# ============================================================

start_datetime = datetime.now(timezone.utc)

end_datetime = (
    start_datetime
    + timedelta(hours=SEARCH_HOURS)
)

t0 = ts.from_datetime(start_datetime)
t1 = ts.from_datetime(end_datetime)


print("=" * 90)
print("IRIDIUM NEXT-PASS PREDICTOR")
print("=" * 90)

print(
    f"Observer latitude : {LATITUDE:.8f}°"
)

print(
    f"Observer longitude: {LONGITUDE:.8f}°"
)

print()

print(
    f"Search start: "
    f"{start_datetime.strftime('%Y-%m-%d %H:%M:%S UTC')}"
)

print(
    f"Search end  : "
    f"{end_datetime.strftime('%Y-%m-%d %H:%M:%S UTC')}"
)

print()

print(
    f"Elevation mask: {ELEVATION_MASK_DEG:.1f}°"
)

print()


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

    except Exception as e:

        print(
            f"WARNING: Could not calculate pass for "
            f"{satellite.name}: {e}"
        )

        continue


    # --------------------------------------------------------
    # Events:
    #
    # 0 = satellite rises above elevation mask
    # 1 = satellite reaches maximum elevation
    # 2 = satellite sets below elevation mask
    # --------------------------------------------------------

    current_rise = None
    current_max = None
    current_set = None


    for time, event in zip(times, events):

        if event == 0:

            current_rise = time.utc_datetime()

        elif event == 1:

            current_max = time.utc_datetime()

        elif event == 2:

            current_set = time.utc_datetime()


            # A complete pass
            if (
                current_rise is not None
                and current_max is not None
                and current_set is not None
            ):

                # Calculate maximum elevation
                t_max = ts.from_datetime(
                    current_max
                )

                difference = satellite - observer

                topocentric = difference.at(t_max)

                altitude, azimuth, distance = (
                    topocentric.altaz()
                )

                passes.append(
                    {
                        "name": satellite.name,
                        "rise": current_rise,
                        "max": current_max,
                        "set": current_set,
                        "max_elevation": altitude.degrees,
                        "max_azimuth": azimuth.degrees,
                        "max_distance": distance.km,
                    }
                )


            current_rise = None
            current_max = None
            current_set = None


# ============================================================
# SORT PASSES BY RISE TIME
# ============================================================

passes.sort(
    key=lambda x: x["rise"]
)


# ============================================================
# DISPLAY UPCOMING PASSES
# ============================================================

print("=" * 90)
print("UPCOMING IRIDIUM PASSES")
print("=" * 90)

print()


if len(passes) == 0:

    print(
        "No complete passes found within the search window."
    )

else:

    for number, current_pass in enumerate(
        passes,
        start=1
    ):

        print(
            f"{number}. "
            f"{current_pass['name']}"
        )

        print(
            f"   Rise : "
            f"{current_pass['rise'].strftime('%H:%M:%S UTC')}"
        )

        print(
            f"   Max  : "
            f"{current_pass['max'].strftime('%H:%M:%S UTC')}"
        )

        print(
            f"   Set  : "
            f"{current_pass['set'].strftime('%H:%M:%S UTC')}"
        )

        print(
            f"   Maximum elevation: "
            f"{current_pass['max_elevation']:.2f}°"
        )

        print(
            f"   Azimuth at maximum: "
            f"{current_pass['max_azimuth']:.2f}°"
        )

        print(
            f"   Distance at maximum: "
            f"{current_pass['max_distance']:.2f} km"
        )

        print()


# ============================================================
# RANK THE BEST PASSES
# ============================================================

passes_by_elevation = sorted(
    passes,
    key=lambda x: x["max_elevation"],
    reverse=True
)


print("=" * 90)
print("BEST UPCOMING PASSES")
print("=" * 90)

print()


for number, current_pass in enumerate(
    passes_by_elevation[:10],
    start=1
):

    print(
        f"{number}. {current_pass['name']}"
    )

    print(
        f"   Maximum elevation : "
        f"{current_pass['max_elevation']:.2f}°"
    )

    print(
        f"   Rise              : "
        f"{current_pass['rise'].strftime('%H:%M:%S UTC')}"
    )

    print(
        f"   Maximum           : "
        f"{current_pass['max'].strftime('%H:%M:%S UTC')}"
    )

    print(
        f"   Set               : "
        f"{current_pass['set'].strftime('%H:%M:%S UTC')}"
    )

    print()


# ============================================================
# BEST SATELLITE
# ============================================================

if len(passes_by_elevation) > 0:

    best = passes_by_elevation[0]

    print("=" * 90)
    print("RECOMMENDED SATELLITE")
    print("=" * 90)

    print()

    print(
        f"Satellite: {best['name']}"
    )

    print(
        f"Rise: "
        f"{best['rise'].strftime('%Y-%m-%d %H:%M:%S UTC')}"
    )

    print(
        f"Maximum elevation: "
        f"{best['max_elevation']:.2f}°"
    )

    print(
        f"Maximum elevation time: "
        f"{best['max'].strftime('%Y-%m-%d %H:%M:%S UTC')}"
    )

    print(
        f"Set: "
        f"{best['set'].strftime('%Y-%m-%d %H:%M:%S UTC')}"
    )

    print(
        f"Azimuth at maximum: "
        f"{best['max_azimuth']:.2f}°"
    )

    print(
        f"Distance at maximum: "
        f"{best['max_distance']:.2f} km"
    )


print()
print("=" * 90)
print("PASS PREDICTION COMPLETE")
print("=" * 90)