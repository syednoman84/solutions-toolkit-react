#!/usr/bin/env python3
import subprocess
import json
import os
import sys
from pathlib import Path

ORG = "odx-platform-configs"
GH_HOST = "git.shared.linearft.tools"
EXCLUDE_REPOS = ["ODXP-DPLOY--odx-config-platform-deploy"]

# Determine output directory: use passed argument or default to script's parent/results/scan
if len(sys.argv) > 3:
    OUTPUT_DIR = Path(sys.argv[3])
else:
    OUTPUT_DIR = Path(__file__).parent.parent / "results" / "scan"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

REPORT_FILE = OUTPUT_DIR / "product_definitions.json"
COUNT_FILE = OUTPUT_DIR / "products_count_by_tenant.txt"
TYPE_FILE = OUTPUT_DIR / "product_type_count_by_tenant.txt"


def run_command(cmd):
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return result.stdout.strip(), result.returncode


def get_repos(limit):
    cmd = f'gh repo list {ORG} --limit {limit} --json name'
    env = os.environ.copy()
    env['GH_HOST'] = GH_HOST
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, env=env)
    if result.returncode != 0:
        raise Exception(f"Failed to fetch repos. stdout: {result.stdout}, stderr: {result.stderr}")
    return [repo['name'] for repo in json.loads(result.stdout) if repo['name'] not in EXCLUDE_REPOS]


def clone_repo(repo_name, temp_dir):
    repo_url = f"https://{GH_HOST}/{ORG}/{repo_name}.git"
    repo_path = temp_dir / repo_name
    cmd = f'git clone --depth 1 {repo_url} {repo_path} 2>&1'
    run_command(cmd)
    return repo_path


def scan_product_dir(repo_path):
    products = []
    product_dir = repo_path / "product"

    if not product_dir.exists():
        return products

    for uuid_dir in product_dir.iterdir():
        if not uuid_dir.is_dir():
            continue

        def_file = uuid_dir / "definition.json"
        if def_file.exists():
            try:
                with open(def_file) as f:
                    data = json.load(f)
                    products.append({
                        "productId": data.get("productId"),
                        "productName": data.get("productName"),
                        "productType": data.get("productType"),
                        "policy": data.get("policy"),
                        "selfServiceManaged": data.get("selfServiceManaged")
                    })
            except:
                pass

    return products


def main():
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else 1000
    cleanup = sys.argv[2].lower() == 'true' if len(sys.argv) > 2 else True

    temp_dir = Path("temp_repos")
    temp_dir.mkdir(exist_ok=True)

    print(f"Fetching repositories from {ORG} (limit: {limit})...")
    sys.stdout.flush()
    repos = get_repos(limit)
    print(f"Found {len(repos)} repositories\n")
    sys.stdout.flush()

    report = {}

    for repo in repos:
        print(f"Scanning {repo}...")
        sys.stdout.flush()
        repo_path = clone_repo(repo, temp_dir)
        products = scan_product_dir(repo_path)

        if products:
            report[repo] = products
            print(f"  Found {len(products)} product(s)")
            sys.stdout.flush()

        if cleanup:
            subprocess.run(f'rm -rf {repo_path}', shell=True)

    if cleanup:
        try:
            temp_dir.rmdir()
        except OSError:
            pass
    else:
        print(f"\nRepositories kept in {temp_dir}")

    with open(REPORT_FILE, 'w') as f:
        json.dump(report, f, indent=2)

    # Generate summary report
    with open(COUNT_FILE, 'w') as f:
        f.write(f"{'S. No.':<10}{'Repo Name':<60}{'Total Products':<15}\n")
        f.write("=" * 85 + "\n")
        for i, (repo, products) in enumerate(sorted(report.items()), 1):
            f.write(f"{i:<10}{repo:<60}{len(products):<15}\n")

    # Generate product type breakdown report
    with open(TYPE_FILE, 'w') as f:
        f.write(f"{'S. No.':<10}{'Repo Name':<60}{'Product Type':<40}{'Count':<10}\n")
        f.write("=" * 120 + "\n")
        sno = 1
        for repo, products in sorted(report.items()):
            type_counts = {}
            for p in products:
                ptype = p.get('productType', 'Unknown')
                type_counts[ptype] = type_counts.get(ptype, 0) + 1
            for ptype, count in sorted(type_counts.items()):
                f.write(f"{sno:<10}{repo:<60}{ptype:<40}{count:<10}\n")
                sno += 1

    print(f"\nProduct Definitions Report is saved to {REPORT_FILE}")
    print(f"Products Count by Tenant Report is saved to {COUNT_FILE}")
    print(f"Product Type Count by Tenant Report is saved to {TYPE_FILE}")
    print(f"Total repositories with products: {len(report)}")
    print(f"Total products found: {sum(len(p) for p in report.values())}")


if __name__ == "__main__":
    main()
