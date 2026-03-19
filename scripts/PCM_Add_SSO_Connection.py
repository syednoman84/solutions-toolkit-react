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


def parse_sso_connections(params):
    """Parse SSO connection entries from params.
    Keys like SSO_Connection_1, SSO_Connection_2, etc.
    Values are comma-separated: display_name, connection_name, sso_url
    """
    connections = []
    idx = 1
    while True:
        key = f"SSO_Connection_{idx}"
        if key not in params:
            break
        value = params[key]
        parts = [p.strip() for p in value.split(",")]
        if len(parts) != 3:
            logging.error(f"❌ Invalid SSO connection format for {key}: '{value}'")
            logging.error(f"   Expected format: display_name, connection_name, sso_url")
            sys.exit(1)
        connections.append({
            "display_name": parts[0],
            "connection_name": parts[1],
            "sso_url": parts[2],
        })
        idx += 1
    return connections


def update_queue_manager_settings(json_file, connections):
    """Update queueManagerUISettings.json with new SSO connections."""
    if not json_file.exists():
        logging.error(f"❌ File not found: {json_file}")
        return False

    logging.info(f"Reading {json_file}...")
    with open(json_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    if "FEATURE_CONNECTIONS" not in data:
        data["FEATURE_CONNECTIONS"] = []
    if "REACT_APP_IDP_AUTHORIZATION_URLS" not in data:
        data["REACT_APP_IDP_AUTHORIZATION_URLS"] = []

    added_count = 0
    skipped_count = 0

    for conn in connections:
        display_name = conn["display_name"]
        connection_name = conn["connection_name"]
        sso_url = conn["sso_url"]

        # Add to FEATURE_CONNECTIONS if not already present
        fc_exists = any(
            c.get("name") == connection_name for c in data["FEATURE_CONNECTIONS"]
        )
        if not fc_exists:
            data["FEATURE_CONNECTIONS"].append({
                "allowUserCreation": True,
                "displayName": display_name,
                "name": connection_name,
            })
            logging.info(f"✅ Added to FEATURE_CONNECTIONS: displayName='{display_name}', name='{connection_name}'")
        else:
            logging.info(f"⏭️ Already exists in FEATURE_CONNECTIONS: name='{connection_name}'")

        # Add to REACT_APP_IDP_AUTHORIZATION_URLS if not already present
        auth_exists = any(
            a.get("name") == display_name
            for a in data["REACT_APP_IDP_AUTHORIZATION_URLS"]
        )
        if not auth_exists:
            max_rank = max(
                (a.get("rank", 0) for a in data["REACT_APP_IDP_AUTHORIZATION_URLS"]),
                default=0,
            )
            data["REACT_APP_IDP_AUTHORIZATION_URLS"].append({
                "name": display_name,
                "rank": max_rank + 1,
                "url": sso_url,
            })
            logging.info(
                f"✅ Added to REACT_APP_IDP_AUTHORIZATION_URLS: name='{display_name}', rank={max_rank + 1}, url='{sso_url}'"
            )
            added_count += 1
        else:
            logging.info(f"⏭️ Already exists in REACT_APP_IDP_AUTHORIZATION_URLS: name='{display_name}'")
            skipped_count += 1

    # Write back
    logging.info(f"Writing updated configuration to {json_file}...")
    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
        f.write("\n")

    logging.info(f"Added {added_count} connection(s), skipped {skipped_count} duplicate(s)")
    return True


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

    # --- Parse SSO connections ---
    connections = parse_sso_connections(params)
    if not connections:
        logging.warning("⚠️ No SSO connections found (no keys matching 'SSO_Connection_<N>'). Nothing to do.")
        return

    logging.info(f"Found {len(connections)} SSO connection(s) to add:")
    for c in connections:
        logging.info(f"  - {c['display_name']} | {c['connection_name']} | {c['sso_url']}")

    try:
        # --- Step 1 - Clone destination repo ---
        dest_repo = clone_repo(params["destination_repo_github_url"], workdir / "destination")

        # --- Step 2 - Create & checkout branch ---
        run_cmd(["git", "checkout", "-b", branch_name], cwd=dest_repo)

        # --- Step 3 - Update queueManagerUISettings.json ---
        json_file = dest_repo / "app" / "template_vars" / "queueManagerUISettings.json"
        if not update_queue_manager_settings(json_file, connections):
            logging.error("❌ Failed to update queueManagerUISettings.json")
            sys.exit(1)

        # --- Step 4 - Commit & push ---
        logging.info("Committing and pushing changes")
        run_cmd(["git", "add", "."], cwd=dest_repo)
        run_cmd(["git", "commit", "-m", params.get("commit_message", "Add SSO connection configuration")], cwd=dest_repo)
        run_cmd(["git", "push", "--set-upstream", "origin", branch_name], cwd=dest_repo)

        # --- Step 5 - Create Pull Request ---
        pr_title = params.get("pr_title", "Add SSO Connection Configuration")
        pr_description = params.get("pr_description", "PR created by automation script to add SSO connection configuration")
        logging.info(f"Creating Pull Request: {branch_name} -> master")
        run_cmd(
            ["gh", "pr", "create", "--base", "master", "--head", branch_name,
             "--title", pr_title, "--body", pr_description],
            cwd=dest_repo,
        )

        logging.info("✅ SSO connection configuration added successfully.")

        # --- Print final state ---
        logging.info("\nFinal queueManagerUISettings.json:")
        with open(json_file, "r", encoding="utf-8") as f:
            logging.info(f.read())

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
