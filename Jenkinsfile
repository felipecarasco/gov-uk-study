// Pipeline declarativo, equivalente ao .github/workflows/ci.yml e ao .gitlab-ci.yml.
//
// Como o .gitlab-ci.yml, este arquivo NÃO é executado por nenhum runner: o
// repositório vive no GitHub. Ele existe porque o ambiente-alvo (HMLR) usa
// GitLab self-hosted com Jenkins, e expressar o mesmo pipeline nos três formatos
// documenta o entendimento daquele ambiente.
//
// Num Jenkins de verdade faltariam duas coisas de infraestrutura, deixadas de
// fora porque dependem da instância:
//   - `options { gitLabConnection('...') }` mais o webhook do GitLab, para o
//     status do build voltar ao merge request;
//   - credenciais do registry (`withCredentials`) no lugar do push comentado
//     no fim.

pipeline {
  // Sem agente global: cada stage escolhe sua imagem, e nada é instalado no nó.
  agent none

  options {
    timestamps()
    buildDiscarder(logRotator(numToKeepStr: '20'))
    timeout(time: 30, unit: 'MINUTES')
  }

  environment {
    // Cache do Maven dentro do workspace: o container do stage é descartado a
    // cada build, então ~/.m2 não sobrevive.
    MAVEN_ARGS = '--batch-mode -Dmaven.repo.local=.m2/repository'
  }

  stages {
    stage('Testes') {
      parallel {
        stage('API (Java 25)') {
          agent {
            docker {
              image 'eclipse-temurin:25-jdk'
              // Os testes de integração usam Testcontainers, que precisa falar
              // com um daemon Docker. Montar o socket do host é o caminho mais
              // simples; onde isso for vetado por política, a alternativa é um
              // serviço docker:dind com TESTCONTAINERS_HOST_OVERRIDE, como no
              // .gitlab-ci.yml.
              args '-v /var/run/docker.sock:/var/run/docker.sock --group-add docker'
              reuseNode true
            }
          }
          steps {
            dir('api') {
              sh './mvnw $MAVEN_ARGS verify'
            }
          }
          post {
            always {
              // Unitários (surefire) e integração (failsafe) em relatórios separados.
              junit allowEmptyResults: true,
                    testResults: 'api/target/surefire-reports/*.xml, api/target/failsafe-reports/*.xml'
            }
          }
        }

        stage('Front-end (Python 3.12)') {
          agent {
            docker {
              image 'python:3.12-slim'
              reuseNode true
            }
          }
          steps {
            dir('web') {
              sh '''
                pip install --no-cache-dir uv
                uv sync --all-groups
                uv run ruff check .
                uv run ruff format --check .
                uv run pytest --junitxml=pytest-report.xml --cov=app --cov-report=term-missing
              '''
            }
          }
          post {
            always {
              junit allowEmptyResults: true, testResults: 'web/pytest-report.xml'
            }
          }
        }
      }
    }

    stage('Imagens') {
      // Só constrói imagem do que já passou nos testes e vai virar deploy.
      when { branch 'main' }
      agent any
      steps {
        script {
          // A tag é o SHA curto, não `latest`: no OpenShift é o que permite
          // apontar o rollback para uma imagem específica.
          def tag = env.GIT_COMMIT.take(7)
          sh "docker build -t land-registry-api:${tag} ./api"
          sh "docker build -t land-registry-web:${tag} ./web"

          // Push e `oc tag`/rollout ficam de fora enquanto não há registry nem
          // cluster alvo neste projeto de estudo:
          //   docker push .../land-registry-api:${tag}
          //   oc -n <projeto> set image deploy/api api=.../land-registry-api:${tag}
          echo "Imagens construídas com a tag ${tag}."
        }
      }
    }
  }

  post {
    failure {
      echo 'Build vermelho. No ambiente real, o webhook devolveria o status ao merge request no GitLab.'
    }
  }
}
