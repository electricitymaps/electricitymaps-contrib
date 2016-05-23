install:
	pip install -r server/requirements.txt
	sudo gem install foreman

server:
	foreman start

api:
	python -u server/server.py

feeder:
	python -u server/feeder.py

db:
	mongod
