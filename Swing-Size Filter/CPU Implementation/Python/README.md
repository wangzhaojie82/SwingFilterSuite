# Python implementation of Swing-Size Filter

This folder contains python scripts for conducting experiments related to flow size measurement tasks. 

## Scripts list

- Packet.py: An encapsulation of IP data. This script is responsible for encapsulating IP data, providing a structured format for processing.

- Exp_Flow_Size_Estimation_: This script is to conduct experiments related to flow size estimation. 

- Exp_Top_k_Query_.py: This script is to conduct experiments related to Top-k query.

- Exp_Heavy_Hitter_Detection_.py: This script is to conduct experiments related to heavy hitter detection.

- filters/\* : Implementations of related filters and the list of large flows in Augmented Sketch

- sketches/\* :  Implementations of related sketches

## Basic Usage

Take the Flow Size Estimation experiment as an example. 

In the `run_parallel()` function, specify your data file path and set the desired memory size for testing. This function will call the `exp_flow_size_es()` function for each parameter set and execute them in parallel.

At lines 38-39 of `exp_flow_size_es()`, initialize the filters and measurement algorithms you wish to test.

Once everything is set up, simply run the `main` function. The program will print the results, or you can write them to a file for further analysis.
