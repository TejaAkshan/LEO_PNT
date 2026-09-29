import numpy as np
import matplotlib.pyplot as plt
import csv


# ============================================================
# SETTINGS
# ============================================================

SAMPLE_RATE = 200_000       # 200 kHz
DURATION = 120              # seconds

REFERENCE_FREQUENCY = 1.621e9

# Doppler range based on our IRIDIUM 142 model
START_DOPPLER = 35_320
END_DOPPLER = -35_330

SIGNAL_AMPLITUDE = 1.0

NOISE_LEVEL = 0.05


# ============================================================
# TIME AXIS
# ============================================================

num_samples = int(
    SAMPLE_RATE * DURATION
)

time = np.arange(
    num_samples
) / SAMPLE_RATE


# ============================================================
# CREATE A SMOOTH DOPPLER CURVE
# ============================================================

doppler = np.linspace(
    START_DOPPLER,
    END_DOPPLER,
    num_samples
)


# ============================================================
# INSTANTANEOUS FREQUENCY
# ============================================================

instantaneous_frequency = doppler


# ============================================================
# CREATE PHASE
# ============================================================

phase = (
    2
    * np.pi
    * np.cumsum(
        instantaneous_frequency
    ) / SAMPLE_RATE
)


# ============================================================
# CREATE COMPLEX IQ SIGNAL
# ============================================================

signal = (
    SIGNAL_AMPLITUDE
    * np.exp(
        1j * phase
    )
)


# ============================================================
# ADD COMPLEX GAUSSIAN NOISE
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


iq_signal = signal + noise


# ============================================================
# SAVE IQ DATA
# ============================================================

np.save(
    "iridium_simulated_iq.npy",
    iq_signal
)


print()
print("=" * 70)
print("SIMULATED IRIDIUM IQ SIGNAL")
print("=" * 70)

print()

print(
    f"Sample rate : "
    f"{SAMPLE_RATE / 1000:.0f} kHz"
)

print(
    f"Duration    : "
    f"{DURATION} seconds"
)

print(
    f"Samples     : "
    f"{num_samples:,}"
)

print()

print(
    f"Initial Doppler : "
    f"{START_DOPPLER / 1000:.2f} kHz"
)

print(
    f"Final Doppler   : "
    f"{END_DOPPLER / 1000:.2f} kHz"
)

print()

print(
    "Saved:"
)

print(
    "iridium_simulated_iq.npy"
)


# ============================================================
# PLOT DOPPLER
# ============================================================

plt.figure(figsize=(11, 6))

plt.plot(
    time,
    doppler / 1000
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
    "Simulated IRIDIUM Doppler"
)

plt.grid(True)

plt.tight_layout()

plt.show()


# ============================================================
# PLOT IQ REAL PART
# ============================================================

display_duration = 0.01

display_samples = int(
    SAMPLE_RATE
    * display_duration
)

plt.figure(figsize=(11, 6))

plt.plot(
    time[:display_samples],
    iq_signal.real[:display_samples]
)

plt.xlabel(
    "Time (seconds)"
)

plt.ylabel(
    "Amplitude"
)

plt.title(
    "Simulated IQ Signal — Real Component"
)

plt.grid(True)

plt.tight_layout()

plt.show()


# ============================================================
# PLOT IQ MAGNITUDE
# ============================================================

plt.figure(figsize=(11, 6))

plt.plot(
    time[:display_samples],
    np.abs(
        iq_signal[:display_samples]
    )
)

plt.xlabel(
    "Time (seconds)"
)

plt.ylabel(
    "Magnitude"
)

plt.title(
    "Simulated IQ Signal — Magnitude"
)

plt.grid(True)

plt.tight_layout()

plt.show()