ARG FROM=ubuntu:bionic
ARG CUSTOM_PYPI_URL=""
FROM ${FROM}
LABEL source_repository="https://github.com/sapcc/rally-openstack"

ENV PYTHONDONTWRITEBYTECODE=1
ENV REQUESTS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt

RUN sed -i s/^deb-src.*// /etc/apt/sources.list

RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates wget curl && \
    wget -O /usr/local/share/ca-certificates/SAP_Global_Root_CA.crt http://aia.pki.co.sap.com/aia/SAP%20Global%20Root%20CA.crt && \
    wget -O /usr/local/share/ca-certificates/SAP_Global_Sub_CA_02.crt http://aia.pki.co.sap.com/aia/SAP%20Global%20Sub%20CA%2002.crt && \
    wget -O /usr/local/share/ca-certificates/SAP_Global_Sub_CA_04.crt http://aia.pki.co.sap.com/aia/SAP%20Global%20Sub%20CA%2004.crt && \
    wget -O /usr/local/share/ca-certificates/SAP_Global_Sub_CA_05.crt http://aia.pki.co.sap.com/aia/SAP%20Global%20Sub%20CA%2005.crt && \
    wget -O /usr/local/share/ca-certificates/SAPNetCA_G2.crt http://aia.pki.co.sap.com/aia/SAPNetCA_G2.crt && \
    update-ca-certificates

RUN apt-get install --yes sudo python python-pip python3.7 python3-distutils vim git-core && \
    pip install --upgrade pip && \
    useradd -u 65500 -m rally && \
    usermod -aG sudo rally && \
    echo "rally ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/00-rally-user

COPY . /home/rally/source
COPY etc/motd /etc/motd
WORKDIR /home/rally/source

# ensure that we have all system packages installed
RUN pip install bindep &&  apt-get install --yes $(bindep -b | tr '\n' ' ')

# Use the CCloud rally version that supports domain scoped admin tokens
RUN pip install git+https://github.com/sapcc/rally.git@ccloud  --constraint upper-constraints.txt

# Install kubernetes-entrypoint from custom pypi
RUN pip install --no-cache-dir --only-binary :all: --no-compile --extra-index-url ${CUSTOM_PYPI_URL} kubernetes-entrypoint

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
