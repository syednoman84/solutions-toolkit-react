#!/usr/bin/env python3
from flask import Flask, request, jsonify
import subprocess
import os
from pathlib import Path

app = Flask(__name__)
BASE_DIR = Path(__file__).parent.parent
PARAMS_FILE = BASE_DIR / 'params' / 'params.txt'
SCRIPTS_DIR = BASE_DIR / 'scripts'
RESULTS_DIR = BASE_DIR / 'results'

# CORS support for React dev server
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
    response.headers.add('Access-Control-Allow-Methods', 'GET,POST,OPTIONS')
    return response

@app.route('/api/load-params', methods=['GET'])
def load_params():
    if not PARAMS_FILE.exists():
        return jsonify({'error': 'params.txt not found'}), 404
    
    with open(PARAMS_FILE) as f:
        lines = f.readlines()
    
    params = {}
    products = []
    
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith('#'):
            continue
        if '=' in stripped:
            key, value = stripped.split('=', 1)
            key = key.strip()
            value = value.strip()
            
            if '_Product_' in key:
                parts = key.split('_Product_')
                product_type = parts[0]
                products.append({'type': product_type, 'name': value})
            else:
                params[key] = value
    
    return jsonify({'params': params, 'products': products})

@app.route('/api/save-params', methods=['POST'])
def save_params():
    data = request.json
    
    # Read existing params.txt
    if PARAMS_FILE.exists():
        with open(PARAMS_FILE) as f:
            lines = f.readlines()
    else:
        return jsonify({'error': 'params.txt not found'}), 404
    
    # Set workingDirectory to results
    results_dir = str(RESULTS_DIR)
    
    # Update specific values
    updated_lines = []
    products_line_index = -1
    
    for i, line in enumerate(lines):
        stripped = line.strip()
        
        # Track where to insert products
        if stripped == '# List of Products to be created':
            products_line_index = i
            updated_lines.append(line)
            continue
        
        # Skip existing product lines (will be replaced)
        if products_line_index != -1 and '_Product_' in line and '=' in line:
            continue
        
        # Update specific parameters
        if '=' in line and not line.strip().startswith('#'):
            key = line.split('=')[0].strip()
            if key == 'destination_repo_github_url':
                updated_lines.append(f"{key}={data['destRepo']}\n")
            elif key == 'tenant-domain':
                updated_lines.append(f"{key}={data['tenantDomain']}\n")
            elif key == 'tenant-id':
                updated_lines.append(f"{key}={data['tenantId']}\n")
            elif key == 'template_vars_tag':
                updated_lines.append(f"{key}={data['templateTag']}\n")
            elif key == 'pr_title':
                updated_lines.append(f"{key}={data['prTitle']}\n")
            elif key == 'branchName':
                updated_lines.append(f"{key}={data['branchName']}\n")
            elif key == 'commit_message':
                updated_lines.append(f"{key}={data.get('commitMessage', '')}\n")
            elif key == 'workingDirectory':
                # Override workingDirectory to results
                updated_lines.append(f"{key}={results_dir}\n")
            else:
                updated_lines.append(line)
        else:
            updated_lines.append(line)
    
    # Insert products after "# List of Products to be created"
    if products_line_index != -1:
        product_counts = {}
        product_lines = []
        
        for product in data['products']:
            ptype = product['type']
            if ptype not in product_counts:
                product_counts[ptype] = 0
            product_counts[ptype] += 1
            product_lines.append(f"{ptype}_Product_{product_counts[ptype]}={product['name']}\n")
        
        # Insert products right after the comment line
        updated_lines = (
            updated_lines[:products_line_index + 1] + 
            product_lines + 
            ['\n'] +
            updated_lines[products_line_index + 1:]
        )
    
    with open(PARAMS_FILE, 'w') as f:
        f.writelines(updated_lines)
    
    return jsonify({'success': True, 'workdir': results_dir})

