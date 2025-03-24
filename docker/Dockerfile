# Use Ubuntu as the base image for better compatibility
FROM ubuntu:22.04
 
# Define build arguments
ARG SPARK_VERSION=3.4.4
ARG HADOOP_VERSION=3.3.6
ARG SPARK_UID=185
ARG SPARK_GID=999
 
# Set environment variables
ENV SPARK_HOME=/opt/spark
ENV HADOOP_HOME=/opt/hadoop
ENV PATH="$SPARK_HOME/bin:$HADOOP_HOME/bin:$PATH"
ENV PYTHONUNBUFFERED=1
 
# Install system dependencies, Python 3, dos2unix, and aria2 for faster downloads
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y \
   bash curl aria2 openjdk-11-jdk libstdc++6 glibc-source krb5-user libnss3 \
   tini python3 python3-pip python3-setuptools dos2unix \
   && rm -rf /var/lib/apt/lists/*
 
# Ensure Python3 is the default
RUN ln -s /usr/bin/python3 /usr/bin/python
 
# Download and install Apache Spark using aria2c (faster parallel downloads)
RUN aria2c -x 16 -s 16 -o /tmp/spark-${SPARK_VERSION}-bin-hadoop3.tgz \
   "https://mirrors.ocf.berkeley.edu/apache/spark/spark-${SPARK_VERSION}/spark-${SPARK_VERSION}-bin-hadoop3.tgz" && \
   tar -xzf /tmp/spark-${SPARK_VERSION}-bin-hadoop3.tgz -C /opt/ && \
   ln -s /opt/spark-${SPARK_VERSION}-bin-hadoop3 ${SPARK_HOME} && \
   rm -f /tmp/spark-${SPARK_VERSION}-bin-hadoop3.tgz
 
# Download and install Hadoop using aria2c (faster parallel downloads)
RUN aria2c -x 16 -s 16 -o /tmp/hadoop-${HADOOP_VERSION}.tar.gz \
   "https://mirrors.ocf.berkeley.edu/apache/hadoop/common/hadoop-${HADOOP_VERSION}/hadoop-${HADOOP_VERSION}.tar.gz" && \
   tar -xzf /tmp/hadoop-${HADOOP_VERSION}.tar.gz -C /opt/ && \
   ln -s /opt/hadoop-${HADOOP_VERSION} ${HADOOP_HOME} && \
   rm -f /tmp/hadoop-${HADOOP_VERSION}.tar.gz
 
# Set Spark classpath
ENV SPARK_DIST_CLASSPATH="$HADOOP_HOME/etc/hadoop:$HADOOP_HOME/share/hadoop/common/lib/*:$HADOOP_HOME/share/hadoop/common/*:$HADOOP_HOME/share/hadoop/hdfs:$HADOOP_HOME/share/hadoop/hdfs/lib/*:$HADOOP_HOME/share/hadoop/hdfs/*:$HADOOP_HOME/share/hadoop/mapreduce/*:$HADOOP_HOME/share/hadoop/yarn:$HADOOP_HOME/share/hadoop/yarn/lib/*:$HADOOP_HOME/share/hadoop/yarn/*:$HADOOP_HOME/share/hadoop/tools/lib/*"
 
# Install additional Python packages for Spark
RUN pip3 install --no-cache-dir --upgrade pip setuptools wheel && \
   pip3 install --no-cache-dir pygeohash requests python-dotenv geohash2
# Copy necessary files
COPY ./entrypoint.sh /opt/
COPY ./dist/sparkbasics-1.0.0-py3.10.egg /opt/
COPY --from=extra-source ./src /opt/src
 
# Convert entrypoint.sh to UNIX line endings
RUN dos2unix /opt/entrypoint.sh
 
# Ensure scripts are executable
RUN chmod +x /opt/entrypoint.sh
 
# Ensure tini is installed and create a symlink for compatibility
RUN ln -s /usr/bin/tini /sbin/tini
 
# Create group and user for Spark
RUN groupadd -g $SPARK_GID spark && \
   useradd -m -u $SPARK_UID -g $SPARK_GID spark
 
# Set working directory
WORKDIR ${SPARK_HOME}/work-dir
 
# Set ownership of necessary directories
RUN mkdir -p /opt/spark/work-dir && \
   chown -R spark:spark /opt/spark/work-dir && \
   chmod -R 777 /opt/spark/work-dir
RUN chown spark:spark /opt/sparkbasics-*.egg && chmod 644 /opt/sparkbasics-*.egg
 
# Switch to non-root user
USER ${SPARK_UID}
 
# Set entrypoint
ENTRYPOINT [ "/usr/bin/tini", "--", "/opt/entrypoint.sh" ]