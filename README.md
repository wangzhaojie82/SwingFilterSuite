# Swing-Size Filter & Swing-Spread Filter

---

This repository contains the related codes of our paper "Compact Filters with Extended Filtering Range for Network Traffic Measurement."

## Introduction

In this paper, we investigate the problem of filtering small flows to improve the performance of network traffic measurement under limited resources and highly skewed traffic distribution. We identify the limitations of existing filters in either their filtering range or processing overhead, which restrict their effectiveness in handling large volumes of small flows. To address this, we propose two novel and flexible filters: Swing-Size Filter for filtering small-size flows, and Swing-Spread Filter for filtering small-spread flows. Both designs leverage signed counters whose value can swing between positive and negative directions to cancel out the impact of small flows, thereby extending the filtering range. We provide theoretical analyses of the proposed filters and then demonstrate their applicability to flow size and flow spread measurement tasks. We further implement our filters in both software and P4-based programmable switch hardware. Extensive experiments using real-world Internet traffic traces (collected by CAIDA) show that our filters can greatly improve measurement accuracy, roughly reducing errors by an order of magnitude.

## About this repo

- `data` contains a sample of CAIDA 2019 IP traces.

- `Swing-Size Filter` contains source code for software and hardware implementations of Swing-Size Filter.  
  
  - `CPU Implementation/`: Software implementation for CPU environments, including algorithm logic and evaluation.  
  - `P4 Implementation/`: Hardware implementation using the P4 language for programmable switches.

- `Swing-Spread Filter` contains source code for software and hardware implementations of Swing-Spread Filter.  
  
  - `CPU Implementation/`: Software implementation for CPU environments, including algorithm logic and evaluation.  
  - `P4 Implementation/`: Hardware implementation using the P4 language for programmable switches.
