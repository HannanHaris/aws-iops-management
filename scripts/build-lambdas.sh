#!/usr/bin/env bash
# Builds lambda1.zip / lambda2.zip from the Python sources.
# Run this before `terraform plan` / `apply`.
set -euo pipefail

cd "$(dirname "$0")/../modules/lambda"
for n in lambda1 lambda2; do
  rm -f "${n}.zip"
  zip -q -j "${n}.zip" "${n}.py"
  echo "Built modules/lambda/${n}.zip"
done
