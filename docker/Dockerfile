# 使用 ubuntu 22.04 作为基础镜像
FROM ubuntu:22.04

# 设置环境变量，防止交互式提示，ARG 构建阶段使用的变量，ENV 是运行时的环境变量
# ENV DEBIAN_FRONTEND=noninteractive
ARG DEBIAN_FRONTEND=noninteractive

# 更新系统包列表并安装 python git wget
RUN apt-get update && apt-get install -y --no-install-recommends python3.11.9 python3-pip git git-lfs wget && rm -rf /var/lib/apt/lists/*

# 复制文件
COPY . /app

# 设置工作目录
WORKDIR /app

# 端口
EXPOSE 7860

# 设置容器启动命令，运行 sh 脚本
ENTRYPOINT ["python3", "/app/main.py", "-c"]
CMD ["./docker/configuration.yaml"]

# 安装依赖
RUN pip3 install --default-timeout=100 --no-cache-dir -i https://mirrors.cloud.tencent.com/pypi/simple uv
RUN uv sync
