# install_and_run.py
import sys
import subprocess
import importlib
import os

APP_FILENAME = "custom_ui2.py"  # change if your app file name is different
REQUIRED_PKGS = ["matplotlib", "streamlit"]

def run(cmd, check=True):
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    print(proc.stdout)
    if check and proc.returncode != 0:
        raise SystemExit(f"Command failed: {' '.join(cmd)} (exit {proc.returncode})")
    return proc

def ensure_pip_upgraded():
    print("Upgrading pip...")
    run([sys.executable, "-m", "pip", "install", "--upgrade", "pip"])

def ensure_package(pkg):
    try:
        importlib.import_module(pkg)
        print(f"Package '{pkg}' already installed.")
        return
    except Exception:
        print(f"Installing package: {pkg}")
    run([sys.executable, "-m", "pip", "install", pkg])

def install_requirements_txt():
    req = os.path.abspath("requirements.txt")
    if os.path.exists(req):
        print("Installing from requirements.txt...")
        run([sys.executable, "-m", "pip", "install", "-r", req])

def launch_streamlit(app_path):
    print(f"Launching Streamlit app: {app_path}")
    # Use the same Python interpreter to run streamlit so environment is consistent
    run([sys.executable, "-m", "streamlit", "run", app_path], check=False)

def main():
    # 1) Ensure pip updated
    ensure_pip_upgraded()

    # 2) Ensure required packages
    for pkg in REQUIRED_PKGS:
        pkg_clean = pkg.strip()
        if pkg_clean:
            ensure_package(pkg_clean)

    # 3) Install extras from requirements.txt (if present)
    install_requirements_txt()

    # 4) Verify app file exists
    app_path = os.path.join(os.path.dirname(__file__), "custom_ui.py")
    if not os.path.exists(app_path):
        raise SystemExit(f"Streamlit app file not found: {app_path}")

    # 5) Launch Streamlit
    launch_streamlit(app_path)

if __name__ == "__main__":

    main()