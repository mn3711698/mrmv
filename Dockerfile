FROM bitnami/git:2.33.0 AS downloader
WORKDIR /opt
RUN git clone https://github.com/mn3711698/mrmv.git
WORKDIR /opt/mrmv
RUN rm config.json

FROM flamhaze5946/lite-trade:20211109.1.0.0
RUN mkdir -p /var/games
COPY --from=downloader /opt/mrmv /var/games/mrmv

WORKDIR /var/games/mrmv
# RUN pip install --ignore-installed -r requirements_l.txt

VOLUME ["/var/games/mrmv/config.json"]
