from __future__ import annotations

from pprint import pprint

from chiller_plant_control_data.entries._shared import run_entry
from chiller_plant_control_data.flows.clean_data_flow import run


if __name__ == "__main__":
    pprint(run_entry("clean_data", run))

