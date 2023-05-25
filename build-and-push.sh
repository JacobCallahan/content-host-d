cd ~/content-host-d
git fetch origin
git checkout master
git reset --hard origin/master
for var in "${@}"
do
    cp -r resources ~/content-host-d/${var}
    cp -r setup_scripts ~/content-host-d/${var}
    docker build -t ${var,,} ~/content-host-d/${var}
done
echo "------------- Cleaning up after docker -------------"
docker rm -v $(docker ps -q -f "status=exited")
docker volume rm $(docker volume ls -f dangling=true -q)
docker rmi $(docker images -f "dangling=true" -q)
