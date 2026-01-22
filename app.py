import streamlit as st
import subprocess
import tempfile
import os
import re
import shutil
from pathlib import Path

def check_orca_installation():
    """Check if ORCA is installed and accessible."""
    try:
        result = subprocess.run(['which', 'orca'], 
                              capture_output=True, 
                              text=True, 
                              timeout=10)
        if result.returncode == 0 and result.stdout.strip():
            orca_path = result.stdout.strip()
            return True, f"ORCA installation found"
        else:
            return False, "ORCA is not installed or not accessible via command line"
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False, "ORCA is not installed or not accessible via command line"

def generate_orca_input(geometry, method="B3LYP", basis="def2-SVP", calculation_type="Opt"):
    """Generate ORCA input file content."""
    input_content = f"""! {method} {basis} {calculation_type}

* xyz 0 1
{geometry}
*
"""
    return input_content

def run_orca_calculation(input_content, temp_dir):
    """Run ORCA calculation and return output file path."""
    input_file = os.path.join(temp_dir, "calculation.inp")
    output_file = os.path.join(temp_dir, "calculation.out")
    
    # Write input file
    with open(input_file, 'w') as f:
        f.write(input_content)
    
    # Run ORCA calculation with shell redirection (as per ORCA manual)
    # ORCA writes to stdout/stderr which must be redirected to output file
    try:
        # Use shell=True to enable redirection: orca input.inp >& output.out
        command = f"orca {input_file} >& {output_file}"
        result = subprocess.run(command,
                              shell=True,
                              cwd=temp_dir,
                              timeout=300)  # 5 minute timeout
        
        # Check if output file was created
        if not os.path.exists(output_file):
            files_created = os.listdir(temp_dir)
            error_msg = f"ORCA did not create output file.\nReturn code: {result.returncode}\n"
            error_msg += f"Files in temp directory: {files_created}\n"
            return False, output_file, error_msg
        
        # Read output file to check for errors
        with open(output_file, 'r') as f:
            output_content = f.read()
        
        # Check if calculation terminated normally
        if "ORCA TERMINATED NORMALLY" not in output_content:
            return False, output_file, f"ORCA did not terminate normally. Check output file for errors."
        
        return True, output_file, output_content
    except subprocess.TimeoutExpired:
        return False, output_file, "Calculation timed out after 5 minutes"
    except Exception as e:
        return False, output_file, str(e)

def parse_orca_output(output_file):
    """Parse ORCA output file for energy and optimized geometry."""
    try:
        with open(output_file, 'r') as f:
            content = f.read()
        
        # Parse final energy - look for "FINAL SINGLE POINT ENERGY"
        energy_pattern = r'FINAL SINGLE POINT ENERGY\s+([-+]?\d*\.?\d+(?:[eE][-+]?\d+)?)'
        energy_match = re.search(energy_pattern, content)
        
        if energy_match:
            energy = energy_match.group(1)
        else:
            energy = "Not found"
        
        # Parse optimized geometry - look for the last CARTESIAN COORDINATES section
        geometry_pattern = r'CARTESIAN COORDINATES \(ANGSTROEM\)\s*-+\s*\n((?:.*\n)*?)(?=-{3,}|\n\s*\n)'
        geometry_matches = re.findall(geometry_pattern, content)
        
        if geometry_matches:
            # Get the last geometry (optimized)
            geometry_text = geometry_matches[-1].strip()
            # Extract atom coordinates
            atom_lines = []
            for line in geometry_text.split('\n'):
                line = line.strip()
                if line and not line.startswith('-'):
                    parts = line.split()
                    if len(parts) >= 4:
                        try:
                            # Check if we can parse the coordinates
                            float(parts[1])
                            float(parts[2])
                            float(parts[3])
                            atom_lines.append(f"{parts[0]:2s}  {parts[1]:>12s}  {parts[2]:>12s}  {parts[3]:>12s}")
                        except (ValueError, IndexError):
                            continue
            geometry = '\n'.join(atom_lines) if atom_lines else "Not found"
        else:
            geometry = "Not found"
        
        return energy, geometry, content
    except Exception as e:
        return f"Error: {str(e)}", f"Error: {str(e)}", str(e)

