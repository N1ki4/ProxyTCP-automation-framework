pipeline {
    agent any
    stages {
        stage('Build') {
            steps {
                sh 'docker-compose run testenv bash ./project/code-assessment.sh'
            }
        }
    }
}
