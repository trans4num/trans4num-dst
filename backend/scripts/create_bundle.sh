#!/bin/bash
set -euo pipefail

output_path="${1:-dist/backend-bundle.zip}"
repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
backend_root="${repo_root}/backend"
common_root="${repo_root}/common"
bundle_root="$(mktemp -d)"
output_dir="$(cd "$(dirname "${output_path}")" && pwd)"
output_file="${output_dir}/$(basename "${output_path}")"

cleanup() {
  rm -rf "${bundle_root}"
}

trap cleanup EXIT

mkdir -p "$(dirname "${output_path}")"
rm -f "${output_file}"

# Bundle backend at the archive root so it unpacks directly into /trans4num.
cp -a "${backend_root}/." "${bundle_root}/"
rm -rf "${bundle_root}/common"
mkdir -p "${bundle_root}/common"
cp -a "${common_root}/." "${bundle_root}/common/"

# The source tree keeps common beside backend; the bundle keeps it inside the
# application root, so update Pixi's local dependency path for runtime.
sed -i 's|path = "../common"|path = "common"|' "${bundle_root}/pixi.toml"
sed -i 's|pypi: ../common|pypi: common|g' "${bundle_root}/pixi.lock"

# Keep runtime secrets and local caches out of the deployment artifact.
rm -f "${bundle_root}/config.json"
rm -rf "${bundle_root}/.pixi"
rm -rf "${bundle_root}/dist"
rm -rf "${bundle_root}/scripts"
rm -rf "${bundle_root}/common/"*.egg-info
find "${bundle_root}" -type d -name "__pycache__" -prune -exec rm -rf {} +
find "${bundle_root}" -type f \( -name "*.pyc" -o -name "*.pyo" \) -delete

(
  cd "${bundle_root}"
  zip -qr "${output_file}" .
)
