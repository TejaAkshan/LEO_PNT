import numpy as np
import matplotlib.pyplot as plt


# ============================================================
# SETTINGS
# ============================================================

IQ_FILE = "iridium_realistic_iq.npy"

SAMPLE_RATE = 100_000

FFT_SIZE = 65_536

WINDOW_SIZE = 20_000

STEP_SIZE = 20_000


# ============================================================
# LOAD IQ
# ============================================================

print()
print("=" * 75)
print("IRIDIUM SOFTWARE RECEIVER")
print("=" * 75)
print()

print("Loading IQ data...")

iq = np.load(
    IQ_FILE
)

print(
    f"Loaded {len(iq):,} samples."
)

print()


# ============================================================
# FREQUENCY ESTIMATION
# ============================================================

estimated_time = []

estimated_doppler = []


for start in range(
    0,
    len(iq) - WINDOW_SIZE,
    STEP_SIZE
):

    samples = iq[
        start:
        start + WINDOW_SIZE
    ]


    # Window
    samples = (
        samples
        * np.hanning(
            len(samples)
        )
    )


    # FFT
    spectrum = np.fft.fft(
        samples,
        n=FFT_SIZE
    )


    frequencies = np.fft.fftfreq(
        FFT_SIZE,
        1 / SAMPLE_RATE
    )


    # Shift
    spectrum = np.fft.fftshift(
        spectrum
    )

    frequencies = np.fft.fftshift(
        frequencies
    )


    # Magnitude
    magnitude = np.abs(
        spectrum
    )


    # Peak
    peak = np.argmax(
        magnitude
    )


    frequency = frequencies[
        peak
    ]


    # Time
    center_time = (
        start
        + WINDOW_SIZE / 2
    ) / SAMPLE_RATE


    estimated_time.append(
        center_time
    )

    estimated_doppler.append(
        frequency
    )


estimated_time = np.array(
    estimated_time
)

estimated_doppler = np.array(
    estimated_doppler
)


# ============================================================
# PRINT
# ============================================================

print()
print("=" * 75)
print("DOPPLER ESTIMATES")
print("=" * 75)
print()


for i in np.linspace(
    0,
    len(estimated_doppler) - 1,
    10,
    dtype=int
):

    print(
        f"T+{estimated_time[i]:7.2f} s"
        f" | Estimated Doppler:"
        f" {estimated_doppler[i] / 1000:9.3f} kHz"
    )


# ============================================================
# PLOT
# ============================================================

plt.figure(
    figsize=(11, 6)
)

plt.plot(
    estimated_time,
    estimated_doppler / 1000
)

plt.axhline(
    0,
    linestyle="--"
)

plt.xlabel(
    "Time (seconds)"
)

plt.ylabel(
    "Estimated Doppler (kHz)"
)

plt.title(
    "IRIDIUM Doppler Recovered from Simulated IQ"
)

plt.grid(True)

plt.tight_layout()

plt.show()


print()
print("Receiver processing complete.")