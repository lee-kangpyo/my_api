# Use the official Python image as the base image
FROM python:3.13.1

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container at /app
COPY requirements.txt /app/

# 패키지 업데이트 및 Vim 설치
RUN apt-get update && \
    apt-get install -y vim

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the current directory contents into the container at /app
COPY . /app/

# Set the timezone to Asia/Seoul
ENV TZ=Asia/Seoul

# Create the uploads directory
RUN mkdir -p /app/uploads

# Make port 80 available to the world outside this container
EXPOSE 80



# Run the Gunicorn server with FastAPI app
# CMD ["gunicorn", "-b", "0.0.0.0:80", "main:app"]
#CMD ["gunicorn", "-w", "2", "-k", "uvicorn.workers.UvicornWorker", "-b", "0.0.0.0:80", "--log-config", "log.ini", "main:app"]
CMD ["gunicorn", "-c", "gunicorn.conf.py", "main:app"]
