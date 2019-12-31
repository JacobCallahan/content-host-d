import docker


class DockerContainer:
    def __init__(self):
        self._client = docker.Client(version='1.22')

    def get_container(self):
        return self._client.create_container(
            image='{0}:{1}'.format(self.image, self.tag),
            hostname=self.hostname,
            detach=False,
            environment=self.env_vars,
            volumes=self.binds.keys(),
            host_config=self._client.create_host_config(binds=self._parse_binds()),
        )

    def start(self):
        return self._client.start(container=self._ctr, network_mode=self.network_mode)

    def get_logs(self):
        return self._client.logs(self._ctr['Id'])

    def search_logs(self, term):
        return term.encode() in self.get_logs()

    def running(self):
        return self._client.inspect_container(self._ctr['Id'])['State'][
            'Status'
        ] == u'running'

    def destroy(self):
        return self._client.remove_container(self._ctr, v=True, force=True)
