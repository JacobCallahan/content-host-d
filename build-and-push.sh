#!/bin/bash
REPO_DIR=${REPO_DIR:-~/content-host-d}

# Determine if Docker or Podman is available.
if command -v docker &> /dev/null; then
    CONTAINER_CMD="docker"
elif command -v podman &> /dev/null; then
    CONTAINER_CMD="podman"
else
    echo "Neither Docker nor Podman is installed. Exiting."
    exit 1
fi

# Validate arguments were passed and REPO_DIR exists.
if [[ $# -eq 0 ]]; then
    echo "No build targets specified. Exiting."
    exit 1
elif [[ ! -d ${REPO_DIR} ]]; then
    echo "Directory ${REPO_DIR} could not be found. Exiting."
    exit 1
fi

# shellcheck disable=SC2164
cd ${REPO_DIR}
git fetch origin
git checkout master
git reset --hard origin/master
git clean -f

for var in "${@}"
do
    # Verify that the build target folder exists.
    if [[ ! -d ${var} ]]; then
        echo "Target ${var} not found. Skipping."
        continue
    fi

    # Copy any user-provided files to the build target folder.
    [[ -d resources ]] && cp -r resources ${var}
    [[ -d setup_scripts ]] && cp -r setup_scripts ${var}

    BUILD_CMD="${CONTAINER_CMD} build ${var} -t ${var,,}"

    # Pass ROOT_PASSWD to UBI*-init images if set.
    [[ ${var} =~ -init ]] && [[ -v ROOT_PASSWD ]] && BUILD_CMD+=" --build-arg ROOT_PASSWD=${ROOT_PASSWD}"

    # Use cgroup v1 for UBI7-init images.
	[[ ${var,,} == ubi7-init ]] && BUILD_CMD+=" --annotation 'run.oci.systemd.force_cgroup_v1=/sys/fs/cgroup'"

    eval ${BUILD_CMD}
done
