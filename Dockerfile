ARG FROM=ubuntu:xenial
FROM ${FROM}

ENV PYTHONDONTWRITEBYTECODE=1
ENV REQUESTS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt

RUN sed -i s/^deb-src.*// /etc/apt/sources.list

RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates wget curl && \
    wget -O /usr/local/share/ca-certificates/SAP_Global_Root_CA.crt http://aia.pki.co.sap.com/aia/SAP%20Global%20Root%20CA.crt && \
    wget -O /usr/local/share/ca-certificates/SAP_Global_Sub_CA_02.crt http://aia.pki.co.sap.com/aia/SAP%20Global%20Sub%20CA%2002.crt && \
    wget -O /usr/local/share/ca-certificates/SAP_Global_Sub_CA_04.crt http://aia.pki.co.sap.com/aia/SAP%20Global%20Sub%20CA%2004.crt && \
    wget -O /usr/local/share/ca-certificates/SAP_Global_Sub_CA_05.crt http://aia.pki.co.sap.com/aia/SAP%20Global%20Sub%20CA%2005.crt && \
    wget -O /usr/local/share/ca-certificates/SAPNetCA_G2.crt http://aia.pki.co.sap.com/aia/SAPNetCA_G2.crt && \
    update-ca-certificates && \
    curl -sLo /usr/local/bin/kubernetes-entrypoint https://github.wdf.sap.corp/d062284/k8s-entrypoint-build/releases/download/f52d105/kubernetes-entrypoint && \
    chmod +x /usr/local/bin/kubernetes-entrypoint

RUN apt-get install --yes sudo python python-pip vim git-core && \
    pip install --upgrade pip && \
    useradd -u 65500 -m rally && \
    usermod -aG sudo rally && \
    echo "rally ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/00-rally-user

COPY . /home/rally/source
COPY etc/motd /etc/motd
WORKDIR /home/rally/source

# add this and below command will run without cache
ARG CACHEBUST=1

# Use the CCloud rally version that supports domain scoped admin tokens
RUN pip install git+https://github.com/sapcc/rally.git@ccloud

# Install CCloud manila tempest plugin
RUN git clone -b ccloud --single-branch https://github.com/sapcc/manila-tempest-plugin.git
RUN pip install -e manila-tempest-plugin/ \
  -c https://raw.githubusercontent.com/sapcc/requirements/stable/rocky-m3/upper-constraints.txt \
  -r manila-tempest-plugin/requirements.txt \
  -r manila-tempest-plugin/test-requirements.txt

RUN pip install . --constraint upper-constraints.txt && \
    mkdir /etc/rally && \
    echo "[database]" > /etc/rally/rally.conf && \
    echo "connection=sqlite:////home/rally/data/rally.db" >> /etc/rally/rally.conf
RUN echo '[ ! -z "$TERM" -a -r /etc/motd ] && cat /etc/motd' >> /etc/bash.bashrc
# Cleanup pip
RUN rm -rf /root/.cache/

USER rally
ENV HOME /home/rally
RUN mkdir -p /home/rally/data && rally db recreate

# Docker volumes have specific behavior that allows this construction to work.
# Data generated during the image creation is copied to volume only when it's
# attached for the first time (volume initialization)
VOLUME ["/home/rally/data"]
ENTRYPOINT ["rally"]
