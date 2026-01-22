# ORCA DFT Calculator

A minimal Streamlit app for running basic ORCA DFT calculations.

## Features

- Geometry optimization calculations with B3LYP/def2-SVP
- XYZ format molecular geometry input
- Real-time calculation status
- Results display (final energy and optimized geometry)
- Full ORCA output file download

## Requirements

- ORCA quantum chemistry package installed and accessible via `orca` command
- Python 3.7+
- Streamlit

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Ensure ORCA is installed and in your PATH

## Usage

Run the Streamlit app:
```bash
streamlit run app.py
```

## Default Example

The app comes pre-loaded with a water molecule geometry:
```
O 0.0 0.0 0.0
H 0.96 0.0 0.0
H -0.24 0.93 0.0
```

## Calculation Parameters

- **Method**: B3LYP (hardcoded)
- **Basis Set**: def2-SVP (hardcoded)
- **Calculation Type**: Geometry Optimization (hardcoded)

## Notes

- Temporary files are automatically cleaned up after each calculation
- Calculations have a 5-minute timeout
- Error handling for ORCA installation and execution issues
