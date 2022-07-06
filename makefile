## makefile automates the build and deployment for python projects

## build config

# type of project
PROJ_TYPE =		python
PROJ_MODULES =		git python-resources python-cli python-doc python-doc-deploy
INFO_TARGETS +=		appinfo
CLEAN_ALL_DEPS +=	cleanplots

include ./zenbuild/main.mk

.PHONY:			appinfo
appinfo:
			@echo "app-resources-dir: $(RESOURCES_DIR)"

.PHONY:			plot
plot:
			./clinicamr clear
			./clinicamr plot
			./clinicamr plot --override='amr_default.parse_model=gsii'

.PHONY:			cleanplots
cleanplots:
			./clinicamr clean --clevel 2
			./clinicamr clear

.PHONY:			push
push:
			hostcon push -n nlproot --delete \
				--localdir '$(HOME)/view/nlp/med/clinicamr/amr-plot/' \
				--remotedir view/rgh/apache-amr/site/proofing
