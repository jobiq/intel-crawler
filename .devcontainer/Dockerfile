# FROM ubuntu:24.04

# # Install Node.js 22 manually
# RUN apt-get update && apt-get install -y curl gnupg \
#     && curl -fsSL https://deb.nodesource.com/setup_22.x | bash - \
#     && apt-get install -y nodejs build-essential
# RUN apt-get install -y sudo
# RUN curl -LsSf https://astral.sh/uv/install.sh | sh
# # RUN source $HOME/.local/bin/env

# # Set workdir
# WORKDIR /app

# # Copy everything
# COPY . /app

# # Install Python deps
# # RUN pip install -r requirements.txt

# # Install Node deps and generate Prisma client
# # RUN prisma generate

# # Expose the app port
# EXPOSE 3000

# # Run the FastAPI app
# # CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "3000"]
# CMD /bin/sh

FROM --platform=linux/amd64 python:3.12-slim

RUN apt-get update && apt-get install -y curl gnupg \
    && curl -fsSL https://deb.nodesource.com/setup_22.x | bash - \
    && apt-get install -y nodejs build-essential
RUN apt-get install -y sudo
RUN curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies
RUN apt-get update && apt-get install -y \
    chromium \
    chromium-driver \
    xvfb \
    curl \
    unzip \
    fonts-liberation \
    libappindicator3-1 \
    libasound2 \
    libatk-bridge2.0-0 \
    libnspr4 \
    libnss3 \
    libx11-xcb1 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    x11-utils \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set environment variables for Chromium
ENV CHROMIUM_BIN=/usr/bin/chromium
ENV CHROMEDRIVER_BIN=/usr/bin/chromedriver

# Start Xvfb automatically
ENV DISPLAY=:99
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# ENTRYPOINT ["/entrypoint.sh"]
# # CMD ["Xvfb", ":99" "-screen" "0" "1920x1080x24 &"]
# RUN /entrypoint.sh
