init_windows:
	py -3 -m venv ./env/
	./env/Scripts/activate.bat
	pip install -r requirements.txt

init_unix:
	python3 -m venv ./env/
	source ./env/bin/activate
	pip install -r requirements.txt

clean_windows:
	./env/Scripts/deactivate.bat
	rm -r ./env/

clean_unix:
	source ./env/bin/deactivate
	rm -r ./env/

test:
	py.test tests