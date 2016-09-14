.PHONY: server

install: install-grib2json
	pip install -r requirements.txt
	pip install honcho==0.7.1
	
install-grib2json:
	git clone https://github.com/cambecc/grib2json
	cd grib2json && mvn package && tar -xvf target/grib2json-0.8.0-SNAPSHOT.tar.gz

server:
	honcho start

api:
	python -u server.py

feeder:
	python -u backend/feeder.py

db:
	mongod

publish-gh-pages:
	git subtree push --prefix public origin gh-pages
