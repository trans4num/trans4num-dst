#!/usr/bin/env bash
set -euo pipefail

repo_root="$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
region_id="${1:-}"

if [[ -z "$region_id" ]]; then
    printf 'Usage: %s REGION_UUID\n' "$(basename "$0")" >&2
    exit 2
fi

exec "$repo_root/trans4num" engine --region "$region_id"
