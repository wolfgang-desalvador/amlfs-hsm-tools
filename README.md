# Azure Managed Lustre HSM Tools
This repository contains an implementation to allow more efficient manage of HSM on Azure Managed Lustre.

# Prerequisites

This utilities rely on a Managed Identity with propoer permissions on the Azure Blob Storage acting as Lustre HSM backend.

More specifically it requires:
* A managed identity with Storage Blob Data Contributor role on the relevant container for Lustre HSM
* A configuration file in `/etc/amlfs_hsm_tools.json` containing account URL and container name, with the following format:

```json
{
    "accountURL": "https://<STORAGE_ACCOUNT_NAME>.blob.core.windows.net/",
    "containerName": "<LUSTRE_HSM_CONTAINER_NAME>"
}
```

## Installation

Ideally, this package is meant to run on Python 3. It is suggested to create a virtual environment, for example:

```bash
python3 -m venv $HOME/az_lfs
source $HOME/az_lfs/bin/activate
```

To install the package, download the wheel from the Releases and just perform:

```bash
source $HOME/az_lfs/bin/activate
pip install <WHEEL_FILE>
```

In case you get error in `cryptography` installation, just perform an upgrade of `pip`:

```bash
source $HOME/az_lfs/bin/activate
pip install --upgrade pip
pip install <WHEEL_FILE>
```

## Usage

In order to perform any standard `lfs hsm_remove`, `lfs hsm_release`, `lfs hsm_archive` on a file or list of files just use the following syntax

```bash
amlfs_hsm_tools archive FILENAME1 [FILENAME2, FILENAME3...]
amlfs_hsm_tools release FILENAME1 [FILENAME2, FILENAME3...]
amlfs_hsm_tools remove FILENAME1 [FILENAME2, FILENAME3...]
```

## Checks

In order to perform a full filesystem check run the following command:

```bash
nohup find local/directory -type f -print0 | xargs -0 -n 1 sudo amlfs_hsm_tools check &
```

At the end of the check, all files will be marked as dirty / lost in case they require another archive operation.

## Contributing

This project welcomes contributions and suggestions.  Most contributions require you to agree to a
Contributor License Agreement (CLA) declaring that you have the right to, and actually do, grant us
the rights to use your contribution. For details, visit https://cla.microsoft.com.

When you submit a pull request, a CLA-bot will automatically determine whether you need to provide
a CLA and decorate the PR appropriately (e.g., label, comment). Simply follow the instructions
provided by the bot. You will only need to do this once across all repos using our CLA.

This project has adopted the [Microsoft Open Source Code of Conduct](https://opensource.microsoft.com/codeofconduct/).
For more information see the [Code of Conduct FAQ](https://opensource.microsoft.com/codeofconduct/faq/) or
contact [opencode@microsoft.com](mailto:opencode@microsoft.com) with any additional questions or comments.