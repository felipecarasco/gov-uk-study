# API image, built to run on OpenShift.
#
# OpenShift ignores the image's USER and injects an arbitrary UID from the
# project's range, always in group 0 (root group). So the image must NOT depend
# on a specific user: everything the process reads or writes has to belong to
# group 0 with group permissions equal to the owner's (`chmod g=u`). An image
# that works with `docker run` and breaks on OpenShift almost always gets this
# wrong.

# ---------- build ----------
FROM eclipse-temurin:25-jdk AS build
WORKDIR /build

# The wrapper and the pom come before the code: while dependencies do not
# change, this layer stays cached and `go-offline` does not run again.
COPY .mvn/ .mvn/
COPY mvnw pom.xml ./
RUN ./mvnw --batch-mode dependency:go-offline

# Only src/main goes in: the image packages the artifact, it does not test it.
# The pipeline (Jenkins/GitLab CI) runs the tests before building the image,
# and the integration tests would need Docker inside the build because they use
# Testcontainers. A useful side effect: a red test in the middle of TDD does not
# stop the image from building.
COPY src/main/ src/main/
RUN ./mvnw --batch-mode -DskipTests package

# ---------- runtime ----------
FROM eclipse-temurin:25-jre
WORKDIR /app

# curl is here only for the HEALTHCHECK below. On OpenShift the kubelet runs
# the probes from outside the container, so it would not be needed there.
RUN apt-get update \
 && apt-get install -y --no-install-recommends curl \
 && rm -rf /var/lib/apt/lists/*

COPY --from=build /build/target/land-registry-api-*.jar app.jar

# Permissions that work with an arbitrary UID (see the note at the top).
RUN chgrp -R 0 /app && chmod -R g=u /app

# Nominal, unprivileged UID. OpenShift replaces it; with a plain `docker run`
# it is the one used. Either way the process is not root.
USER 1001

EXPOSE 8080

# OpenShift liveness/readiness probes point at /actuator/health; this
# HEALTHCHECK is the equivalent for `docker run` / compose.
HEALTHCHECK --interval=10s --timeout=3s --start-period=40s --retries=3 \
  CMD curl -fsS http://127.0.0.1:8080/actuator/health | grep -q '"status":"UP"'

# -XX:MaxRAMPercentage rather than -Xmx: in a container the memory limit comes
# from the cgroup, not the host, and the JVM must size the heap from it.
ENTRYPOINT ["java", "-XX:MaxRAMPercentage=75", "-jar", "app.jar"]