@app.route('/api/run-setup', methods=['POST'])
def run_setup():
    script = SCRIPTS_DIR / 'PCM_Tenants_Configs_Setup.py'
    if not script.exists():
        return jsonify({'error': 'Setup script not found'}), 404
    
    try:
        result = subprocess.run(
            ['python3', str(script)],
            cwd=str(BASE_DIR),
            capture_output=True,
            text=True,
            timeout=300
        )
        return jsonify({
            'stdout': result.stdout,
            'stderr': result.stderr,
            'returncode': result.returncode
        })
    except subprocess.TimeoutExpired:
        return jsonify({'error': 'Script execution timed out'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/validate/<script_type>', methods=['POST'])
def validate(script_type):
    script_map = {
        'template_vars': 'validate_template_vars.py',
        'env_files': 'validate_env_files.py',
        'summary': 'print_products_summary.py'
    }
    
    script_name = script_map.get(script_type)
    if not script_name:
        return jsonify({'error': 'Invalid script type'}), 400
    
    script = SCRIPTS_DIR / script_name
    if not script.exists():
        return jsonify({'error': f'{script_name} not found'}), 404
    
    try:
        result = subprocess.run(
            ['python3', str(script)],
            cwd=str(BASE_DIR),
            capture_output=True,
            text=True,
            timeout=60
        )
        return jsonify({
            'stdout': result.stdout,
            'stderr': result.stderr,
            'returncode': result.returncode
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/add-products/load-params', methods=['GET'])
def add_products_load_params():
    if not PARAMS_FILE.exists():
        return jsonify({'error': 'params.txt not found'}), 404

    with open(PARAMS_FILE) as f:
        lines = f.readlines()

    params = {}
    products = []

    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith('#'):
            continue
        if '=' in stripped:
            key, value = stripped.split('=', 1)
            key = key.strip()
            value = value.strip()
            if '_Product_' in key:
                parts = key.split('_Product_')
                product_type = parts[0]
                products.append({'type': product_type, 'name': value})
            else:
                params[key] = value

    return jsonify({'params': params, 'products': products})

@app.route('/api/add-products/save-params', methods=['POST'])
def add_products_save_params():
    data = request.json

    if not PARAMS_FILE.exists():
        return jsonify({'error': 'params.txt not found'}), 404

    with open(PARAMS_FILE) as f:
        lines = f.readlines()

    results_dir = str(RESULTS_DIR)
    updated_lines = []
    products_line_index = -1

    for i, line in enumerate(lines):
        stripped = line.strip()

        if stripped == '# List of Products to be created':
            products_line_index = i
            updated_lines.append(line)
            continue

        # Skip existing product lines (will be replaced)
        if products_line_index != -1 and '_Product_' in line and '=' in line:
            continue

        if '=' in line and not line.strip().startswith('#'):
            key = line.split('=')[0].strip()
            if key == 'destination_repo_github_url':
                updated_lines.append(f"{key}={data['destRepo']}\n")
            elif key == 'template_vars_tag':
                updated_lines.append(f"{key}={data['templateTag']}\n")
            elif key == 'pr_title':
                updated_lines.append(f"{key}={data['prTitle']}\n")
            elif key == 'branchName':
                updated_lines.append(f"{key}={data['branchName']}\n")
            elif key == 'commit_message':
                updated_lines.append(f"{key}={data.get('commitMessage', '')}\n")
            elif key == 'workingDirectory':
                updated_lines.append(f"{key}={results_dir}\n")
            else:
                updated_lines.append(line)
        else:
            updated_lines.append(line)

    # Insert products after "# List of Products to be created"
    if products_line_index != -1:
        product_counts = {}
        product_lines = []
        for product in data['products']:
            ptype = product['type']
            if ptype not in product_counts:
                product_counts[ptype] = 0
            product_counts[ptype] += 1
            product_lines.append(f"{ptype}_Product_{product_counts[ptype]}={product['name']}\n")

        updated_lines = (
            updated_lines[:products_line_index + 1] +
            product_lines +
            ['\n'] +
            updated_lines[products_line_index + 1:]
        )

    with open(PARAMS_FILE, 'w') as f:
        f.writelines(updated_lines)

    return jsonify({'success': True, 'workdir': results_dir})

@app.route('/api/add-products/run', methods=['POST'])
def add_products_run():
    script = SCRIPTS_DIR / 'PCM_Add_Products_Existing_Tenant.py'
    if not script.exists():
        return jsonify({'error': 'Add products script not found'}), 404

    try:
        result = subprocess.run(
            ['python3', str(script)],
            cwd=str(BASE_DIR),
            capture_output=True,
            text=True,
            timeout=300
        )
        return jsonify({
            'stdout': result.stdout,
            'stderr': result.stderr,
            'returncode': result.returncode
        })
    except subprocess.TimeoutExpired:
        return jsonify({'error': 'Script execution timed out'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/disable-products/save-params', methods=['POST'])
def disable_products_save_params():
    data = request.json

    if not PARAMS_FILE.exists():
        return jsonify({'error': 'params.txt not found'}), 404

    with open(PARAMS_FILE) as f:
        lines = f.readlines()

    results_dir = str(RESULTS_DIR)
    updated_lines = []
    products_line_index = -1

    for i, line in enumerate(lines):
        stripped = line.strip()

        if stripped == '# List of Products to be created':
            products_line_index = i
            updated_lines.append(line)
            continue

        # Skip existing product lines and disable product lines (will be replaced)
        if products_line_index != -1 and ('_Product_' in line or 'Disable_Product_' in line) and '=' in line:
            continue

        if '=' in line and not line.strip().startswith('#'):
            key = line.split('=')[0].strip()
            if key == 'destination_repo_github_url':
                updated_lines.append(f"{key}={data['destRepo']}\n")
            elif key == 'pr_title':
                updated_lines.append(f"{key}={data['prTitle']}\n")
            elif key == 'branchName':
                updated_lines.append(f"{key}={data['branchName']}\n")
            elif key == 'commit_message':
                updated_lines.append(f"{key}={data.get('commitMessage', '')}\n")
            elif key == 'workingDirectory':
                updated_lines.append(f"{key}={results_dir}\n")
            else:
                updated_lines.append(line)
        else:
            updated_lines.append(line)

    # Insert disable product IDs after "# List of Products to be created"
    if products_line_index != -1:
        product_lines = []
        for idx, pid in enumerate(data['productIds'], 1):
            product_lines.append(f"Disable_Product_{idx}={pid}\n")

        updated_lines = (
            updated_lines[:products_line_index + 1] +
            product_lines +
            ['\n'] +
            updated_lines[products_line_index + 1:]
        )

    with open(PARAMS_FILE, 'w') as f:
        f.writelines(updated_lines)

    return jsonify({'success': True, 'workdir': results_dir})

@app.route('/api/disable-products/run', methods=['POST'])
def disable_products_run():
    script = SCRIPTS_DIR / 'PCM_Disable_Products_Existing_Tenant.py'
    if not script.exists():
        return jsonify({'error': 'Disable products script not found'}), 404

    try:
        result = subprocess.run(
            ['python3', str(script)],
            cwd=str(BASE_DIR),
            capture_output=True,
            text=True,
            timeout=300
        )
        return jsonify({
            'stdout': result.stdout,
            'stderr': result.stderr,
            'returncode': result.returncode
        })
    except subprocess.TimeoutExpired:
        return jsonify({'error': 'Script execution timed out'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/sso-connection/save-params', methods=['POST'])
def sso_connection_save_params():
    data = request.json

    if not PARAMS_FILE.exists():
        return jsonify({'error': 'params.txt not found'}), 404

    with open(PARAMS_FILE) as f:
        lines = f.readlines()

    results_dir = str(RESULTS_DIR)
    updated_lines = []
    products_line_index = -1

    for i, line in enumerate(lines):
        stripped = line.strip()

        if stripped == '# List of Products to be created':
            products_line_index = i
            updated_lines.append(line)
            continue

        # Skip existing product lines, disable lines, and SSO lines (will be replaced)
        if products_line_index != -1 and ('_Product_' in line or 'Disable_Product_' in line or 'SSO_Connection_' in line) and '=' in line:
            continue

        if '=' in line and not line.strip().startswith('#'):
            key = line.split('=')[0].strip()
            if key == 'destination_repo_github_url':
                updated_lines.append(f"{key}={data['destRepo']}\n")
            elif key == 'pr_title':
                updated_lines.append(f"{key}={data['prTitle']}\n")
            elif key == 'commit_message':
                updated_lines.append(f"{key}={data['commitMessage']}\n")
            elif key == 'branchName':
                updated_lines.append(f"{key}={data['branchName']}\n")
            elif key == 'workingDirectory':
                updated_lines.append(f"{key}={results_dir}\n")
            else:
                updated_lines.append(line)
        else:
            updated_lines.append(line)

    # Check if commit_message key exists, if not add it before workingDirectory
    has_commit_message = any(
        l.strip().startswith('commit_message=') for l in updated_lines if not l.strip().startswith('#')
    )
    if not has_commit_message:
        # Insert after pr_title
        for i, l in enumerate(updated_lines):
            if l.strip().startswith('pr_title='):
                updated_lines.insert(i + 1, f"commit_message={data['commitMessage']}\n")
                break

    # Insert SSO connections after "# List of Products to be created"
    if products_line_index != -1:
        conn_lines = []
        for idx, conn in enumerate(data['connections'], 1):
            conn_lines.append(
                f"SSO_Connection_{idx}={conn['displayName']}, {conn['connectionName']}, {conn['ssoUrl']}\n"
            )

        updated_lines = (
            updated_lines[:products_line_index + 1] +
            conn_lines +
            ['\n'] +
            updated_lines[products_line_index + 1:]
        )

    with open(PARAMS_FILE, 'w') as f:
        f.writelines(updated_lines)

    return jsonify({'success': True, 'workdir': results_dir})

@app.route('/api/sso-connection/run', methods=['POST'])
def sso_connection_run():
    script = SCRIPTS_DIR / 'PCM_Add_SSO_Connection.py'
    if not script.exists():
        return jsonify({'error': 'SSO connection script not found'}), 404

    try:
        result = subprocess.run(
            ['python3', str(script)],
            cwd=str(BASE_DIR),
            capture_output=True,
            text=True,
            timeout=300
        )
        return jsonify({
            'stdout': result.stdout,
            'stderr': result.stderr,
            'returncode': result.returncode
        })
    except subprocess.TimeoutExpired:
        return jsonify({'error': 'Script execution timed out'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/rebase/create-changelog', methods=['POST'])
def create_changelog_file():
    """Create a changelog JSON file inside a product's amt-product-config-bff/changes/ directory."""
    import uuid as uuid_mod
    data = request.json or {}
    repo_path_str = data.get('repoPath', '').strip()
    product_id = data.get('productId', '').strip()
    json_content = data.get('jsonContent', '').strip()

    if not repo_path_str or not product_id or not json_content:
        return jsonify({'error': 'repoPath, productId, and jsonContent are required'}), 400

    repo_path = Path(repo_path_str)
    if not repo_path.exists():
        return jsonify({'error': 'Repository path not found. Clone first.'}), 404

    changes_dir = repo_path / 'product' / product_id / 'amt-product-config-bff' / 'changes'
    changes_dir.mkdir(parents=True, exist_ok=True)

    filename = f"{uuid_mod.uuid4()}.json"
    filepath = changes_dir / filename

    try:
        filepath.write_text(json_content, encoding='utf-8')
    except Exception as e:
        return jsonify({'error': f'Failed to write file: {e}'}), 500

    relative_path = f"product/{product_id}/amt-product-config-bff/changes/{filename}"
    return jsonify({'success': True, 'filename': filename, 'relativePath': relative_path})

# --- Rebase pending-changes API routes ---

REBASE_WORK_DIR = RESULTS_DIR / 'rebase'

@app.route('/api/rebase/clone', methods=['POST'])
def rebase_clone():
    """Clone the tenant repo and return list of product UUIDs."""
    data = request.json or {}
    tenant_id = data.get('tenantId', '').strip()
    repo_url = data.get('repoUrl', '').strip()

    if not tenant_id and not repo_url:
        return jsonify({'error': 'Tenant ID or Repository URL is required'}), 400

    if repo_url:
        repo_name = repo_url.rstrip('/').rstrip('.git').split('/')[-1]
    else:
        repo_name = f"ODXP-DPLOY--odx-config-{tenant_id}-deploy"
        repo_url = f"https://git.shared.linearft.tools/odx-platform-configs/{repo_name}.git"
    repo_path = REBASE_WORK_DIR / repo_name

    # Clean up previous clone
    if repo_path.exists():
        subprocess.run(['rm', '-rf', str(repo_path)])
    REBASE_WORK_DIR.mkdir(parents=True, exist_ok=True)

    try:
        result = subprocess.run(
            f'git clone {repo_url} {repo_path}',
            shell=True, capture_output=True, text=True, timeout=120
        )
        if result.returncode != 0:
            return jsonify({'error': f'Failed to clone: {result.stderr.strip()}'}), 500

        product_dir = repo_path / 'product'
        products = []
        if product_dir.exists():
            for uuid_dir in sorted(product_dir.iterdir()):
                if uuid_dir.is_dir():
                    products.append(uuid_dir.name)

        return jsonify({
            'repoPath': str(repo_path),
            'repoName': repo_name,
            'products': products
        })
    except subprocess.TimeoutExpired:
        return jsonify({'error': 'Clone timed out'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/rebase/run-command', methods=['POST'])
def rebase_run_command():
    """Run a shell command in the cloned repo directory."""
    data = request.json or {}
    repo_path = data.get('repoPath', '').strip()
    command = data.get('command', '').strip()

    if not repo_path or not command:
        return jsonify({'error': 'repoPath and command are required'}), 400

    if not Path(repo_path).exists():
        return jsonify({'error': 'Repository path not found. Clone first.'}), 404

    try:
        result = subprocess.run(
            command,
            shell=True,
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=60
        )
        return jsonify({
            'stdout': result.stdout,
            'stderr': result.stderr,
            'returncode': result.returncode
        })
    except subprocess.TimeoutExpired:
        return jsonify({'error': 'Command timed out'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

SCAN_OUTPUT_DIR = RESULTS_DIR / 'scan'

@app.route('/api/view-products-by-tenant/fetch', methods=['POST'])
def fetch_tenant_products():
    data = request.json or {}
    tenant_id = data.get('tenantId', '').strip()
    branch_name = data.get('branchName', 'master').strip() or 'master'
    if not tenant_id:
        return jsonify({'error': 'Tenant ID is required'}), 400

    script = SCRIPTS_DIR / 'fetch_tenant_products.py'
    if not script.exists():
        return jsonify({'error': 'fetch_tenant_products.py not found'}), 404

    try:
        result = subprocess.run(
            ['python3', str(script), tenant_id, branch_name],
            cwd=str(BASE_DIR),
            capture_output=True,
            text=True,
            timeout=120
        )
        if result.returncode != 0:
            error_msg = result.stderr.strip() or result.stdout.strip() or 'Script failed'
            return jsonify({'error': error_msg}), 500

        import json as json_mod
        products = json_mod.loads(result.stdout)
        return jsonify({'products': products})
    except subprocess.TimeoutExpired:
        return jsonify({'error': 'Timed out cloning/scanning the repository'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/scan-tenants/run', methods=['POST'])
def scan_tenants_run():
    data = request.json or {}
    limit = str(data.get('limit', 1000))
    cleanup = str(data.get('cleanup', True)).lower()

    script = SCRIPTS_DIR / 'tenant_product_analyzer.py'
    if not script.exists():
        return jsonify({'error': 'tenant_product_analyzer.py not found'}), 404

    SCAN_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    try:
        result = subprocess.run(
            ['python3', str(script), limit, cleanup, str(SCAN_OUTPUT_DIR)],
            cwd=str(BASE_DIR),
            capture_output=True,
            text=True,
            timeout=600
        )
        return jsonify({
            'stdout': result.stdout,
            'stderr': result.stderr,
            'returncode': result.returncode
        })
    except subprocess.TimeoutExpired:
        return jsonify({'error': 'Script execution timed out (10 min limit)'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/scan-tenants/results/<report_type>', methods=['GET'])
def scan_tenants_results(report_type):
    file_map = {
        'definitions': SCAN_OUTPUT_DIR / 'product_definitions.json',
        'count': SCAN_OUTPUT_DIR / 'products_count_by_tenant.txt',
        'types': SCAN_OUTPUT_DIR / 'product_type_count_by_tenant.txt'
    }

    filepath = file_map.get(report_type)
    if not filepath:
        return jsonify({'error': 'Invalid report type'}), 400

    if not filepath.exists():
        return jsonify({'error': f'Report not found. Run the scan first.'}), 404

    try:
        content = filepath.read_text(encoding='utf-8')
        return jsonify({'content': content, 'filename': filepath.name})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# --- Configure NACHA Files API routes ---

NACHA_DEFAULTS_DIR = BASE_DIR / 'params'
NACHA_WORK_DIR = RESULTS_DIR / 'nacha'

@app.route('/api/nacha/defaults', methods=['GET'])
def nacha_defaults():
    """Return the default JSON content for the three NACHA config files."""
    defaults = {}
    for key, filename in [
        ('fileOptions', 'nacha_file_options_default.txt'),
        ('vendor', 'nacha_vendor_default.txt'),
        ('nachaPg', 'nacha_nachapg_default.txt'),
    ]:
        filepath = NACHA_DEFAULTS_DIR / filename
        if filepath.exists():
            defaults[key] = filepath.read_text(encoding='utf-8')
        else:
            defaults[key] = '{}'
    return jsonify(defaults)

@app.route('/api/nacha/clone', methods=['POST'])
def nacha_clone():
    """Clone the tenant repo, checkout feature branch, and return existing env files."""
    data = request.json or {}
    repo_url = data.get('repoUrl', '').strip()
    branch_name = data.get('branchName', '').strip()

    if not repo_url or not branch_name:
        return jsonify({'error': 'Repository URL and branch name are required'}), 400

    # Derive repo name from URL
    repo_name = repo_url.rstrip('/').rstrip('.git').split('/')[-1]
    repo_path = NACHA_WORK_DIR / repo_name

    # Clean up previous clone
    if repo_path.exists():
        subprocess.run(['rm', '-rf', str(repo_path)])
    NACHA_WORK_DIR.mkdir(parents=True, exist_ok=True)

    try:
        # Clone
        result = subprocess.run(
            f'git clone {repo_url} {repo_path}',
            shell=True, capture_output=True, text=True, timeout=120
        )
        if result.returncode != 0:
            return jsonify({'error': f'Failed to clone: {result.stderr.strip()}'}), 500

        # Create and checkout feature branch
        checkout = subprocess.run(
            f'git checkout -b {branch_name}',
            shell=True, capture_output=True, text=True, cwd=str(repo_path)
        )
        if checkout.returncode != 0:
            # Branch may already exist, try just checking it out
            checkout2 = subprocess.run(
                f'git checkout {branch_name}',
                shell=True, capture_output=True, text=True, cwd=str(repo_path)
            )
            if checkout2.returncode != 0:
                return jsonify({'error': f'Failed to checkout branch: {checkout2.stderr.strip()}'}), 500

        # Read existing env files if they exist
        env_files = {}
        for env_name in ['serenityprdpr', 'serenityprod1']:
            env_file = repo_path / 'env' / f'{env_name}.json'
            if env_file.exists():
                try:
                    env_files[env_name] = env_file.read_text(encoding='utf-8')
                except Exception:
                    env_files[env_name] = None
            else:
                env_files[env_name] = None

        return jsonify({
            'repoPath': str(repo_path),
            'repoName': repo_name,
            'envFiles': env_files
        })
    except subprocess.TimeoutExpired:
        return jsonify({'error': 'Clone timed out'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/nacha/run', methods=['POST'])
def nacha_run():
    """Write NACHA config files, commit, push, and create PR."""
    import json as json_mod

    data = request.json or {}
    repo_path_str = data.get('repoPath', '').strip()
    pr_title = data.get('prTitle', '').strip()
    commit_message = data.get('commitMessage', '').strip()
    branch_name = data.get('branchName', '').strip()
    file_options_json = data.get('fileOptionsJson', '').strip()
    vendor_json = data.get('vendorJson', '').strip()
    nacha_pg_json = data.get('nachaPgJson', '').strip()
    serenityprdpr_json = data.get('serenityprdprJson', '')
    serenityprod1_json = data.get('serenityprod1Json', '')

    if not repo_path_str or not pr_title or not commit_message or not branch_name:
        return jsonify({'error': 'repoPath, prTitle, commitMessage, and branchName are required'}), 400

    repo_path = Path(repo_path_str)
    if not repo_path.exists():
        return jsonify({'error': 'Repository path not found. Clone first.'}), 404

    files_written = []

    try:
        # Write file_options.json
        if file_options_json:
            parsed = json_mod.loads(file_options_json)
            dest = repo_path / 'app' / 'payment-gateway' / 'nacha' / 'file_options.json'
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(json_mod.dumps(parsed, indent=2) + '\n', encoding='utf-8')
            files_written.append('app/payment-gateway/nacha/file_options.json')

        # Write vendor.json
        if vendor_json:
            parsed = json_mod.loads(vendor_json)
            dest = repo_path / 'app' / 'payment-gateway' / 'nacha' / 'vendor.json'
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(json_mod.dumps(parsed, indent=2) + '\n', encoding='utf-8')
            files_written.append('app/payment-gateway/nacha/vendor.json')

        # Write nachaPg.json
        if nacha_pg_json:
            parsed = json_mod.loads(nacha_pg_json)
            dest = repo_path / 'app' / 'template_vars' / 'nachaPg.json'
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(json_mod.dumps(parsed, indent=2) + '\n', encoding='utf-8')
            files_written.append('app/template_vars/nachaPg.json')

        # Write env files if provided
        if serenityprdpr_json and serenityprdpr_json.strip():
            parsed = json_mod.loads(serenityprdpr_json)
            dest = repo_path / 'env' / 'serenityprdpr.json'
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(json_mod.dumps(parsed, indent=2) + '\n', encoding='utf-8')
            files_written.append('env/serenityprdpr.json')

        if serenityprod1_json and serenityprod1_json.strip():
            parsed = json_mod.loads(serenityprod1_json)
            dest = repo_path / 'env' / 'serenityprod1.json'
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(json_mod.dumps(parsed, indent=2) + '\n', encoding='utf-8')
            files_written.append('env/serenityprod1.json')

        if not files_written:
            return jsonify({'error': 'No files to write'}), 400

        # Git add, commit, push
        add_result = subprocess.run(
            'git add -A',
            shell=True, capture_output=True, text=True, cwd=str(repo_path)
        )

        commit_result = subprocess.run(
            f'git commit -m "{commit_message}"',
            shell=True, capture_output=True, text=True, cwd=str(repo_path)
        )

        push_result = subprocess.run(
            f'git push -u origin {branch_name}',
            shell=True, capture_output=True, text=True, cwd=str(repo_path), timeout=120
        )

        # Create PR
        pr_result = subprocess.run(
            f'gh pr create --title "{pr_title}" --body "Automated NACHA configuration files setup" --base master --head {branch_name}',
            shell=True, capture_output=True, text=True, cwd=str(repo_path), timeout=60
        )

        stdout_parts = []
        stdout_parts.append(f'✅ Files written: {", ".join(files_written)}')
        if add_result.stdout:
            stdout_parts.append(add_result.stdout)
        if commit_result.stdout:
            stdout_parts.append(commit_result.stdout)
        if push_result.stdout:
            stdout_parts.append(push_result.stdout)
        if pr_result.stdout:
            stdout_parts.append(f'🔗 PR Created: {pr_result.stdout.strip()}')

        stderr_parts = []
        if push_result.stderr:
            stderr_parts.append(push_result.stderr)
        if pr_result.returncode != 0 and pr_result.stderr:
            stderr_parts.append(f'PR creation issue: {pr_result.stderr}')

        return jsonify({
            'stdout': '\n'.join(stdout_parts),
            'stderr': '\n'.join(stderr_parts),
            'returncode': push_result.returncode
        })

    except json_mod.JSONDecodeError as e:
        return jsonify({'error': f'Invalid JSON content: {str(e)}'}), 400
    except subprocess.TimeoutExpired:
        return jsonify({'error': 'Git operation timed out'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/readme', methods=['GET'])
def get_readme():
    readme_file = BASE_DIR / 'README.md'
    if not readme_file.exists():
        return jsonify({'error': 'README.md not found'}), 404
    
    try:
        content = readme_file.read_text(encoding='utf-8')
        return jsonify({'content': content})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("🚀 Starting PCM Tenants Configuration Toolkit Web UI")
    print("📍 Open http://localhost:5000 in your browser")
    app.run(debug=True, host='0.0.0.0', port=5000)
