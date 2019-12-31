import podman


class PodmanContainer:
    def get_container(self):
        with podman.Client() as client:
            image_id = '{}:{}'.format(self.image, self.tag)
            image_id = client.images.pull(image_id)
            image = client.images.get(image_id)
            container = image.create(
                    detach=False,
                    env=self._parse_env_vars(),
                    hostname=self.hostname,
                    volume=self._parse_binds(),
                    command=self.command
            )
        return container

    def _parse_env_vars(self):
        return list(map(lambda var: '{}={}'.format(var[0], var[1]), self.env_vars.items()))

    def start(self):
        return self._ctr.start()

    def get_logs(self):
        return list(self._ctr.logs())

    def search_logs(self, term):
        logs = self.get_logs()
        for log in logs:
            if term in log:
                return True
        return False

    def running(self):
        return self._ctr.inspect().state['running']

    def destroy(self):
        return self._ctr.remove(force=True)
