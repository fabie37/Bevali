init_windows:
	py -3 -m venv ./env/
	./env/Scripts/activate.bat
<<<<<<< HEAD
	py -3 -m pip install -r requirements.txt
=======
	pip install -r requirements.txt
>>>>>>> acad1aa314fff8a685ac8de976c6450052124b54

init_unix:
	python3 -m venv ./env/
	source ./env/bin/activate
<<<<<<< HEAD
	python3 -m pip install -r requirements.txt
=======
	pip install -r requirements.txt
>>>>>>> acad1aa314fff8a685ac8de976c6450052124b54

clean_windows:
	./env/Scripts/deactivate.bat
	rm -r ./env/

clean_unix:
	source ./env/bin/deactivate
	rm -r ./env/

test:
	py.test tests