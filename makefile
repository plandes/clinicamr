## makefile automates the build and deployment for python projects


## Build system
#
PROJ_TYPE =		python
PROJ_MODULES =		git python-resources python-cli python-doc python-doc-deploy
ADD_CLEAN +=		amr_graph
ADD_CLEAN_ALL +=	data

## Project
#
ENTRY=			./clinicamr


## Includes
#
include ./zenbuild/main.mk


## Targets
#
# generate AMR sentences by first parsing into graphs
.PHONY:			generate
generate:
			@echo "generating sentences"
			$(ENTRY) generate 134891,124656,104434,110132

# push graphs to NLPDeep server for annotation lookups
.PHONY:			push
push:
			hostcon push -n nlproot --delete \
				--localdir '$(HOME)/view/nlp/med/clinicamr/amr-plot/' \
				--remotedir view/rgh/apache-amr/site/proofing

# stop the plots
.PHONY:			stop
stop:
			ps -eaf | grep clinic | grep -v grep | awk '{print $$2}' | xargs kill


# TODO
.PHONY:			tmp
tmp:
			@echo "generating sentences"
			$(ENTRY) generate 110132
