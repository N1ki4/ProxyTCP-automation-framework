pipeline {
    agent any
    stages {
        stage('Build') {
            steps {
                sh '/usr/local/bin/docker-compose run testenv bash ./project/code-assessment.sh'
            }
        }
    }
}
