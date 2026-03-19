import json
import sys
from pathlib import Path

def load_params(file_path):
    """Load workingDirectory from params.txt"""
    params = {}
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            params[key.strip()] = value.strip()
    return params

def print_summary(product_dir):
    """Print summary of all products in the product directory"""
    product_dir = Path(product_dir)
    
    if not product_dir.exists():
        print(f"❌ Product directory not found: {product_dir}")
        sys.exit(1)
    
    # Find all product directories (UUID directories with definition.json)
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
        return
    
    # Sort by product type and name for consistent output
    products.sort(key=lambda x: (x[1].get("productType", ""), x[1].get("productName", "")))
    
    print(f"📋 Summary of products in: {product_dir}")
    print(f"Total products: {len(products)}\n")
    
    for product_path, definition in products:
        ptype = definition.get("productType", "UNKNOWN")
        pname = definition.get("productName", "UNKNOWN")
        
        print(f"{'='*80}")
        print(f"{ptype}: {pname}")
        print(f"Path: {product_path}")
        print(f"{'='*80}")
        print(json.dumps(definition, indent=2, ensure_ascii=False))
        print()

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
    
    print_summary(product_dir)
