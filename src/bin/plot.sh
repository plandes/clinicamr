#!/bin/sh

./clinicamr clean --clevel 2
./clinicamr clear
./clinicamr plot --mode by_paragraph --override='amr_default.parse_model=gsii'
./clinicamr clear
./clinicamr plot --mode by_paragraph --override='amr_default.parse_model=t5'
