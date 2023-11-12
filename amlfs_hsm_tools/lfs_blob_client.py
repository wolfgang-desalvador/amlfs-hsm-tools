from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient

from .utilities import loadConfiguration


class LFSBlobClient(BlobServiceClient):
    def __init__(self, configurationFile='/etc/amlfs_hsm_tools.json', **kwargs) -> None:
        configuration = loadConfiguration(configurationFile)
        self.accountURL = configuration.get('accountURL')
        self.containerName = configuration.get('containerName')
        super().__init__(self.accountURL, credential=DefaultAzureCredential(exclude_workload_identity_credential=True, exclude_environment_credential=True), **kwargs)
