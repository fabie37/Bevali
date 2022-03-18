SHELL := /bin/bash

OSFLAG 				:=
ifeq ($(OS),Windows_NT)
	OSFLAG += WIN32
else
	UNAME_S := $(shell uname -s)
	ifeq ($(UNAME_S),Linux)
		OSFLAG += LINUX
	endif
	ifeq ($(UNAME_S),Darwin)
		OSFLAG += OSX
	endif
endif

PYTHON				:=
ifeq ($(OSFLAG),WIN32)
	PYTHON += python
endif
ifeq ($(OSFLAG), OSX)
	PYTHON += python3
endif
ifeq ($(OSFLAG), LINUX)
	PYTHON += python3
endif

ENV  			:=
ifeq ($(OSFLAG),WIN32)
	ENV += ./env/Scripts/activate.bat
endif
ifeq ($(OSFLAG), OSX)
	ENV += source ./env/bin/activate
endif
ifeq ($(OSFLAG), LINUX)
	ENV += source ./env/bin/activate
endif

install:
	$(PYTHON) -m venv ./env/
	$(ENV) && pip install -r requirements.txt

test:
	coverage run -m pytest tests

evaluate:
	$(ENV) && $(PYTHON) evaluation/test_throughput.py
	$(ENV) && $(PYTHON) evaluation/graph_throughput.py

complete_run: test evaluate

source:
	$(ENV)

clean:
ifeq ($(OSFLAG),WIN32)
	./env/Scripts/deactivate.bat
	rm -r ./env/
endif
ifeq ($(OSFLAG),OSX)
	source ./env/bin/deactivate || deactivate
	rm -r ./env/
endif
ifeq ($(OSFLAG),LINUX)
	ource ./env/bin/deactivate || deactivate
	rm -r ./env/
endif