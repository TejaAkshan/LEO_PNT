import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


# ============================================================
# SETTINGS
# ============================================================

CSV_FILE = "iridium_doppler_correction.csv"

OUTPUT_FILE = "iridium_realistic_iq.npy"

SAMPLE_RATE = 100_000       # 100 kHz

NOISE_LEVEL = 0.08

# Keep the simulation manageable
MAX_DURATION_SECONDS = 120


# ============================================================
# LOAD DOPPLER DATA
# ============================================================

print()
print("=" * 75)
print("REALISTIC IRIDIUM IQ SIMULATOR")
print("=" * 75)
print()

print("Loading orbital Doppler data...")

df = pd.read_csv(CSV_FILE)

print(
    f"Loaded {len(df)} orbital samples."
)

print()


# ============================================================
# EXTRACT DATA
# ============================================================

utc_time = pd.to_datetime(
    df["UTC_Time"]
)

doppler = (
    df["Doppler_Hz"]
    .to_numpy(dtype=np.float64)
)


# ============================================================
# CREATE TIME AXIS
# ============================================================

time_original = (
    utc_time - utc_time.iloc[0]
).dt.total_seconds().to_numpy()


# ============================================================
# LIMIT SIMULATION LENGTH
# ============================================================

duration = time_original[-1]

if duration > MAX_DURATION_SECONDS:

    print(
        f"Original pass duration: "
        f"{duration:.1f} seconds"
    )

    print(
        f"Using first "
        f"{MAX_DURATION_SECONDS} seconds."
    )

    duration = MAX_DURATION_SECONDS

else:

    print(
        f"Using full pass: "
        f"{duration:.1f} seconds."
    )


# ============================================================
# NEW HIGH-SPEED TIME AXIS
# ============================================================

num_samples = int(
    duration * SAMPLE_RATE
)

time = (
    np.arange(num_samples)
    / SAMPLE_RATE
)


# ============================================================
# INTERPOLATE REAL DOPPLER CURVE
# ============================================================

doppler_simulated = np.interp(
    time,
    time_original,
    doppler
)


# ============================================================
# GENERATE SIGNAL PHASE
# ============================================================

phase = (
    2
    * np.pi
    * np.cumsum(
        doppler_simulated
    )
    / SAMPLE_RATE
)


# ============================================================
# GENERATE COMPLEX IQ
# ============================================================

signal = np.exp(
    1j * phase
)


# ============================================================
# ADD NOISE
# ============================================================

noise = (
    np.random.normal(
        0,
        NOISE_LEVEL,
        num_samples
    )
    +
    1j
    * np.random.normal(
        0,
        NOISE_LEVEL,
        num_samples
    )
)


iq = (
    signal
    + noise
)


# ============================================================
# SAVE
# ============================================================

np.save(
    OUTPUT_FILE,
    iq.astype(np.complex64)
)


# ============================================================
# INFORMATION
# ============================================================

print()
print("=" * 75)

print(
    f"Sample rate       : "
    f"{SAMPLE_RATE / 1000:.0f} kHz"
)

print(
    f"Duration          : "
    f"{duration:.1f} seconds"
)

print(
    f"Number of samples : "
    f"{num_samples:,}"
)

print(
    f"Initial Doppler   : "
    f"{doppler_simulated[0] / 1000:.3f} kHz"
)

print(
    f"Final Doppler     : "
    f"{doppler_simulated[-1] / 1000:.3f} kHz"
)

print()

print(
    f"Saved IQ file:"
)

print(
    OUTPUT_FILE
)


# ============================================================
# PLOT ACTUAL DOPPLER
# ============================================================

plt.figure(
    figsize=(11, 6)
)

plt.plot(
    time,
    doppler_simulated / 1000
)

plt.axhline(
    0,
    linestyle="--"
)

plt.xlabel(
    "Time (seconds)"
)

plt.ylabel(
    "Doppler (kHz)"
)

plt.title(
    "IRIDIUM — Actual Orbital Doppler Used for IQ Simulation"
)

plt.grid(True)

plt.tight_layout()

plt.show()


print()
print("Simulation complete.")