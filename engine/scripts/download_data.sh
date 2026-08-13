#!/bin/bash
set -euo pipefail

: "${TRANS4NUM_SOURCE_DATA_URI:?Set TRANS4NUM_SOURCE_DATA_URI to the source S3 URI}"

source_data_uri="${TRANS4NUM_SOURCE_DATA_URI%/}"

aws s3 cp "${source_data_uri}/Fields2023_DataDST_May2025.csv" data/Fields2023_DataDST_May2025.csv
aws s3 cp "${source_data_uri}/Marker_2023_n61489.zip" data/Marker_2023_n61489.zip
