FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

# Adding a non root user and giving ownership of the /app to the user
RUN adduser --disabled-password --no-create-home appuser && \
    chown -R appuser:appuser /app
USER appuser


# Google cloud run will inject it's own port variable during the runtime 
# so we need to define it here
ENV PORT=8080
EXPOSE 8080


# the amount of the works needs to be configured here as 
# the number of the vcpus are changed

# sh -c to start a shell so that can use the ${PORT} variable
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT} --workers 1"]
