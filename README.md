# GoGo
the source code and executable file of the GoGo software

## Introduction

This is a software with GUI to help design primers which are used in Golden gate clone.

## Usage

The GUI was maked by Pyside2, if you want to run the source python file, you need to install the Pside2 package.

You can also run the GoGo.exe in the GoGo directory on Windows platform



The custom needs to input protospacer sequence and define donor vectors and promoters. GoGo will give an error if protospacers contain BsaI recognition site "GGTCTC". Based on the input information, GoGo will split protospacers (adjacent sequence will also be considered if necessary)for calculating all possible overhang combinations. Palindromic or low-fidelity overhangs will-be eliminated at first.Overhang pairs with: the same, similar (3 out of 4 bases are the same), reverse complementary or reverse complementary similar sequences will be eliminated in
overhang combinations. Then primers will be designed based on specific sequences of sgRNA and presetting promoters. GOGO was written by Python and the GUI was made by Qt designer. 
