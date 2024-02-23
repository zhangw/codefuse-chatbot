From python:3.9.18-bookworm

WORKDIR /home/user

COPY ./requirements.txt /home/user/docker_requirements.txt

RUN sed -i 's/deb.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list.d/debian.sources
RUN apt-get update
RUN apt-get install -y iputils-ping telnetd net-tools vim tcpdump
# RUN echo telnet stream tcp nowait telnetd /usr/sbin/tcpd /usr/sbin/in.telnetd /etc/inetd.conf
# RUN service inetutils-inetd start
# service inetutils-inetd status

RUN wget https://oss-cdn.nebula-graph.com.cn/package/3.6.0/nebula-graph-3.6.0.ubuntu1804.amd64.deb
RUN dpkg -i nebula-graph-3.6.0.ubuntu1804.amd64.deb
RUN wget -O /usr/local/bin/nebula-console https://github.com/vesoft-inc/nebula-console/releases/download/v3.6.0/nebula-console-linux-amd64-v3.6.0 && \
    chmod +x /usr/local/bin/nebula-console

RUN pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple
RUN pip install -r /home/user/docker_requirements.txt

CMD ["bash"]
