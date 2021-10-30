FROM flamhaze5946/centos7-trade:20211024.1.0.0

WORKDIR /var/games
RUN git clone https://github.com/mn3711698/mrmv
WORKDIR /var/games/mrmv
RUN cp /var/games/mrmv/strategies/base_l36.so /var/games/mrmv/strategies/base.so
RUN pip3 install -r requirements_l.txt

WORKDIR /var/games/mrmv

VOLUME ["/var/games/mrmv/config.json"]
