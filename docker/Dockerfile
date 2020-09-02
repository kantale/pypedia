# see also: https://hub.docker.com/r/kantale/pypedia 

FROM continuumio/anaconda:latest
MAINTAINER Alexandros Kanterakis <alexandros.kanterakis@gmail.com>

RUN apt-get -y update && apt-get install -y \
    git \
    gcc \
    g++ \
    zlibc zlib1g zlib1g-dev \
    xpdf \
    vim \
    texlive-latex-extra \
    texlive-latex-base texmaker texlive-fonts-recommended texlive-science texlive-publishers texlive-fonts-extra texlive-math-extra \
    dvipng

RUN echo "y" | conda update conda 

RUN pip install \
    brewer2mpl \
    biopython \
    pybedtools

RUN git clone https://github.com/kantale/pypedia.git ; cd pypedia; python setup.py install ; cd


CMD ["/bin/bash"]

