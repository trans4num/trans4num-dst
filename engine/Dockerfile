FROM public.ecr.aws/lambda/python:3.12

ARG MICROMAMBA_DIR=/opt/micromamba
ENV ENV_DIR=/opt/conda-env

# Install dependencies for micromamba
RUN dnf update -y && dnf install -y tar bzip2

# Install micromamba
RUN mkdir --parents $MICROMAMBA_DIR
RUN curl -Ls https://micro.mamba.pm/api/micromamba/linux-64/latest \
    | tar -xvj --directory $MICROMAMBA_DIR bin/micromamba
ENV PATH="$MICROMAMBA_DIR/bin:${PATH}"
ENV MAMBA_ROOT_PREFIX=$MICROMAMBA_DIR

# Create conda environment and install dependencies
COPY engine/environment.yml .
RUN micromamba create -f environment.yml -p $ENV_DIR \
    && micromamba clean --all --yes
RUN $ENV_DIR/bin/pip install awslambdaric

# Install shared common package used by the engine.
COPY common/ /opt/trans4num/common/
RUN $ENV_DIR/bin/pip install /opt/trans4num/common

# In order for gdal to read projections, since environment is never directly activated.
ENV PROJ_LIB="${ENV_DIR}/share/proj"

# Setup AWS Lambda runtime environment for local testing
ADD https://github.com/aws/aws-lambda-runtime-interface-emulator/releases/latest/download/aws-lambda-rie /usr/bin/aws-lambda-rie
RUN chmod 755 /usr/bin/aws-lambda-rie
COPY engine/scripts/entrypoint.sh /entrypoint.sh
RUN ["chmod", "+x", "/entrypoint.sh"]
ENTRYPOINT [ "/entrypoint.sh" ]

# Copy source code and set Lambda handler function
COPY engine/src/ .
CMD [ "handler.handler" ]
