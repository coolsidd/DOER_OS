#!/bin/bash

cd ./simple-cdd
mkdir -p ./local_extras/
git archive -o ./local_extras/DOER_OS.zip HEAD --format=zip
build-simple-cdd -p test --keyring ../new-debian-archive-keyring.gpg --conf ./test.conf
