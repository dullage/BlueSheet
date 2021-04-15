FROM dullage/gunicorn:20.0-python3.8-alpine3.12

COPY . /app

# Switch to root to install dependendies
USER 0

RUN apk add --update-cache \
    build-base \
 && rm -rf /var/cache/apk/*

# Switch back to the gunicorn user
USER 1000

RUN pip install pipenv && pipenv install --system --deploy --ignore-pipfile
