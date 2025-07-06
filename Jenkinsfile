pipeline {
  agent any
  environment {
    REGISTRY_CRED_ID = 'docker-registry-creds'
    DOCKER_REGISTRY  = 'idirym92/serviceclient'
    IMAGE_TAG        = "${env.BUILD_NUMBER}"
  }

  stages {
    stage('🔍 Checkout') {
      steps {
        checkout scm
      }
    }

    stage('🧪 Tests Unitaires') {
	  steps {
		bat '''
		  docker run --rm ^
			-e CLIENT_DB_URL="sqlite:///:memory:" ^
			-v "%WORKSPACE%\\commandes-service":/app ^
			-w /app ^
			python:3.11-slim ^
			sh -c "pip install --upgrade pip && \
				   pip install -r requirements.txt && \
				   pytest --maxfail=1 --disable-warnings -q --junitxml=reports/results.xml"
		'''
	  }
	  post {
		always {
		  junit 'commandes-service/reports/results.xml'
		}
		failure {
		  echo '❌ Les tests ont échoué !'
		}
	  }
	}

    stage('🐳 Build & Push Docker Image') {
      steps {
        bat label: 'Build & Push', script: """
          REM → build de l’image de production
          docker build ^
            -t %DOCKER_REGISTRY%:%IMAGE_TAG% ^
            -f commandes-service\\Dockerfile ^
            commandes-service
        """
        withCredentials([usernamePassword(
          credentialsId: "${REGISTRY_CRED_ID}",
          usernameVariable: 'DOCKER_USER',
          passwordVariable: 'DOCKER_PASS'
        )]) {
          bat label: 'Docker Login & Push', script: """
			
            docker logout
			docker login -u "%DOCKER_USER%" -p "%DOCKER_PASS%"
            docker push %DOCKER_REGISTRY%:%IMAGE_TAG%
          """
        }
      }
    }

    stage('🚀 Deploy en local') {
      steps {
        bat label: 'docker-compose up', script: """
          cd commandes-service
          REM → pull & relance tes conteneurs en local
		  docker-compose down
          docker-compose pull
          docker-compose up -d --no-deps --build
        """
      }
    }
  }

  post {
    success { echo '✅ Pipeline terminée avec succès !' }
    failure { echo '❗ Pipeline échouée. Consulte les logs pour diagnostiquer.' }
  }
}
