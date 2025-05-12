# P4 Implementation of Swing Filter

This folder contains the source code for P4 implementation of Swing Filter.

## Description

We implement Swing Filter using the P4_16 language, targeting both software and hardware switches. Our implementation is compatible with:

- BMv2 (Behavioral Model v2) — a software switch for functional testing and validation.
- Barefoot Tofino programmable switches — high-performance programmable switches based on the Tofino ASIC.

## Folder Structure

```
.
├── BMv2/
│   └── [P4 and other related code for BMv2 software switch]
├── BF_Layer=1_switch.p4   # One-layer version for Tofino hardware
├── BF_Layer=2_switch.p4   # Two-layer version for Tofino hardware
└── README.md
```
