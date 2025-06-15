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
# install dependencies need by the the models (both training and inference)
.PHONY:			modeldeps
modeldeps:
			$(PIP_BIN) install $(PIP_ARGS) \
				-r $(PY_SRC)/requirements-model.txt --no-deps

# plot a sentence
.PHONY:			plot
plot:
			$(eval SENT=58 y/o M with multiple myeloma s/p chemo and auto SCT [**4-27**]\npresenting with acute onset of CP and liver failure)
			@echo "parsing: $(SENT)"
			$(ENTRY) plot '$(SENT)'


# generate AMR sentences by first parsing into graphs
.PHONY:			generate
generate:
			@echo "generating sentences"
			$(ENTRY) generate 134891,124656,104434,110132

# get DSProv annotated admissions by note count per admission
.PHONY:			admbycount
admbycount:
			./src/bin/adm-by-count.py
