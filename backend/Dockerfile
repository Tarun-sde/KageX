FROM eclipse-temurin:17-jdk-jammy AS ck-build
WORKDIR /tools
ADD --checksum=sha256:2ddfdc275b6b59c2033e03253c4fec511c338fe494a10b70f651bc039a72c74d https://repo.maven.apache.org/maven2/com/github/mauricioaniche/ck/0.7.0/ck-0.7.0-jar-with-dependencies.jar ck.jar
COPY app/analyzers/tools/KagexCK.java ./
RUN javac --release 17 -cp ck.jar KagexCK.java && chmod 644 ck.jar

FROM node:24.14.0-bookworm-slim AS node-tools
WORKDIR /tools
COPY app/analyzers/tools/package*.json ./
RUN npm ci --ignore-scripts --omit=dev

FROM python:3.14-slim AS api
COPY --from=ghcr.io/astral-sh/uv:0.12.23 /uv /usr/local/bin/uv
ENV PYTHONUNBUFFERED=1 UV_COMPILE_BYTECODE=1 PATH="/app/.venv/bin:$PATH"
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project
COPY app ./app
COPY alembic ./alembic
COPY alembic.ini ./
RUN uv sync --frozen --no-dev && useradd --create-home --uid 10001 kagex && mkdir -p /app/storage && chmod 700 /app/storage && chown -R kagex:kagex /app
USER kagex
EXPOSE 8000
CMD ["python", "-m", "app"]

FROM api AS worker
USER root
COPY --from=eclipse-temurin:17-jre-jammy /opt/java/openjdk /opt/java/openjdk
COPY --from=node-tools /usr/local/bin/node /usr/bin/node
COPY --from=node-tools /tools/node_modules /app/app/analyzers/tools/node_modules
COPY --from=ck-build /tools/ /app/app/analyzers/tools/
ENV ANALYZER_JAVA=/opt/java/openjdk/bin/java
USER kagex
