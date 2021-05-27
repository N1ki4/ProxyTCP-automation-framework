pipeline {
    agent any
    stages {
        stage('Build') {
            steps {
                sh 'sudo docker-compose run testenv bash ./project/code-assessment.sh'
            }
        }
    }
}
