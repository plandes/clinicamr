#!/bin/sh

./clinicamr plot --mode by_paragraph --override='amr_default.parse_model=gsii'
./clinicamr plot --mode by_paragraph --override='amr_default.parse_model=t5'
