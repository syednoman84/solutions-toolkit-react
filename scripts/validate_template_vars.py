import json
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

def parse_map_param(param_str):
    """Parse param string like: k1:v1,k2:v2 into dict"""
    mapping = {}
    if not param_str:
        return mapping
    for entry in param_str.split(","):
        entry = entry.strip()
        if not entry or ":" not in entry:
            continue
        k, v = entry.split(":", 1)
        mapping[k.strip()] = v.strip()
    return mapping

def get_all_files(directory):
    """Get all files recursively from directory."""
    return {f.relative_to(directory): f for f in Path(directory).rglob('*') if f.is_file()}

def compare_json_files(file1, file2):
    """Compare two JSON files, return True if identical."""
    try:
        with open(file1) as f1, open(file2) as f2:
            return json.load(f1) == json.load(f2)
    except:
        return False

def compare_template_vars(product_path, source_path, product_name):
    """Compare template_vars in product directory with source default-variables"""
    product_tv = product_path / "template_vars"
    
    if not product_tv.exists():
        return {"status": "missing", "message": "template_vars directory not found"}
    
    if not source_path.exists():
        return {"status": "error", "message": f"Source path not found: {source_path}"}
    
    # Get all files from both directories
    product_files = get_all_files(product_tv)
    source_files = get_all_files(source_path)
    
    product_names = set(product_files.keys())
    source_names = set(source_files.keys())
    
    missing = source_names - product_names
    extra = product_names - source_names
    common = product_names & source_names
    
    # Compare JSON files
    json_common = [f for f in common if f.suffix == '.json']
    identical = []
    different = []
    
    for rel_path in json_common:
        if compare_json_files(product_files[rel_path], source_files[rel_path]):
            identical.append(rel_path)
        else:
            different.append(rel_path)
    
    return {
        "status": "success",
        "total_files": len(product_files),
        "missing": sorted(missing),
        "extra": sorted(extra),
        "json_identical": len(identical),
        "json_different": sorted(different)
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
    
    product_dir = dest_repo / "product"
    
    # Clone template vars repo for comparison
    template_vars_tag = params.get("template_vars_tag")
    template_vars_url = params.get("template_vars_github_url")
    
    if not template_vars_url:
        print("❌ template_vars_github_url not found in params.txt")
        sys.exit(1)
    
    print(f"📥 Cloning template_vars repo at tag '{template_vars_tag}'...")
    template_vars_repo = validation_dir / "template_vars"
    
    try:
        subprocess.run(["git", "clone", template_vars_url, str(template_vars_repo)], check=True, capture_output=True)
        if template_vars_tag:
            subprocess.run(["git", "checkout", template_vars_tag], cwd=str(template_vars_repo), check=True, capture_output=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to clone template_vars: {e.stderr.decode()}")
        sys.exit(1)
    
    if not product_dir.exists():
        print(f"❌ Product directory not found: {product_dir}")
        sys.exit(1)
    
    if not template_vars_repo.exists():
        print(f"❌ Template vars repo not found: {template_vars_repo}")
        sys.exit(1)
    
    # Load template paths mapping
    TEMPLATE_PATHS = parse_map_param(params.get("TEMPLATE_PATHS", ""))
    
    # Find all products
    products = []
    for item in product_dir.iterdir():
        if item.is_dir():
            def_file = item / "definition.json"
            if def_file.exists():
                with open(def_file, "r", encoding="utf-8") as f:
                    definition = json.load(f)
                products.append((item, definition))
    
    if not products:
        print(f"⚠️ No products found in {product_dir}")
        sys.exit(0)
    
    # Sort by product type and name
    products.sort(key=lambda x: (x[1].get("productType", ""), x[1].get("productName", "")))
    
    print(f"\n{'='*80}")
    print(f"Template Variables Comparison Report")
    print(f"{'='*80}")
    print(f"Total products: {len(products)}\n")
    
    all_success = True
    results_by_type = {}
    
    for product_path, definition in products:
        product_type = definition.get("productType", "UNKNOWN")
        product_name = definition.get("productName", "UNKNOWN")
        
        # Map product type back to params key (e.g., CONSUMER_DAO -> Consumer_DAO)
        ptype_key = None
        for key, value in parse_map_param(params.get("PRODUCT_TYPE_MAP", "")).items():
            if value == product_type:
                ptype_key = key
                break
        
        if not ptype_key or ptype_key not in TEMPLATE_PATHS:
            print(f"⚠️ {product_name}: No template path mapping found for {product_type}")
            all_success = False
            continue
        
        source_path = template_vars_repo / TEMPLATE_PATHS[ptype_key]
        result = compare_template_vars(product_path, source_path, product_name)
        
        if ptype_key not in results_by_type:
            results_by_type[ptype_key] = []
        results_by_type[ptype_key].append((product_name, result))
    
    # Print results grouped by product type
    for ptype_key in sorted(results_by_type.keys()):
        print(f"\n{'-'*80}")
        print(f"Product Type: {ptype_key}")
        print(f"Source: {TEMPLATE_PATHS[ptype_key]}")
        print(f"{'-'*80}")
        
        for product_name, result in results_by_type[ptype_key]:
            if result["status"] == "success":
                status_icon = "✅" if not result["missing"] and not result["json_different"] else "⚠️"
                print(f"\n  {status_icon} {product_name}")
                print(f"     Total files: {result['total_files']}")
                print(f"     JSON identical: {result['json_identical']}")
                
                if result["missing"]:
                    print(f"     ❌ Missing files: {len(result['missing'])}")
                    for f in result["missing"]:
                        print(f"        - {f}")
                    all_success = False
                
                if result["extra"]:
                    print(f"     ⚠️ Extra files: {len(result['extra'])}")
                    for f in result["extra"]:
                        print(f"        - {f}")
                
                if result["json_different"]:
                    print(f"     ❌ Different JSON files: {len(result['json_different'])}")
                    for f in result["json_different"]:
                        print(f"        - {f}")
                    all_success = False
            else:
                print(f"\n  ❌ {product_name}: {result['message']}")
                all_success = False
    
    print(f"\n{'='*80}")
    if all_success:
        print("✅ All template_vars copied successfully!")
    else:
        print("⚠️ Some issues found in template_vars comparison")
    print(f"{'='*80}\n")
