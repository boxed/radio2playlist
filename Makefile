collect-static:
	./manage.py collectstatic --no-input

migrate-deploy:
	./manage.py migrate --noinput

predeploy: migrate-deploy collect-static
