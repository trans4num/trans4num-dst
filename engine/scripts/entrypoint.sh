#!/bin/sh
if [ -z "${AWS_LAMBDA_RUNTIME_API}" ]; then
    # Running locally
    exec /usr/bin/aws-lambda-rie $ENV_DIR/bin/python -m awslambdaric $1
else
    # Running on AWS Lambda
    exec $ENV_DIR/bin/python -m awslambdaric $1
fi
