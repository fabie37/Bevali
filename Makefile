SHELL := /bin/bash
PYTHON = unk
ENV = unk
OSFLAG 				:=
ifeq ($(OS),Windows_NT)
	OSFLAG += WIN32
	PYTHON = python
	ENV += ./env/Scripts/activate.bat
else
	UNAME_S := $(shell uname -s)
	ifeq ($(UNAME_S),Linux)
		OSFLAG = LINUX
		PYTHON = python3
		ENV = source ./env/bin/activate
	endif
	ifeq ($(UNAME_S),Darwin)
		OSFLAG = OSX
		PYTHON = python3
		ENV = source ./env/bin/activate
	endif
endif

install:
	$(PYTHON) -m venv ./env/
	$(ENV) && pip install -r requirements.txt

test:
	$(ENV) && coverage run -m pytest tests

evaluate:
	$(ENV) && $(PYTHON) evaluation/test_throughput.py
	$(ENV) && $(PYTHON) evaluation/graph_throughput.py

complete_run: test evaluate

source:
	echo $(ENV)

os:
	echo $(OSFLAG)

python:
	echo $(PYTHON)

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
	rm -r ./env/
endif