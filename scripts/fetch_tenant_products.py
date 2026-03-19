#!/usr/bin/env python3
"""Fetch all product definitions from a single tenant repository.

Usage: python3 fetch_tenant_products.py <tenant_id> [branch_name]

Clones the tenant repo, checks out the specified branch (default: master),
scans product/*/definition.json files, and prints the results as a JSON array to stdout.
"""
import subprocess
import json
import sys
import tempfile
import shutil
from pathlib import Path

GH_HOST = "git.shared.linearft.tools"
ORG = "odx-platform-configs"


def main():
    if len(sys.argv) < 2:
        print("Usage: fetch_tenant_products.py <tenant_id>", file=sys.stderr)
        sys.exit(1)

    tenant_id = sys.argv[1].strip()
    branch_name = sys.argv[2].strip() if len(sys.argv) > 2 else "master"
    repo_name = f"ODXP-DPLOY--odx-config-{tenant_id}-deploy"
    repo_url = f"https://{GH_HOST}/{ORG}/{repo_name}.git"

    temp_dir = tempfile.mkdtemp()
    repo_path = Path(temp_dir) / repo_name

    try:
        clone_cmd = f'git clone {repo_url} {repo_path}'
        if branch_name == "master":
            clone_cmd = f'git clone --depth 1 {repo_url} {repo_path}'

        result = subprocess.run(
            clone_cmd, shell=True, capture_output=True, text=True
        )
        if result.returncode != 0:
            print(f"Failed to clone repository: {result.stderr.strip()}", file=sys.stderr)
            sys.exit(1)

        if branch_name != "master":
            checkout = subprocess.run(
                f'git checkout {branch_name}',
                shell=True, capture_output=True, text=True, cwd=str(repo_path)
            )
            if checkout.returncode != 0:
                print(f"Failed to checkout branch '{branch_name}': {checkout.stderr.strip()}", file=sys.stderr)
                sys.exit(1)

        products = []
        product_dir = repo_path / "product"

        if product_dir.exists():
            for uuid_dir in sorted(product_dir.iterdir()):
                if not uuid_dir.is_dir():
                    continue
                def_file = uuid_dir / "definition.json"
                if def_file.exists():
                    try:
                        with open(def_file) as f:
                            data = json.load(f)
                            products.append({
                                "productId": data.get("productId", ""),
                                "productName": data.get("productName", ""),
                                "productType": data.get("productType", ""),
                                "policy": data.get("policy", ""),
                                "selfServiceManaged": data.get("selfServiceManaged", "")
                            })
                    except (json.JSONDecodeError, IOError):
                        pass

        print(json.dumps(products))
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    main()
