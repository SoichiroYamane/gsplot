# 12. Reproducibility

`gsplot` is designed to have functions that can be used to reproduce the same plots. When plot with importing gsplot generates `gsplot_log.yml` in `~/.config/gsplot` directory. This file contains the version of `gsplot` and the commit hash of the repository. This file is used to reproduce the same plot in the future.

## Logger of Package Information

```yaml
versions:
- version: 0.0.1
  commits:
  - commit: 33b00054bd2b28d7f0815ea59ace33eda5178d17a
    date: '2024-12-02 21:16:47'
  - commit: 33b00054bd2b28d7f0815ea59ace33eda5178d17sdf
    date: 2024-12-02 21:16:55sd
- version: 0.0.2
  commits:
  - commit: ea1141e9c345fbaae4dc9f2eb5e1707268de9021
    date: '2024-12-14 20:25:52'
  - commit: 6260de51bb78df0cd30ca6d130a87e2c130677f9
    date: '2024-12-17 23:14:52'
- version: 0.0.5
  commits:
  - commit: 516eb39b353e4c110c9a9b4c505b902dfd099acb
    date: '2024-12-25 13:54:17'
  - commit: 37260f1530af2da661220d86a1baf246570f4d7a
    date: '2024-12-25 15:37:20'
```

## Store Metadata of gsplot

Metadata of `gsplot` can be stored in following files: `./.gsplot/metadata.yml`, `./.gsplot/config.json`, and `./.gsplot/history/history.txt`. The metadata file contains the version of `gsplot` and the commit hash of the repository. The config file contains the configuration of `gsplot`. The history file tracks all histories of configuration on the executed main file. This feature enables the user to reproduce the same plot in the future by using the metadata and config files.

### Configuration

To enable this feature, set `metadata` to `true` in the configuration file.

```json
{
  "metadata": true
}
```

### Example: Structure of Metadata

Matadata and config files are stored in the `.gsplot` directory.

```bash
$ tree
.
├── main.py
├── .gsplot
│   ├── metadata.yml
│   ├── config.json
│   └── history
│       └─── history.txt
```

#### metadata.yml

```yaml
date: '2024-12-26 15:55:35'
version: 0.0.5
commit: 6b818865da62342790933a079a65fea1e2d9e63e
```

#### config.json

```json
{
  "metadata": true
}
```

#### history.txt

```text
{"date": "2024-12-26 15:55:23", "version": "0.0.5", "commit": "6b818865da62342790933a079a65fea1e2d9e63e", "config": {"rich": {"traceback": {}}, "rcParams": {"xtick.major.pad": 6, "ytick.major.pad": 6}, "metadata": true}}
{"date": "2024-12-26 15:55:35", "version": "0.0.5", "commit": "6b818865da62342790933a079a65fea1e2d9e63e", "config": {"metadata": true}}
```
