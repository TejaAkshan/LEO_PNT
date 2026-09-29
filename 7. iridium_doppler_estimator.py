import numpy as np
import matplotlib.pyplot as plt


# ============================================================
# SETTINGS
# ============================================================

IQ_FILE = "iridium_simulated_iq.npy"

SAMPLE_RATE = 200_000       # 200 kHz

FFT_SIZE = 262_144

WINDOW_DURATION = 0.1       # 100 ms

STEP_DURATION = 0.1


# ============================================================
# LOAD IQ DATA
# ============================================================

print()
print("=" * 70)
print("IRIDIUM DOPPLER ESTIMATOR")
print("=" * 70)

print()

print("Loading IQ data...")

iq = np.load(IQ_FILE)

print(
    f"Loaded {len(iq):,} IQ samples"
)

print()


# ============================================================
# CALCULATE WINDOW PARAMETERS
# ============================================================

window_size = int(
    SAMPLE_RATE * WINDOW_DURATION
)

step_size = int(
    SAMPLE_RATE * STEP_DURATION
)


print(
    f"Sample rate   : "
    f"{SAMPLE_RATE / 1000:.0f} kHz"
)

print(
    f"FFT size      : "
    f"{FFT_SIZE:,}"
)

print(
    f"Window        : "
    f"{WINDOW_DURATION * 1000:.0f} ms"
)

print()


# ============================================================
# ESTIMATE FREQUENCY
# ============================================================

estimated_times = []
estimated_doppler = []


for start in range(
    0,
    len(iq) - window_size,
    step_size
):

    # --------------------------------------------------------
    # Extract window
    # --------------------------------------------------------

    samples = iq[
        start:
        start + window_size
    ]


    # --------------------------------------------------------
    # Apply Hann window
    # --------------------------------------------------------

    window = np.hanning(
        len(samples)
    )

    samples = samples * window


    # --------------------------------------------------------
    # FFT
    # --------------------------------------------------------

    spectrum = np.fft.fft(
        samples,
        n=FFT_SIZE
    )

    frequencies = np.fft.fftfreq(
        FFT_SIZE,
        d=1 / SAMPLE_RATE
    )


    # --------------------------------------------------------
    # Shift zero frequency to center
    # --------------------------------------------------------

    spectrum = np.fft.fftshift(
        spectrum
    )

    frequencies = np.fft.fftshift(
        frequencies
    )


    # --------------------------------------------------------
    # Find strongest frequency
    # --------------------------------------------------------

    magnitude = np.abs(
        spectrum
    )

    peak_index = np.argmax(
        magnitude
    )

    peak_frequency = frequencies[
        peak_index
    ]


    # --------------------------------------------------------
    # Store result
    # --------------------------------------------------------

    center_time = (
        start
        + window_size / 2
    ) / SAMPLE_RATE

    estimated_times.append(
        center_time
    )

    estimated_doppler.append(
        peak_frequency
    )


# ============================================================
# CONVERT TO NUMPY ARRAYS
# ============================================================

estimated_times = np.array(
    estimated_times
)

estimated_doppler = np.array(
    estimated_doppler
)


# ============================================================
# PRINT RESULTS
# ============================================================

print(
    f"Frequency estimates: "
    f"{len(estimated_doppler)}"
)

print()

print("=" * 70)
print("SAMPLE FREQUENCY ESTIMATES")
print("=" * 70)

print()


for i in range(
    0,
    len(estimated_doppler),
    max(1, len(estimated_doppler) // 10)
):

    print(
        f"T+{estimated_times[i]:6.1f} s"
        f" | Doppler: "
        f"{estimated_doppler[i] / 1000:8.3f} kHz"
    )


# ============================================================
# PLOT ESTIMATED DOPPLER
# ============================================================

plt.figure(
    figsize=(11, 6)
)

plt.plot(
    estimated_times,
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
    "IRIDIUM Doppler Estimated from IQ"
)

plt.grid(True)

plt.tight_layout()

plt.show()