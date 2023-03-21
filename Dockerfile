# Install Python
FROM python:3.9-slim-buster


# Install node and npm
RUN curl -sL https://deb.nodesource.com/setup_16.x | bash -
RUN apt-get install -y nodejs


# Install Selenium and its dependencies
RUN apt-get update && apt-get install -y wget gnupg unzip libglib2.0-0 libnss3 libx11-6 libx11-xcb1 libxcb1 libxcomposite1 libxcursor1 libxdamage1 libxext6 libxfixes3 libxi6 libxrandr2 libxrender1 libxtst6 libatspi2.0-0 libappindicator3-1 libsecret-1-0 google-chrome-stable

RUN wget https://chromedriver.storage.googleapis.com/111.0.5563.64/chromedriver_linux64.zip && unzip chromedriver_linux64.zip && mv chromedriver /usr/local/bin/
RUN chmod +x /usr/local/bin/chromedriver

RUN pip install flask

RUN npm install -g @axe-core/cli

COPY . /app
WORKDIR /app

ENV PORT 8083

CMD ["python", "app.py"]

