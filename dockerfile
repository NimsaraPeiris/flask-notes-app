# Get the python 3.12 base image
FROM python:3.12-slim-bookworm

# Install uv package manager
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Change the working directory
WORKDIR /app

# Copy the project into the image
ADD . /app

# Sync the dependancies
RUN uv sync --frozen

# Expose port 5000 to access the app
EXPOSE 5000

# Set environment variables
ENV FLASK_APP=app.py
ENV FLASK_ENV=production

# Run the Flask app using Gunicorn
CMD ["uv", "run", "gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]
