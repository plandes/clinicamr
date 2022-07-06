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
			nohup ./src/bin/plot.sh > plot.log 2>&1 &

.PHONY:			cleanplots
cleanplots:
			./clinicamr clean --clevel 2
			./clinicamr clear

.PHONY:			push
push:
			hostcon push -n nlproot --delete \
				--localdir '$(HOME)/view/nlp/med/clinicamr/amr-plot/' \
				--remotedir view/rgh/apache-amr/site/proofing

.PHONY:			stop
stop:
			ps -eaf | grep clinic | grep -v grep | awk '{print $2}' | xargs kill
