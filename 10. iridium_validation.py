import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


# ============================================================
# FILES
# ============================================================

CSV_FILE = "iridium_doppler_correction.csv"

IQ_FILE = "iridium_realistic_iq.npy"


# ============================================================
# SETTINGS
# ============================================================

SAMPLE_RATE = 100_000

FFT_SIZE = 65_536

WINDOW_SIZE = 20_000

STEP_SIZE = 20_000


# ============================================================
# LOAD GROUND TRUTH
# ============================================================

df = pd.read_csv(
    CSV_FILE
)

utc = pd.to_datetime(
    df["UTC_Time"]
)

truth_time = (
    utc - utc.iloc[0]
).dt.total_seconds().to_numpy()

truth_doppler = (
    df["Doppler_Hz"]
    .to_numpy()
)


# ============================================================
# LIMIT TO IQ DURATION
# ============================================================

iq = np.load(
    IQ_FILE
)

duration = (
    len(iq)
    / SAMPLE_RATE
)


# ============================================================
# ESTIMATE FROM IQ
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

    samples *= np.hanning(
        len(samples)
    )


    spectrum = np.fft.fft(
        samples,
        n=FFT_SIZE
    )

    frequencies = np.fft.fftfreq(
        FFT_SIZE,
        1 / SAMPLE_RATE
    )


    spectrum = np.fft.fftshift(
        spectrum
    )

    frequencies = np.fft.fftshift(
        frequencies
    )


    peak = np.argmax(
        np.abs(spectrum)
    )


    estimated_doppler.append(
        frequencies[peak]
    )


    estimated_time.append(
        (
            start
            + WINDOW_SIZE / 2
        )
        / SAMPLE_RATE
    )


estimated_time = np.array(
    estimated_time
)

estimated_doppler = np.array(
    estimated_doppler
)


# ============================================================
# INTERPOLATE GROUND TRUTH
# ============================================================

truth_interpolated = np.interp(
    estimated_time,
    truth_time,
    truth_doppler
)


# ============================================================
# ERROR
# ============================================================

error = (
    estimated_doppler
    - truth_interpolated
)


mae = np.mean(
    np.abs(error)
)

rmse = np.sqrt(
    np.mean(
        error ** 2
    )
)


# ============================================================
# RESULTS
# ============================================================

print()
print("=" * 75)
print("IRIDIUM DOPPLER VALIDATION")
print("=" * 75)

print()

print(
    f"Number of estimates : "
    f"{len(estimated_doppler)}"
)

print()

print(
    f"Mean Absolute Error : "
    f"{mae:.2f} Hz"
)

print(
    f"RMSE                : "
    f"{rmse:.2f} Hz"
)

print()

print(
    f"Mean Absolute Error : "
    f"{mae / 1000:.4f} kHz"
)

print(
    f"RMSE                : "
    f"{rmse / 1000:.4f} kHz"
)


# ============================================================
# PLOT
# ============================================================

plt.figure(
    figsize=(12, 6)
)

plt.plot(
    truth_time,
    truth_doppler / 1000,
    label="Orbital prediction"
)

plt.plot(
    estimated_time,
    estimated_doppler / 1000,
    linestyle="--",
    label="IQ receiver estimate"
)

plt.xlabel(
    "Time (seconds)"
)

plt.ylabel(
    "Doppler (kHz)"
)

plt.title(
    "IRIDIUM Doppler — Prediction vs Receiver Estimate"
)

plt.legend()

plt.grid(True)

plt.tight_layout()

plt.show()


# ============================================================
# ERROR PLOT
# ============================================================

plt.figure(
    figsize=(12, 6)
)

plt.plot(
    estimated_time,
    error
)

plt.axhline(
    0,
    linestyle="--"
)

plt.xlabel(
    "Time (seconds)"
)

plt.ylabel(
    "Doppler error (Hz)"
)

plt.title(
    "IRIDIUM Doppler Estimation Error"
)

plt.grid(True)

plt.tight_layout()

plt.show()


print()
print("=" * 75)
print("VALIDATION COMPLETE")
print("=" * 75)