FROM debian:stable
MAINTAINER  <coolsidd>
RUN apt-get update
RUN apt-get install \
    apt-transport-https \
    ca-certificates \
    curl \
    gnupg-agent \
    software-properties-common -y
RUN curl -fsSL https://download.docker.com/linux/debian/gpg | apt-key add -
RUN add-apt-repository \
   "deb [arch=amd64] https://download.docker.com/linux/debian \
   $(lsb_release -cs) \
    stable"
RUN apt-get update
RUN apt-get install docker-ce docker-ce-cli containerd.io -y
RUN apt-get install python3 python3-pip git -y
WORKDIR /project
COPY . /project
CMD ["bash"]
