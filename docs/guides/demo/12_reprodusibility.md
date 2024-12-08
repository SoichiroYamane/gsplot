# 12. Reproducibility

`gsplot` is designed to have functions that can be used to reproduce the same plots. When plot with importing gsplot generates `gsplot_log.yml` in `~/.config/gsplot` directory. This file contains the version of `gsplot` and the commit hash of the repository. This file is used to reproduce the same plot in the future.

```yaml
versions:
- version: 0.0.1
  commits:
  - commit: 33b00054bd2b28d7f0815ea59ace33eda5178d17a
    date: '2024-12-02 21:16:47'
  - commit: 33b00054bd2b28d7f0815ea59ace33eda5178d17sdf
    date: '2024-12-02 21:16:55'
  - commit: 33b00054bd2b28d7f0815ea59ace33eda5178d17
  - commit: 676e16a4e9e5b389a3b4e6ce6c8393a73f9732fb
    date: '2024-12-02 21:31:24'
  - commit: d4cf59ab16933bbaea4ee36112bbca6843c04fad
    date: '2024-12-03 20:28:12'
```
