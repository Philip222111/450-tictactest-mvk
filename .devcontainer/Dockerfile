FROM eclipse-temurin:25-jdk-noble

ARG GRADLE_VERSION=9.7.0

# Die OCI-Metadaten verbinden das veröffentlichte Image mit dem Repository.
LABEL org.opencontainers.image.source="https://github.com/Philip222111/450-tictactest-mvk"
LABEL org.opencontainers.image.description="Java 25 development environment for TicTacTest"

# Ubuntu/glibc supports the Node runtime of GitHub Actions.
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        bash ca-certificates curl git openssh-client unzip \
    && rm -rf /var/lib/apt/lists/* \
    && curl --fail --location --silent --show-error \
        "https://services.gradle.org/distributions/gradle-${GRADLE_VERSION}-bin.zip" \
        --output /tmp/gradle.zip \
    && unzip -q /tmp/gradle.zip -d /opt \
    && ln -s "/opt/gradle-${GRADLE_VERSION}" /opt/gradle \
    && ln -s /opt/gradle/bin/gradle /usr/local/bin/gradle \
    && rm /tmp/gradle.zip \
    && groupmod --new-name vscode ubuntu \
    && usermod --login vscode --home /home/vscode --move-home --shell /bin/bash ubuntu \
    && mkdir -p /home/vscode/.gradle \
    && chown -R vscode:vscode /home/vscode \
    && printf '%s\n' \
        'export JAVA_HOME=/opt/java/openjdk' \
        'export PATH="$JAVA_HOME/bin:$PATH"' \
        > /etc/profile.d/java.sh

# Entwicklungs- und CI-Befehle laufen ohne Root-Rechte.
USER vscode
WORKDIR /workspaces
