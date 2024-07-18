cd ~/content-host-d
git fetch origin
git checkout master
git reset --hard origin/master

# Determine if Docker or Podman is available
if command -v docker &> /dev/null; then
    CONTAINER_CMD="docker"
elif command -v podman &> /dev/null; then
    CONTAINER_CMD="podman"
else
    echo "Neither Docker nor Podman is installed. Exiting."
    exit 1
fi

for var in "${@}"
do
    cp -r resources ~/content-host-d/${var}
    cp -r setup_scripts ~/content-host-d/${var}
    $CONTAINER_CMD build -t ${var,,} ~/content-host-d/${var}
done

echo "------------- Cleaning up after $CONTAINER_CMD -------------"
$CONTAINER_CMD rm -v $($CONTAINER_CMD ps -q -f "status=exited")
$CONTAINER_CMD volume rm $($CONTAINER_CMD volume ls -f dangling=true -q)
$CONTAINER_CMD rmi $($CONTAINER_CMD images -f "dangling=true" -q)