def main():
    st.title("🧪 ORCA DFT Calculator")
    st.markdown("""
    Welcome to the ORCA DFT Calculator! This app performs quantum chemistry calculations using the ORCA software package.
    
    **What this app does:**
    - Performs geometry optimization using DFT (Density Functional Theory)
    - Uses the B3LYP functional with def2-SVP basis set
    - Finds the lowest energy structure of your molecule
    """)
    
    # Check ORCA installation
    st.divider()
    st.subheader("Step 1: System Check")
    st.info("Verifying ORCA installation...")
    
    orca_available, orca_info = check_orca_installation()
    if not orca_available:
        st.error(f"❌ ORCA Error: {orca_info}")
        st.markdown("""
        **How to fix:**
        - Make sure ORCA is installed on your system
        - Ensure ORCA is in your PATH environment variable
        - Try running `which orca` in your terminal to verify
        """)
        st.stop()
    
    st.success(f"✓ {orca_info}")
    
    # Default water molecule geometry
    default_geometry = """O 0.0 0.0 0.0
H 0.96 0.0 0.0
H -0.24 0.93 0.0"""
    
    # Input section
    st.divider()
    st.subheader("Step 2: Define Your Molecule")
    st.markdown("""
    Enter the molecular geometry in XYZ format. Each line represents one atom with its coordinates.
    
    **Format:** `Element X Y Z`
    - **Element**: Atomic symbol (e.g., O, H, C, N)
    - **X, Y, Z**: Cartesian coordinates in Ångströms
    
    **Example:** The default water molecule (H₂O) is already loaded below.
    """)
    
    geometry_input = st.text_area(
        "Molecular coordinates:",
        value=default_geometry,
        height=150,
        help="Format: Element x y z (one atom per line, coordinates in Angstroms)"
    )
    
    # Show atom count
    atom_count = len([line for line in geometry_input.strip().split('\n') if line.strip()])
    st.caption(f"📊 Number of atoms: {atom_count}")
    
    # Fixed calculation parameters
    st.divider()
    st.subheader("Step 3: Calculation Settings")
    st.markdown("""
    These parameters are pre-configured for reliable results:
    """)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Method", "B3LYP", help="Hybrid DFT functional - good balance of accuracy and speed")
    with col2:
        st.metric("Basis Set", "def2-SVP", help="Split-valence polarized basis set - suitable for most organic molecules")
    with col3:
        st.metric("Job Type", "Opt", help="Geometry optimization - finds the lowest energy structure")
    
    st.info("💡 **Tip:** This setup is ideal for small to medium-sized organic molecules (< 100 atoms)")
    
    # Run calculation button
    st.divider()
    st.subheader("Step 4: Run Calculation")
    st.markdown("Click the button below to start the quantum chemistry calculation.")
    
    if st.button("🚀 Run Calculation", type="primary", use_container_width=True):
        if not geometry_input.strip():
            st.error("❌ Please enter molecular geometry")
            return
        
        # Create temporary directory
        with tempfile.TemporaryDirectory() as temp_dir:
            with st.status("Running ORCA calculation...", expanded=True) as status:
                st.write("📝 Generating ORCA input file...")
                input_content = generate_orca_input(geometry_input)
                
                st.write("⚙️ Executing ORCA calculation...")
                st.caption("This may take a few seconds to several minutes depending on molecule size")
                
                # Run calculation
                success, output_file, message = run_orca_calculation(input_content, temp_dir)
                
                if not success:
                    status.update(label="❌ Calculation failed", state="error")
                    st.error(f"Calculation failed: {message}")
                    return
                
                st.write("✅ Parsing results...")
                status.update(label="✅ Calculation completed successfully!", state="complete")
            
            # Parse results
            energy, optimized_geometry, full_output = parse_orca_output(output_file)
            
            # Display results
            st.divider()
            st.header("📊 Results")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("⚡ Final Energy")
                st.metric("Energy", f"{energy} Eh", help="Total electronic energy in Hartrees (Eh)")
                st.caption("Lower energy = more stable structure")
            
            with col2:
                st.subheader("🔬 Optimized Geometry")
                st.caption("Final atomic coordinates (Ångströms)")
                st.code(optimized_geometry, language=None)
            
            # Full ORCA output in expandable section
            st.divider()
            st.subheader("📄 Full ORCA Output")
            st.markdown("Expand below to see the complete ORCA output including the ASCII art logo and detailed calculation information.")
            
            with st.expander("View Complete ORCA Output", expanded=False):
                st.text_area(
                    "ORCA Output",
                    value=full_output,
                    height=400,
                    label_visibility="collapsed"
                )
            
            # Download section
            st.divider()
            st.subheader("💾 Download Results")
            st.markdown("Download the complete ORCA output file for further analysis or record keeping.")
            st.download_button(
                label="📥 Download ORCA Output File",
                data=full_output,
                file_name="orca_output.out",
                mime="text/plain",
                use_container_width=True
            )

if __name__ == "__main__":
    main()
