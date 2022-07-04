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
			./clinicamr plot --override='amr_default.parse_model=gsii'

.PHONY:			cleanplots
cleanplots:
			./clinicamr clean --clevel 2
			./clinicamr clear
