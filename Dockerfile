FROM ubuntu:22.04
ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update &&     apt-get install -y python3 python3-pip curl openssh-server sudo &&     pip3 install -U discord.py &&     apt-get clean

WORKDIR /app
COPY . /app
CMD ["python3", "bot.py"]
