## makefile automates the build and deployment for python projects


## Build system
#
PROJ_TYPE =		python
PROJ_MODULES =		git python-resources python-cli python-doc python-doc-deploy
ADD_CLEAN +=		amr_graph

## Project
#
ENTRY=			./clinicamr


## Includes
#
include ./zenbuild/main.mk


## Targets
#
.PHONY:			plot
plot:
			nohup ./src/bin/plot.sh > plot.log 2>&1 &

.PHONY:			push
push:
			hostcon push -n nlproot --delete \
				--localdir '$(HOME)/view/nlp/med/clinicamr/amr-plot/' \
				--remotedir view/rgh/apache-amr/site/proofing

.PHONY:			stop
stop:
			ps -eaf | grep clinic | grep -v grep | awk '{print $$2}' | xargs kill

.PHONY:			proofrep
proofrep:
			$(ENTRY) proofrep --output /d/proof.csv \
				--override amr_default.parse_model=gsii
