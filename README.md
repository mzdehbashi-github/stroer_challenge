## Stroer challenge

### Prerequisites
  - docker
  - docker-compose


### How to set up and run
```shell
# Spin up the services
docker-compose up --build

# Create django-admin user
docker-compose run backendserver python manage.py createsuperuser

# You can access django admin dashboard at http://localhost:8000/admin

# Import posts and comments from external API
docker-compose run backendserver python manage.py bootstrap_blog 

# Then you can add/modify record, using django-admin dashboard

# Synchronizes records in external API, according to local DB
docker-compose run backendserver python manage.py synchronize

# Finally to remove services (and related volumes)
docker-compose down -v
```

You can also visit:
- API-docs on http://localhost:8000/api/swagger


### Libraries that I used:
- `gunicorn`: for running production ready web server
- `whitenoise`: for serving staticfiles as an easy solution
- `psycopg2-binary`: to handle communication via postgres
- `aiohttp`: to handle sending multiple http requests concurrently
- `requests`: to send blocking http requests
