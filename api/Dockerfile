# Imagem da API, construída para rodar no OpenShift.
#
# O OpenShift ignora o UID do `USER` e injeta um UID arbitrário do range do
# projeto, sempre no grupo 0 (root group). Por isso a imagem NÃO pode depender
# de um usuário específico: tudo que o processo precisa escrever ou ler tem de
# pertencer ao grupo 0 com permissão de grupo igual à do dono (`chmod g=u`).
# Uma imagem que funciona no `docker run` e quebra no OpenShift quase sempre
# erra exatamente nisso.

# ---------- build ----------
FROM eclipse-temurin:25-jdk AS build
WORKDIR /build

# O wrapper e o pom vêm antes do código: enquanto as dependências não mudam,
# esta camada fica em cache e o `go-offline` não roda de novo.
COPY .mvn/ .mvn/
COPY mvnw pom.xml ./
RUN ./mvnw --batch-mode dependency:go-offline

# Só src/main entra: a imagem existe para empacotar o artefato, não para testar.
# Quem roda os testes é o pipeline (Jenkins/GitLab CI), antes de mandar construir
# a imagem — e os testes de integração precisariam de um Docker dentro do build,
# porque usam Testcontainers. Como consequência útil, um teste em vermelho no meio
# de um TDD não impede de gerar a imagem.
COPY src/main/ src/main/
RUN ./mvnw --batch-mode -DskipTests package

# ---------- runtime ----------
FROM eclipse-temurin:25-jre
WORKDIR /app

# curl existe aqui só para servir ao HEALTHCHECK abaixo. No OpenShift as probes
# são feitas pelo kubelet, de fora do container, e ele seria dispensável.
RUN apt-get update \
 && apt-get install -y --no-install-recommends curl \
 && rm -rf /var/lib/apt/lists/*

COPY --from=build /build/target/land-registry-api-*.jar app.jar

# Permissões compatíveis com UID arbitrário (ver comentário no topo).
RUN chgrp -R 0 /app && chmod -R g=u /app

# UID nominal, não privilegiado. No OpenShift ele é substituído; num `docker
# run` puro é ele que vale — nos dois casos o processo não é root.
USER 1001

EXPOSE 8080

# Liveness/readiness no OpenShift apontam para /actuator/health; o HEALTHCHECK
# abaixo é o equivalente para `docker run` / compose.
HEALTHCHECK --interval=10s --timeout=3s --start-period=40s --retries=3 \
  CMD curl -fsS http://127.0.0.1:8080/actuator/health | grep -q '"status":"UP"'

# `-XX:MaxRAMPercentage` em vez de `-Xmx`: no container o limite de memória vem
# do cgroup, não da máquina, e a JVM precisa dimensionar o heap por ele.
ENTRYPOINT ["java", "-XX:MaxRAMPercentage=75", "-jar", "app.jar"]
