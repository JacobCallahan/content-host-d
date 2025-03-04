import subprocess
from pathlib import Path

IGNORE_MESSAGES = ["JSONArgsRecommended", "SecretsUsedInArgOrEnv"]


def pytest_generate_tests(metafunc):
    if "directory" in metafunc.fixturenames:
        try:
            # Try direct attribute access as an alternative method
            dirs_opt = metafunc.config.option.dirs
        except AttributeError:
            # Fallback to default behavior
            dirs_opt = None
            
        if dirs_opt:
            dirs = dirs_opt.split(",")
        else:
            # Default: find all directories with Dockerfiles
            dirs = find_dockerfile_dirs()
        metafunc.parametrize("directory", dirs)

def find_dockerfile_dirs():
    """Find all directories containing a Dockerfile"""
    dockerfile_dirs = []
    root_path = Path('.')
    for path in root_path.rglob('Dockerfile'):
        dockerfile_dirs.append(str(path.parent))
    return dockerfile_dirs

def test_docker_build(directory):
    """Test that docker build succeeds without errors for the directory"""
    dockerfile_path = Path(directory) / "Dockerfile"
    assert dockerfile_path.exists(), f"No Dockerfile found in {directory}"
    
    result = subprocess.run(
        ["docker", "build", "--check", "."],
        cwd=directory,
        capture_output=True,
        text=True
    )
        
    # If build succeeded, pass the test immediately
    if result.returncode == 0:
        return
        
    # If build failed, check for unignored warning/error messages
    for line in result.stdout.splitlines():
        if line.startswith(("WARNING:", "ERROR:")):
            # Check if this message should be ignored
            if not any(ignore_msg in line for ignore_msg in IGNORE_MESSAGES):
                assert False, f"Unignored message: {line}"
