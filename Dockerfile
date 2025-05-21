# FROM ubuntu:24.04

# # Install Node.js 22 manually
# RUN apt-get update && apt-get install -y curl gnupg \
#     && curl -fsSL https://deb.nodesource.com/setup_22.x | bash - \
#     && apt-get install -y nodejs build-essential

# RUN apt-get install sudo
# RUN curl -LsSf https://astral.sh/uv/install.sh | sh

# ENV DEBIAN_FRONTEND=noninteractive
# RUN apt-get install -y software-properties-common && \
#     add-apt-repository ppa:xtradeb/apps -y && \
#     apt-get update && \
#     apt-get install -y chromium

# # Set workdir
# WORKDIR /app

# # Copy everything
# COPY . /app

# # Install Python deps
# RUN uv venv
# RUN source .venv/bin/activate
# RUN uv pip install -r requirements.txt



# # Install Node deps and generate Prisma client
# RUN prisma generate

# # Expose the app port
# EXPOSE 3000

# # Run the FastAPI app
# CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "3000"]


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

FROM python:3.12-slim

ARG DATABASE_URL
ARG MANAGER_PORT
ARG MANAGER_RELOAD
ARG MAIL_PASSWORD
ARG GEMINI_API_KEY

RUN apt-get update && apt-get install -y curl gnupg \
    && curl -fsSL https://deb.nodesource.com/setup_22.x | bash - \
    && apt-get install -y nodejs build-essential
RUN apt-get install -y sudo

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

# Set workdir
WORKDIR /app

# Copy everything
COPY . /app

# Install Python deps
RUN pip install -r requirements.txt

# Install Node deps and generate Prisma client

RUN prisma db push
RUN prisma generate

# Expose the app port
EXPOSE 3000

ENV DISPLAY=:99
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Run the FastAPI app
# CMD ["Xvfb", ":99" "-screen" "0" "1920x1080x24 &"]
# CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "3000"]
ENTRYPOINT ["/entrypoint.sh"]