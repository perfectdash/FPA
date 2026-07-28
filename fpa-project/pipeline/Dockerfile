# Base image matches the Apache Beam SDK python version
FROM apache/beam_python3.11_sdk:2.56.0

# Set the working directory inside the container
WORKDIR /app

# Copy requirements file first for layer caching
COPY requirements.txt .

# Install dependencies needed by the pipeline
RUN pip install --no-cache-dir -r requirements.txt

# Copy pipeline code into the image
COPY . .

# Set container entry point (Apache Beam SDK default entrypoint is inherited)
ENTRYPOINT ["/opt/apache/beam/boot"]
