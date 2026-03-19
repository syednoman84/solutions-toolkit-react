import logging
import os
import shutil
import subprocess
import sys
import uuid
import json
import re
from pathlib import Path

# --- Configure logging ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)

# --- Helper Methods Start---
def run_cmd(cmd, cwd=None):
    """Run shell command, stop script if fails."""
    logging.info(f"Running command: {' '.join(cmd)} (cwd={cwd or os.getcwd()})")
    try:
        subprocess.run(cmd, cwd=cwd, check=True)
    except subprocess.CalledProcessError:
        logging.error(f"❌ Command failed: {' '.join(cmd)}")
        sys.exit(1)


def clone_repo(github_url, dest_dir, tag=None):
    """Clone a Git repo into dest_dir, optionally checkout a tag."""
    logging.info(f"Cloning repo {github_url} into {dest_dir}")
    run_cmd(["git", "clone", github_url, str(dest_dir)])
    if tag:
        logging.info(f"Checking out tag: {tag}")
        run_cmd(["git", "checkout", tag], cwd=dest_dir)
    return Path(dest_dir)


def copy_contents(src, dst):
    """Copy files/dirs from src to dst, replacing if exists."""
    src = Path(src)
    dst = Path(dst)
    logging.info(f"Copying {src} → {dst}")
    try:
        if src.is_dir():
            if dst.exists():
                shutil.rmtree(dst)
            shutil.copytree(src, dst)
        else:
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
    except Exception as e:
        logging.error(f"❌ Failed to copy {src} to {dst}: {e}")
        sys.exit(1)


def load_params_from_txt(file_path):
    """Load key=value params from a txt file (preserves file order)."""
    logging.info(f"Loading parameters from {file_path}")
    params = {}
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" not in line:
                logging.error(f"❌ Invalid line in params file: {line}")
                sys.exit(1)
            key, value = line.split("=", 1)
            params[key.strip()] = value.strip()
    return params


def parse_map_param(param_str):
    """Parse param string like: k1:v1,k2:v2 into dict"""
    mapping = {}
    if not param_str:
        return mapping
    for entry in param_str.split(","):
        entry = entry.strip()
        if not entry:
            continue
        if ":" not in entry:
            logging.error(f"❌ Invalid mapping entry: '{entry}'. Expected format 'key:value'")
            sys.exit(1)
        k, v = entry.split(":", 1)
        mapping[k.strip()] = v.strip()
    return mapping
# --- Helper Methods End---

PRODUCT_KEY_REGEX = re.compile(r"^(?P<ptype>.+)_Product_(?P<idx>\d+)$")

