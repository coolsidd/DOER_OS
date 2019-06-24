pipeline {
    agent {
        dockerfile{
            args "-it -v /var/run/docker.sock:/var/run/docker.sock -v /usr/bin/docker:/usr/bin/docker --user root -p 8003:80 8004:443"
        }
   }
    stages {
        stage('build') {
            steps {
                sh "echo Build the image here"
            }
        }
    }
}
