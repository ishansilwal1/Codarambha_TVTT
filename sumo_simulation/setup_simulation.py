"""
LifeLine AI - Network Generation Script
Generates SUMO network from nodes and edges files
"""

import os
import subprocess
import sys

def check_sumo_installation():
    """Check if SUMO is properly installed"""
    if 'SUMO_HOME' not in os.environ:
        print("❌ Error: SUMO_HOME environment variable not set!")
        print("\nPlease set SUMO_HOME to your SUMO installation directory.")
        print("Example (Windows): setx SUMO_HOME \"C:\\Program Files (x86)\\Eclipse\\Sumo\"")
        print("Example (Linux): export SUMO_HOME=/usr/share/sumo")
        return False
    
    sumo_home = os.environ['SUMO_HOME']
    print(f"✅ SUMO_HOME found: {sumo_home}")
    return True

def generate_network():
    """Generate SUMO network file from nodes and edges"""
    print("\n" + "="*80)
    print("🚦 LifeLine AI - Network Generation")
    print("="*80)
    
    if not check_sumo_installation():
        return False
    
    # Find netconvert
    netconvert = os.path.join(os.environ['SUMO_HOME'], 'bin', 'netconvert')
    if sys.platform == 'win32':
        netconvert += '.exe'
    
    if not os.path.exists(netconvert):
        print(f"❌ Error: netconvert not found at {netconvert}")
        return False
    
    print(f"\n📍 Using netconvert: {netconvert}")
    
    # Check input files
    files_to_check = ['city.nod.xml', 'city.edg.xml']
    for file in files_to_check:
        if not os.path.exists(file):
            print(f"❌ Error: Required file not found: {file}")
            return False
        print(f"✅ Found: {file}")
    
    # Generate network
    print("\n🔨 Generating network file...")
    
    cmd = [
        netconvert,
        '--node-files=city.nod.xml',
        '--edge-files=city.edg.xml',
        '--output-file=city.net.xml',
        '--default.junctions.keep-clear=false',
        '--tls.guess=true',
        '--no-turnarounds=false'
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Network file generated successfully: city.net.xml")
            
            if os.path.exists('city.net.xml'):
                size = os.path.getsize('city.net.xml')
                print(f"   File size: {size} bytes")
            
            return True
        else:
            print("❌ Error generating network:")
            print(result.stderr)
            return False
            
    except Exception as e:
        print(f"❌ Error running netconvert: {e}")
        return False

def verify_files():
    """Verify all required files exist"""
    print("\n📋 Verifying simulation files...")
    
    required_files = [
        'city.net.xml',
        'routes.rou.xml',
        'simulation.sumocfg',
        'gui-settings.xml'
    ]
    
    all_exist = True
    for file in required_files:
        if os.path.exists(file):
            print(f"   ✅ {file}")
        else:
            print(f"   ❌ {file} - MISSING")
            all_exist = False
    
    return all_exist

def print_instructions():
    """Print usage instructions"""
    print("\n" + "="*80)
    print("🎯 Setup Complete!")
    print("="*80)
    print("\nTo run the simulation:")
    print("   python simulation.py")
    print("\nOr manually with SUMO-GUI:")
    print("   sumo-gui -c simulation.sumocfg")
    print("\n" + "="*80)

def main():
    """Main setup function"""
    print("Starting LifeLine AI setup...\n")
    
    # Generate network
    if not generate_network():
        print("\n❌ Setup failed!")
        sys.exit(1)
    
    # Verify all files
    if not verify_files():
        print("\n⚠️  Warning: Some files are missing!")
    
    # Print instructions
    print_instructions()
    
    print("✅ Setup completed successfully!\n")

if __name__ == "__main__":
    main()
