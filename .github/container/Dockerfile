# Ubuntu provides glibc for the Node.js runtime used by GitHub Actions.
FROM eclipse-temurin:25-jdk-noble

LABEL org.opencontainers.image.source="https://github.com/Philip222111/450-tictactest-mvk"
LABEL org.opencontainers.image.description="Java 25 build environment for TicTacTest CI"

RUN apt-get update \
    && apt-get install -y --no-install-recommends bash ca-certificates curl git unzip \
    && rm -rf /var/lib/apt/lists/*

# The checked-out project's Gradle Wrapper supplies the Gradle version.
WORKDIR /workspace
