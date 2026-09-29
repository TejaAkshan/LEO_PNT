# LEO-PNT: Positioning Using Low Earth Orbit Satellite Data

## Overview

This project explores the use of Low Earth Orbit (LEO) satellite data for Positioning, Navigation, and Timing (PNT) in environments where conventional GNSS/GPS-based positioning may be unavailable or degraded.

The project focuses on the Iridium satellite constellation and investigates whether satellite position and range information can be used to estimate the position of a receiver on Earth.

The final implementation uses a publicly available Iridium Ring Alert dataset and performs satellite-data processing, coordinate transformations, multilateration, and positioning-error analysis using Python.

---

## Motivation

Global Navigation Satellite Systems (GNSS), such as GPS, are widely used for positioning and navigation. However, GNSS signals can become unavailable or unreliable in environments affected by signal obstruction, interference, jamming, or other limitations.

LEO satellite constellations provide an alternative source of satellite-based measurements that can potentially be exploited for positioning.

The objective of this project was therefore to investigate:

- How LEO satellite position data can be processed for positioning.
- How satellite-to-receiver ranges can be calculated.
- How multiple satellite measurements can be combined using multilateration.
- How measurement errors affect the resulting position estimate.
- Whether publicly available Iridium satellite data can be used to demonstrate the underlying positioning concept.

---

## Project Objective

The main objective was to develop a positioning analysis pipeline that:

1. Processes Iridium satellite data.
2. Extracts relevant satellite information.
3. Determines satellite positions.
4. Converts geographic coordinates into Earth-Centered, Earth-Fixed (ECEF) coordinates.
5. Calculates satellite-to-receiver ranges.
6. Uses multiple satellite measurements for multilateration.
7. Estimates the receiver position.
8. Evaluates how measurement errors affect positioning accuracy.

---

## Original Approach

The initial project concept involved building a live satellite-signal processing pipeline using:

- QFH antenna
- RTL-SDR
- GNU Radio
- Live Iridium signal reception
- Doppler analysis
- Satellite identification
- Position estimation

The hardware acquisition path was not sufficiently reliable for a complete live SDR-based implementation.

Therefore, the project was adapted to use a real publicly available Iridium Ring Alert dataset. This allowed the positioning and data-analysis portions of the project to be developed and tested using real satellite data rather than simulated satellite trajectories.

This pivot allowed the project to focus on the underlying LEO-PNT positioning problem and its mathematical analysis.

---

# Dataset

The project uses a publicly available Iridium Ring Alert dataset hosted on Zenodo.

Dataset:

**Iridium Ring Alert Dataset**

DOI:

`10.5281/zenodo.8220494`

The dataset contains approximately 1.78 million records and information associated with multiple Iridium satellites.

The analysis identified 66 unique satellite IDs within the processed data.

---

# System Workflow

The overall processing pipeline is:

```text
Public Iridium Ring Alert Dataset
                |
                v
        Data Preprocessing
                |
                v
      Extract Satellite Metadata
                |
                v
     Filter Relevant Satellite Data
                |
                v
 Satellite Latitude / Longitude / Altitude
                |
                v
       Convert to ECEF Coordinates
                |
                v
       Calculate Satellite Ranges
                |
                v
       Select Multiple Satellites
                |
                v
         Multilateration
                |
                v
       Estimate Receiver Position
                |
                v
     Position Error Analysis
                |
                v
       Monte-Carlo Experiments