## makefile automates the build and deployment for python projects


## Build system
#
PROJ_TYPE =		python
PROJ_MODULES =		python/doc python/package python/deploy
PY_TEST_ALL_TARGETS +=	plot generate
ADD_CLEAN +=		amr_graph
ADD_CLEAN_ALL +=	data


## Includes
#
include ./zenbuild/main.mk


## Targets
#
# plot a sentence
.PHONY:			plot
plot:
			$(eval SENT := $(strip $(file <test-resources/clinical-example.txt)))
			@echo "parsing: $(SENT)"
			@$(MAKE) $(PY_MAKE_ARGS) pyharn ARG="plot '$(SENT)'"

# generate AMR sentences by first parsing into graphs
.PHONY:			generate
generate:
			@echo "generating sentences"
			@$(MAKE) $(PY_MAKE_ARGS) pyharn \
				ARG="generate 134891,124656,104434,110132"
