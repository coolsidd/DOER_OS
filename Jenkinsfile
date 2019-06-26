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
                sh "cp -a /usr/share/keyrings/debian-archive-keyring.gpg ./new-debian-archive-keyring.gpg"
                sh "cd ./simple-cdd"
                sh "gpg --no-default-keyring --keyring=../new-debian-archive-keyring.gpg --delete-key \"6FB2A1C265FFB764\""
                sh "build-simple-cdd --profiles test --keyring ../new-debian-archive-keyring.gpg"
            }
        }
    }
}