# -----------------------------------------
# --- Main Method ---
# -----------------------------------------
def automate(params):
    # --- Decide working directory from params ---
    working_dir_param = params.get("workingDirectory", "workdir")
    workdir = Path(working_dir_param)
    
    # If relative path, resolve from script's parent directory (project root)
    if not workdir.is_absolute():
        script_parent = Path(__file__).parent.parent
        workdir = (script_parent / workdir).resolve()
    else:
        workdir = workdir.expanduser().absolute()

    if workdir.exists():
        logging.info(f"Cleaning existing workdir at {workdir}")
        shutil.rmtree(workdir)
    workdir.mkdir(parents=True, exist_ok=True)
    logging.info(f"Using workdir at {workdir}")

    # --- Branch name from params ---
    branch_name = params.get("branchName", "branch-a")

    # --- Load mappings from params.txt ---
    TEMPLATE_PATHS = parse_map_param(params.get("TEMPLATE_PATHS", ""))
    PRODUCT_TYPE_MAP = parse_map_param(params.get("PRODUCT_TYPE_MAP", ""))
    PRODUCT_TYPE_NAME_MAP = parse_map_param(params.get("PRODUCT_TYPE_NAME_MAP", ""))
    PRODUCT_POLICY_MAP = parse_map_param(params.get("PRODUCT_POLICY_MAP", ""))

    # --- Discover products dynamically from params (fully dynamic types) ---
    # Build a list of (ptype, idx, key, name) for stable ordering
    discovered = []
    for key, product_name in params.items():
        m = PRODUCT_KEY_REGEX.match(key)
        if not m:
            continue
        ptype = m.group("ptype")
        idx = int(m.group("idx"))
        discovered.append((ptype, idx, key, product_name))

    if not discovered:
        logging.warning("⚠️ No products found (no keys matching '<Type>_Product_<N>=<Name>'). Nothing to do.")
        # Still continue to push baseline files in case that's desired.

    # Sort by product type then numeric index for deterministic behavior
    discovered.sort(key=lambda t: (t[0], t[1]))

    # --- Preflight validation: ensure all discovered ptypes have mappings ---
    discovered_types = sorted({ptype for ptype, _, _, _ in discovered})
    if discovered_types:
        logging.info(f"Discovered product types: {', '.join(discovered_types)}")

    missing_template = [t for t in discovered_types if t not in TEMPLATE_PATHS]
    missing_type_map = [t for t in discovered_types if t not in PRODUCT_TYPE_MAP]
    missing_type_name = [t for t in discovered_types if t not in PRODUCT_TYPE_NAME_MAP]
    missing_policy = [t for t in discovered_types if t not in PRODUCT_POLICY_MAP]

    errs = []
    if missing_template:
        errs.append(f"TEMPLATE_PATHS missing keys: {', '.join(missing_template)}")
    if missing_type_map:
        errs.append(f"PRODUCT_TYPE_MAP missing keys: {', '.join(missing_type_map)}")
    if missing_type_name:
        errs.append(f"PRODUCT_TYPE_NAME_MAP missing keys: {', '.join(missing_type_name)}")
    if missing_policy:
        errs.append(f"PRODUCT_POLICY_MAP missing keys: {', '.join(missing_policy)}")

    if errs:
        logging.error("❌ Mapping validation failed:\n  - " + "\n  - ".join(errs))
        sys.exit(1)

    try:
        # --- Step 1 - Clone destination repo into 'destination' ---
        dest_repo = clone_repo(params["destination_repo_github_url"], workdir / "destination")

        # --- Step 2 - Create & checkout branch ---
        run_cmd(["git", "checkout", "-b", branch_name], cwd=dest_repo)

        # --- Step 3 - Clone static files repo into 'static-repo' ---
        static_repo = clone_repo(params["static_files_repo_github_url"], workdir / "static-repo")

        # --- Step 4 - Copy baseline files into destination repo ---
        copy_contents(static_repo / "static-files/app", dest_repo / "app")
        copy_contents(static_repo / "static-files/env", dest_repo / "env")
        copy_contents(static_repo / "static-files/.gitignore", dest_repo / ".gitignore")

        # --- Step 5 - Replace placeholders in env files using tenant values ---
        tenant_domain = params.get("tenant-domain")
        tenant_id = params.get("tenant-id")

        if not tenant_domain or not tenant_id:
            logging.error("❌ tenant-domain or tenant-id not provided in params.txt")
            sys.exit(1)

        env_dir = dest_repo / "env"
        for filename in ["serenityprdpr.json", "serenityprod1.json"]:
            file_path = env_dir / filename
            if file_path.exists():
                logging.info(f"Updating placeholders in {file_path}")
                content = file_path.read_text(encoding="utf-8")
                content = content.replace("<tenant-domain>", tenant_domain)
                content = content.replace("<tenant-id>", tenant_id)
                file_path.write_text(content, encoding="utf-8")
            else:
                logging.warning(f"⚠️ Expected env file not found: {file_path}")

        # --- Step 6: Create product directory ---
        product_dir = dest_repo / "product"
        product_dir.mkdir(exist_ok=True)
        logging.info(f"Created product directory at {product_dir}")

        # --- Step 7 - Clone template vars repo ---
        template_vars_tag = params.get("template_vars_tag")
        template_vars_repo = clone_repo(params["template_vars_github_url"], workdir / "template_vars", template_vars_tag)

        # --- Step 8/9 - Process products (dynamic) ---
        summary = []
        for ptype, idx, key, product_name in discovered:
            product_type_code = PRODUCT_TYPE_MAP[ptype]
            product_type_name = PRODUCT_TYPE_NAME_MAP[ptype]
            policy_name = PRODUCT_POLICY_MAP[ptype]
            template_rel_path = TEMPLATE_PATHS[ptype]

            # Step 10 - Create Product Directory with random UUID
            product_uuid = str(uuid.uuid4())
            product_path = product_dir / product_uuid
            product_path.mkdir()
            logging.info(f"Created {ptype} product directory {product_path} for '{product_name}' (#{idx})")

            # Step 11 - Copy template vars into product directory
            template_path = template_vars_repo / template_rel_path
            if template_path.exists():
                tv_dir = product_path / "template_vars"
                tv_dir.mkdir()
                copy_contents(template_path, tv_dir)
            else:
                logging.warning(f"⚠️ Template vars path not found for {ptype}: {template_path}")

            # Step 12 - Create definition.json
            definition = {
                "productId": product_uuid,
                "productName": product_name,
                "productType": product_type_code,
                "productTypeName": product_type_name,
                "policy": policy_name,
                "selfServiceManaged": True
            }
            with open(product_path / "definition.json", "w", encoding="utf-8") as f:
                json.dump(definition, f, indent=2, ensure_ascii=False)
            logging.info(f"Created definition.json for {product_name}")

            summary.append((ptype, product_name, product_path))

        # --- Step 13 - Commit & push ---
        logging.info("Committing and pushing changes")
        run_cmd(["git", "add", "."], cwd=dest_repo)
        run_cmd(["git", "commit", "-m", params.get("commit_message", "PCM products created by automation script")], cwd=dest_repo)
        run_cmd(["git", "push", "--set-upstream", "origin", branch_name], cwd=dest_repo)

        # --- Step 14 - Create Pull Request ---
        pr_title = params.get("pr_title", "Automated setup script changes")
        logging.info(f"Creating Pull Request: {branch_name} -> master")
        run_cmd(["gh", "pr", "create", "--base", "master", "--head", branch_name, "--title", pr_title, "--body", "PR created by automation script to setup new PCM products"], cwd=dest_repo)

        logging.info("✅ Automation completed successfully.")
        if summary:
            logging.info("Summary of created products:")
            for ptype, pname, ppath in summary:
                definition_file = ppath / "definition.json"
                with open(definition_file, "r", encoding="utf-8") as f:
                    definition = json.load(f)
                logging.info(f"\n{'='*80}")
                logging.info(f"{ptype}: {pname}")
                logging.info(f"Path: {ppath}")
                logging.info(f"{'='*80}")
                logging.info(json.dumps(definition, indent=2, ensure_ascii=False))

    finally:
        # --- Step 14 - Conditionally delete everything from working directory ---
        cleanup = params.get("cleanup_after_run", "false").lower()
        if cleanup == "true":
            logging.info(f"Cleaning up workdir at {workdir}")
            shutil.rmtree(workdir)
        else:
            logging.info(f"Keeping workdir at {workdir} (set cleanup_after_run=true to delete)")


if __name__ == "__main__":
    script_dir = Path(__file__).parent.parent
    params_file = script_dir / "params" / "params.txt"

    if not params_file.exists():
        logging.error(f"❌ Parameters file not found: {params_file}")
        sys.exit(1)

    params = load_params_from_txt(params_file)
    automate(params)
