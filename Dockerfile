FROM php:7.4-apache

RUN apt-get update && apt-get install -y wget gnupg unzip

# Install node and npm
RUN curl -sL https://deb.nodesource.com/setup_16.x | bash -
RUN apt-get install -y nodejs

# Install Selenium and its dependencies
RUN apt-get update && apt-get install -y libglib2.0-0 libnss3 libx11-6 libx11-xcb1 libxcb1 libxcomposite1 libxcursor1 libxdamage1 libxext6 libxfixes3 libxi6 libxrandr2 libxrender1 libxtst6 libatspi2.0-0 libappindicator3-1 libsecret-1-0
RUN wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | apt-key add -
RUN echo 'deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main' | tee /etc/apt/sources.list.d/google-chrome.list
RUN apt-get update && apt-get install -y google-chrome-stable
RUN wget https://chromedriver.storage.googleapis.com/111.0.5563.64/chromedriver_linux64.zip && unzip chromedriver_linux64.zip && mv chromedriver /usr/local/bin/
RUN chmod +x /usr/local/bin/chromedriver

# Install axe-cli
RUN npm install -g @axe-core/cli

# Copy the PHP files to the container
COPY index.php /var/www/html/
