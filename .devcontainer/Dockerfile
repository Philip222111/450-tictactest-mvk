FROM eclipse-temurin:25-jdk-alpine

ARG GRADLE_VERSION=9.7.0

RUN apk add --no-cache \
        bash \
        curl \
        git \
        openssh-client \
        shadow \
        unzip \
    && curl --fail --location --silent --show-error \
        "https://services.gradle.org/distributions/gradle-${GRADLE_VERSION}-bin.zip" \
        --output /tmp/gradle.zip \
    && unzip -q /tmp/gradle.zip -d /opt \
    && ln -s "/opt/gradle-${GRADLE_VERSION}" /opt/gradle \
    && ln -s /opt/gradle/bin/gradle /usr/local/bin/gradle \
    && rm /tmp/gradle.zip \
    && groupadd --gid 1000 vscode \
    && useradd --uid 1000 --gid 1000 --create-home --shell /bin/bash vscode \
    && mkdir -p /home/vscode/.gradle \
    && chown -R vscode:vscode /home/vscode

USER vscode
WORKDIR /workspaces
