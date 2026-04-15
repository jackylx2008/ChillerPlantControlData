# Chiller Plant Control Data

This project follows a three-layer structure:

- `modules/`: reusable capabilities
- `flows/`: business orchestration
- `entries/`: independent entry scripts

The current step only includes project infrastructure:

- configuration loading from `config.yaml`
- local env injection from `common.env`
- shared runtime context
- centralized logging setup

