pipeline {
    agent {
        dockerfile{
            args "-it -v /var/run/docker.sock:/var/run/docker.sock -v /usr/bin/docker:/usr/bin/docker --user root"
        }
   }
    stages {
        stage('build') {
            steps {
                sh "echo Build the image here"
                sh "cd /project/DOER_OS/simple-cdd"
                sh "build-simple-cdd --profiles test --keyring ../new-debian-archive-keyring.gpg"
            }
        }
    }
}
