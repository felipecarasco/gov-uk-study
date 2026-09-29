// Declarative pipeline, equivalent to .github/workflows/ci.yml and .gitlab-ci.yml.
//
// Like .gitlab-ci.yml, this file is not run by any agent: the repository is
// hosted on GitHub. It exists because the target environment uses self-hosted
// GitLab with Jenkins, and writing the same pipeline in all three formats keeps
// them comparable.
//
// A real Jenkins would need two more pieces of infrastructure, left out
// because they depend on the instance:
//   - `options { gitLabConnection('...') }` plus the GitLab webhook, so the
//     build status goes back to the merge request;
//   - registry credentials (`withCredentials`) in place of the commented-out
//     push at the end.

pipeline {
  // No global agent: each stage picks its own image and nothing is installed on the node.
  agent none

  options {
    timestamps()
    buildDiscarder(logRotator(numToKeepStr: '20'))
    timeout(time: 30, unit: 'MINUTES')
  }

  environment {
    // Maven cache inside the workspace: the stage container is thrown away on
    // every build, so ~/.m2 would not survive.
    MAVEN_ARGS = '--batch-mode -Dmaven.repo.local=.m2/repository'
  }

  stages {
    stage('Tests') {
      parallel {
        stage('API (Java 25)') {
          agent {
            docker {
              image 'eclipse-temurin:25-jdk'
              // The integration tests use Testcontainers, which needs to talk
              // to a Docker daemon. Mounting the host socket is the simplest
              // way; where policy forbids it, use a docker:dind service with
              // TESTCONTAINERS_HOST_OVERRIDE, as in .gitlab-ci.yml.
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
              // Unit (surefire) and integration (failsafe) tests report separately.
              junit allowEmptyResults: true,
                    testResults: 'api/target/surefire-reports/*.xml, api/target/failsafe-reports/*.xml'
            }
          }
        }

        stage('Front end (Python 3.12)') {
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

    stage('Images') {
      // Only build images from what passed the tests and is going to be deployed.
      when { branch 'main' }
      agent any
      steps {
        script {
          // Tag with the short SHA, not `latest`: on OpenShift that is what lets
          // a rollback point at one specific image.
          def tag = env.GIT_COMMIT.take(7)
          sh "docker build -t land-registry-api:${tag} ./api"
          sh "docker build -t land-registry-web:${tag} ./web"

          // Push and `oc tag`/rollout are left out while there is no registry
          // or target cluster:
          //   docker push .../land-registry-api:${tag}
          //   oc -n <project> set image deploy/api api=.../land-registry-api:${tag}
          echo "Images built with tag ${tag}."
        }
      }
    }
  }

  post {
    failure {
      echo 'Build failed. In the real environment the webhook would report the status back to the GitLab merge request.'
    }
  }
}
