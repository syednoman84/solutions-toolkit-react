import logging
import os
import shutil
import subprocess
import sys
import json
from pathlib import Path

# --- Configure logging ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)


# --- Helper Methods ---
def run_cmd(cmd, cwd=None):
    """Run shell command, stop script if fails."""
    logging.info(f"Running command: {' '.join(cmd)} (cwd={cwd or os.getcwd()})")
    try:
        subprocess.run(cmd, cwd=cwd, check=True)
    except subprocess.CalledProcessError:
        logging.error(f"❌ Command failed: {' '.join(cmd)}")
        sys.exit(1)


def clone_repo(github_url, dest_dir):
    """Clone a Git repo into dest_dir."""
    logging.info(f"Cloning repo {github_url} into {dest_dir}")
    run_cmd(["git", "clone", github_url, str(dest_dir)])
    return Path(dest_dir)


def load_params_from_txt(file_path):
    """Load key=value params from a txt file."""
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


# -----------------------------------------
# --- Main Method ---
# -----------------------------------------
def automate(params):
    # --- Decide working directory from params ---
    working_dir_param = params.get("workingDirectory", "workdir")
    workdir = Path(working_dir_param)

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

    branch_name = params.get("branchName", "branch-a")

    # --- Collect product IDs to disable ---
    product_ids = []
    for key, value in params.items():
        if key.startswith("Disable_Product_") and value.strip():
            product_ids.append(value.strip())

    if not product_ids:
        logging.warning("⚠️ No product IDs found (no keys matching 'Disable_Product_<N>=<UUID>'). Nothing to do.")
        return

    logging.info(f"Product IDs to disable: {', '.join(product_ids)}")

    try:
        # --- Step 1 - Clone destination repo ---
        dest_repo = clone_repo(params["destination_repo_github_url"], workdir / "destination")

        # --- Step 2 - Create & checkout branch ---
        run_cmd(["git", "checkout", "-b", branch_name], cwd=dest_repo)

        product_dir = dest_repo / "product"
        if not product_dir.exists():
            logging.error(f"❌ Product directory not found at {product_dir}. Is this an existing tenant repo?")
            sys.exit(1)

        # --- Step 3 - Process each product ID ---
        summary = []
        for product_id in product_ids:
            product_path = product_dir / product_id

            if not product_path.exists() or not product_path.is_dir():
                logging.error(f"❌ Product directory not found: {product_path}")
                summary.append((product_id, "NOT FOUND", None))
                continue

            definition_file = product_path / "definition.json"
            if not definition_file.exists():
                logging.error(f"❌ definition.json not found in {product_path}")
                summary.append((product_id, "NO DEFINITION", None))
                continue

            # --- Update definition.json: set selfServiceManaged to false ---
            with open(definition_file, "r", encoding="utf-8") as f:
                definition = json.load(f)

            product_name = definition.get("productName", "UNKNOWN")
            definition["selfServiceManaged"] = False

            with open(definition_file, "w", encoding="utf-8") as f:
                json.dump(definition, f, indent=2, ensure_ascii=False)
                f.write("\n")
            logging.info(f"✅ Updated selfServiceManaged=false in definition.json for '{product_name}' ({product_id})")

            # --- Update or create agentCreation.json in template_vars ---
            tv_dir = product_path / "template_vars"
            tv_dir.mkdir(exist_ok=True)

            agent_creation_file = tv_dir / "agentCreation.json"
            if agent_creation_file.exists():
                with open(agent_creation_file, "r", encoding="utf-8") as f:
                    agent_data = json.load(f)
                agent_data["enabled"] = False
                logging.info(f"✅ Updated existing agentCreation.json (enabled=false) for '{product_name}'")
            else:
                agent_data = {"enabled": False}
                logging.info(f"✅ Created agentCreation.json (enabled=false) for '{product_name}'")

            with open(agent_creation_file, "w", encoding="utf-8") as f:
                json.dump(agent_data, f, indent=2, ensure_ascii=False)
                f.write("\n")

            summary.append((product_id, "DISABLED", definition))

        # --- Check if any products were actually disabled ---
        not_found = [pid for pid, status, _ in summary if status in ("NOT FOUND", "NO DEFINITION")]
        disabled = [pid for pid, status, _ in summary if status == "DISABLED"]

        if not disabled:
            logging.error(f"\n{'='*80}")
            logging.error(f"❌ None of the provided product IDs were found in the repository!")
            logging.error(f"{'='*80}")
            logging.error(f"Repository: {params['destination_repo_github_url']}")
            logging.error(f"Product directory: {product_dir}")
            logging.error(f"Product IDs not found:")
            for pid in not_found:
                logging.error(f"  - {pid}")
            logging.error(f"\nPlease verify the product IDs exist in the destination repository's product/ directory.")
            sys.exit(1)

        if not_found:
            logging.warning(f"\n⚠️ {len(not_found)} product ID(s) were not found and skipped:")
            for pid in not_found:
                logging.warning(f"  - {pid}")
            logging.info(f"Continuing with {len(disabled)} product(s) that were successfully disabled.\n")

        # --- Step 4 - Commit & push ---
        logging.info("Committing and pushing changes")
        run_cmd(["git", "add", "."], cwd=dest_repo)
        run_cmd(["git", "commit", "-m", params.get("commit_message", "Disable PCM products by automation script")], cwd=dest_repo)
        run_cmd(["git", "push", "--set-upstream", "origin", branch_name], cwd=dest_repo)

        # --- Step 5 - Create Pull Request ---
        pr_title = params.get("pr_title", "Disable products for existing tenant")
        logging.info(f"Creating Pull Request: {branch_name} -> master")
        run_cmd(
            ["gh", "pr", "create", "--base", "master", "--head", branch_name,
             "--title", pr_title, "--body",
             "PR created by automation script to disable PCM products for existing tenant"],
            cwd=dest_repo,
        )

        logging.info("✅ Automation completed successfully.")
        if summary:
            logging.info("\nSummary of disabled products:")
            for pid, status, definition in summary:
                logging.info(f"\n{'='*80}")
                if status == "DISABLED" and definition:
                    logging.info(f"✅ {definition.get('productName', 'UNKNOWN')} ({pid})")
                    logging.info(f"{'='*80}")
                    logging.info(json.dumps(definition, indent=2, ensure_ascii=False))
                else:
                    logging.info(f"❌ {pid}: {status}")
                    logging.info(f"{'='*80}")

    finally:
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
