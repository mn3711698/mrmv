FROM bitnami/git:2.33.0 AS downloader
WORKDIR /opt
RUN git clone https://github.com/flamhaze5946/mrmv.git

FROM flamhaze5946/lite-trade:20211109.1.0.0
COPY --from=downloader /opt/mrmv /var/games/mrmv

WORKDIR /var/games/mrmv
RUN pip install -r requirements_l.txt

WORKDIR /var/games/mrmv

VOLUME ["/var/games/mrmv/config.py"]
