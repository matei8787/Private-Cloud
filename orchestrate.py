import os
import sys
import ansible_runner
from pulumi import automation as auto

# --- Configuration ---
STACK_NAME = "dev"
REPO_ROOT = os.path.dirname(os.path.abspath(__file__))
INFRA_DIR = os.path.join(REPO_ROOT, "Pulumi", "infrastructure")
APPS_DIR = os.path.join(REPO_ROOT, "Pulumi", "apps")
ANSIBLE_DIR = os.path.join(REPO_ROOT, "Ansible") 

def run_ansible():
    """Runs Ansible programmatically using ansible-runner."""
    print(f"\n🚀 Starting Phase 2: Ansible Configuration...")
    
    
    inventory_path = os.path.join(ANSIBLE_DIR, "inventory", "inventory.yml")
    
    run_config = {
        'private_data_dir': ANSIBLE_DIR,
        'playbook': 'playbooks/site.yml',
        'inventory': inventory_path,
        'envvars': {
            'SSH_AUTH_SOCK': os.environ.get("SSH_AUTH_SOCK")
        }
    }

    r = ansible_runner.run(**run_config, quiet=False)

    if r.status == 'failed':
        print(f"❌ Ansible Failed! Status: {r.status}")
        raise Exception("Ansible Playbook execution failed.")
    
    print(f"✅ Ansible Complete. Stats: {r.stats}")

def main():
    if not os.environ.get("SSH_AUTH_SOCK"):
        print("❌ Error: SSH_AUTH_SOCK not defined.")
        sys.exit(1)

    print(f"\n🏗️  Phase 1: Infrastructure (Pulumi)...")
    infra_stack = auto.create_or_select_stack(stack_name=STACK_NAME, work_dir=INFRA_DIR)
    
    # Initialize Apps stack object early so it's available in the 'except' block
    apps_stack = auto.create_or_select_stack(stack_name=STACK_NAME, work_dir=APPS_DIR)

    try:
        # --- 1. Provision Infra ---
        infra_stack.up(on_output=print)
    
    except Exception as e:
        print(f"\n💥 Infrastructure Deployment Failed: {e}")
        try:
            print("🔻 Destroying Infrastructure Layer...")
            infra_stack.destroy(on_output=print)
            print("✅ Infrastructure removed.")
        except Exception as infra_err:
            print(f"💀 FATAL: Infrastructure destroy failed! Manual intervention required. {infra_err}")
        sys.exit(1)

    try:
        # --- 2. Deploy Apps (Pulumi) ---
        print(f"\n📦 Phase 2: Apps (Pulumi)...")
        # Apps stack pulls config via StackReference, so no set_config needed here
        apps_stack.up(on_output=print)
        
        print("\n✅✅✅ Full Private Cloud Deployment Complete! ✅✅✅")

    except Exception as e:
        print(f"\n💥 Critical Failure detected: {e}")
        print("🧹 Initiating Emergency Teardown Sequence...")
        
        # --- Teardown Logic (LIFO - Last In First Out) ---
        
        # 1. Try to destroy Apps (if they were partially created)
        try:
            print("🔻 Destroying Apps Layer...")
            # We destroy Apps first because they depend on the Infra
            apps_stack.destroy(on_output=print)
        except Exception as app_err:
            print(f"⚠️  App destroy failed (might not exist yet or already clean): {app_err}")
            
        sys.exit(1)

if __name__ == "__main__":
    main()