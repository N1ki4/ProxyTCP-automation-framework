timestamps {
    node () {
        cleanWs()
    	stage ('Checkout') {
     	 checkout([$class: 'GitSCM', branches: [[name: '*/develop']], doGenerateSubmoduleConfigurations: false, extensions: [], submoduleCfg: [], userRemoteConfigs: [[credentialsId: '', url: 'https://github.com/YuriiShp/proxytcp.git']]]) 
    	}
    }
}

pipeline {
    agent any

    stages {
        stage('Pull Testframework'){
            steps {
                sh "git clone https://github.com/YuriiShp/ProxyTCP-automation-framework.git"
            }
        }
        stage ('Build Environment'){
            steps{
                sh "sudo docker-compose -f ./ProxyTCP-automation-framework/docker-compose.yaml run --rm testenv pyats run job /pyats/project/src/jobs/build_environment.py --service-key /share/service-acc2-key.json"
            }
        }
        stage ('Run Tests'){
            steps{
                sh "sudo docker-compose -f ./ProxyTCP-automation-framework/docker-compose.yaml run --rm testenv pyats run job /pyats/project/src/jobs/smoke.py --testbed-file /pyats/project/src/testbed.yaml"
            }
        }
    }
    post {
        always {
            sh "sudo docker-compose -f ./ProxyTCP-automation-framework/docker-compose.yaml run --rm testenv pyats run job /pyats/project/src/jobs/destroy_environment.py --service-key /share/service-acc2-key.json"
        }
        success {
            emailext body: """SUCCESS: Job '${env.JOB_NAME} [${env.BUILD_NUMBER}]':
                Check logs at ${env.BUILD_URL}""",
                subject: "SUCCESS: Job '${env.JOB_NAME} [${env.BUILD_NUMBER}]'",
                attachLog: true,
                to: '$DEFAULT_RECIPIENTS'
        }
        failure {
            emailext body: """FAILURE: Job '${env.JOB_NAME} [${env.BUILD_NUMBER}]':
                Check logs at ${env.BUILD_URL}""",
                subject: "FAILURE: Job '${env.JOB_NAME} [${env.BUILD_NUMBER}]'",
                attachLog: true,
                to: '$DEFAULT_RECIPIENTS'
        }
    }
}