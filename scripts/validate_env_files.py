import json
import re
import sys
from pathlib import Path

def load_params(file_path):
    """Load parameters from params.txt"""
    params = {}
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            params[key.strip()] = value.strip()
    return params

def validate_env_file(file_path, tenant_domain, tenant_id, baseline_path):
    """Validate that env file matches baseline with replaced placeholders"""
    if not file_path.exists():
        return {"status": "missing", "message": f"File not found: {file_path}"}
    
    if not baseline_path.exists():
        return {"status": "missing", "message": f"Baseline file not found: {baseline_path}"}
    
    try:
        # Read actual file from remote branch
        actual_content = file_path.read_text(encoding="utf-8")
        actual_data = json.loads(actual_content)
        
        # Read baseline and replace placeholders
        baseline_content = baseline_path.read_text(encoding="utf-8")
        expected_content = baseline_content.replace("<tenant-domain>", tenant_domain)
        expected_content = expected_content.replace("<tenant-id>", tenant_id)
        expected_data = json.loads(expected_content)
        
        # Compare JSON structures
        if actual_data == expected_data:
            return {
                "status": "success",
                "match": True,
                "message": "File matches baseline with correct tenant values"
            }
        else:
            # Find differences
            differences = []
            
            def compare_json(path, expected, actual, diffs):
                if type(expected) != type(actual):
                    diffs.append(f"{path}: Type mismatch - expected {type(expected).__name__}, got {type(actual).__name__}")
                    return
                
                if isinstance(expected, dict):
                    all_keys = set(expected.keys()) | set(actual.keys())
                    for key in all_keys:
                        if key not in expected:
                            diffs.append(f"{path}.{key}: Extra key in actual file")
                        elif key not in actual:
                            diffs.append(f"{path}.{key}: Missing key in actual file")
                        else:
                            compare_json(f"{path}.{key}" if path else key, expected[key], actual[key], diffs)
                elif isinstance(expected, list):
                    if len(expected) != len(actual):
                        diffs.append(f"{path}: Array length mismatch - expected {len(expected)}, got {len(actual)}")
                    else:
                        for i, (exp_item, act_item) in enumerate(zip(expected, actual)):
                            compare_json(f"{path}[{i}]", exp_item, act_item, diffs)
                else:
                    if expected != actual:
                        diffs.append(f"{path}: Value mismatch - expected '{expected}', got '{actual}'")
            
            compare_json("", expected_data, actual_data, differences)
            
            return {
                "status": "success",
                "match": False,
                "differences": differences[:10],  # Limit to first 10 differences
                "total_differences": len(differences)
            }
    except json.JSONDecodeError as e:
        return {
            "status": "error",
            "message": f"Invalid JSON: {e}"
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error: {e}"
        }

if __name__ == "__main__":
    script_dir = Path(__file__).parent.parent
    params_file = script_dir / "params" / "params.txt"
    
    if not params_file.exists():
        print(f"❌ Parameters file not found: {params_file}")
        sys.exit(1)
    
    params = load_params(params_file)
    
    # Create validation directory
    validation_dir = script_dir / "validation"
    if validation_dir.exists():
        print(f"Cleaning existing validation directory...")
        import shutil
        shutil.rmtree(validation_dir)
    validation_dir.mkdir(parents=True, exist_ok=True)
    
    # Clone the remote branch for validation
    dest_repo_url = params.get('destination_repo_github_url')
    branch_name = params.get('branchName', 'master')
    
    if not dest_repo_url:
        print("❌ destination_repo_github_url not found in params.txt")
        sys.exit(1)
    
    print(f"📥 Cloning remote branch '{branch_name}' from {dest_repo_url}...")
    dest_repo = validation_dir / "destination"
    
    import subprocess
    try:
        subprocess.run(["git", "clone", "-b", branch_name, dest_repo_url, str(dest_repo)], check=True, capture_output=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to clone branch '{branch_name}': {e.stderr.decode()}")
        sys.exit(1)
    
    # Clone static files repo for baseline comparison
    static_repo_url = params.get('static_files_repo_github_url')
    if not static_repo_url:
        print("❌ static_files_repo_github_url not found in params.txt")
        sys.exit(1)
    
    print(f"📥 Cloning static files repo from {static_repo_url}...")
    static_repo = validation_dir / "static-repo"
    
    try:
        subprocess.run(["git", "clone", static_repo_url, str(static_repo)], check=True, capture_output=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to clone static files repo: {e.stderr.decode()}")
        sys.exit(1)
    
    env_dir = dest_repo / "env"
    baseline_env_dir = static_repo / "static-files" / "env"
    
    tenant_domain = params.get("tenant-domain")
    tenant_id = params.get("tenant-id")
    
    if not tenant_domain or not tenant_id:
        print("❌ tenant-domain or tenant-id not found in params.txt")
        sys.exit(1)
    
    if not env_dir.exists():
        print(f"❌ Env directory not found: {env_dir}")
        sys.exit(1)
    
    print(f"\n{'='*80}")
    print(f"Environment Files Validation Report")
    print(f"{'='*80}")
    print(f"Expected tenant-domain: {tenant_domain}")
    print(f"Expected tenant-id: {tenant_id}")
    print(f"Env directory: {env_dir}\n")
    
    env_files = ["serenityprdpr.json", "serenityprod1.json"]
    all_valid = True
    
    for filename in env_files:
        file_path = env_dir / filename
        baseline_path = baseline_env_dir / filename
        result = validate_env_file(file_path, tenant_domain, tenant_id, baseline_path)
        
        print(f"{'-'*80}")
        print(f"File: {filename}")
        print(f"{'-'*80}")
        
        if result["status"] == "missing":
            print(f"❌ {result['message']}")
            all_valid = False
        elif result["status"] == "error":
            print(f"❌ {result['message']}")
            all_valid = False
        else:
            if result.get("match"):
                print(f"✅ PASSED - {result['message']}")
                print(f"   - tenant-domain: {tenant_domain} ✓")
                print(f"   - tenant-id: {tenant_id} ✓")
            else:
                print(f"❌ FAILED - File does not match baseline")
                print(f"   Total differences: {result['total_differences']}")
                print(f"   Showing first {len(result['differences'])} differences:")
                for diff in result['differences']:
                    print(f"   - {diff}")
                all_valid = False
        print()
    
    print(f"{'='*80}")
    if all_valid:
        print("✅ All environment files validated successfully!")
    else:
        print("❌ Some environment files have issues")
    print(f"{'='*80}\n")
