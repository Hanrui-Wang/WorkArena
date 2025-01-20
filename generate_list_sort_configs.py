import os
import pdb
import re
import itertools
import json
import random 

from tqdm import tqdm
from playwright.sync_api import sync_playwright
from playwright.sync_api import Page

from browsergym.workarena.tasks.list import __TASKS__

import os
os.environ['SNOW_INSTANCE_URL'] = 'https://dev210336.service-now.com'
os.environ['SNOW_INSTANCE_UNAME'] = 'admin'
os.environ['SNOW_INSTANCE_PWD'] = 'NRWn^1%0wjZd'

SORT_TASKS = [
    task for task in __TASKS__ if re.compile(r"^Sort\w+ListTask$").match(task.__name__)
]

def generate_all_configs_fixed_n_field(task, page: Page, n_fields_to_sort: int):
    
    list_info = task._extract_list_info(page)

    # Get available fields
    available_fields = list(list_info["columns"].keys())
    # ... remove forbidden fields
    available_fields = [f for f in available_fields if f not in task.forbidden_fields]

    field_txt = {k: x["label"] for k, x in list_info["columns"].items()}
    dir_txt = {"asc": "ascending", "desc": "descending"}


    # compute all field combinations
    all_sort_fields = list(itertools.combinations(available_fields, n_fields_to_sort))
    # compute all direction combinations
    all_sort_dirs = list(itertools.product(*[["asc", "desc"] for _ in range(n_fields_to_sort)]))

    # product of field combinations x direction combinations
    all_configs = list(itertools.product(all_sort_fields, all_sort_dirs))

    all_configs = [
        {
            "sort_fields": sort_fields,
            "sort_dirs": sort_dirs,
            "goal": f'Sort the "{list_info["title"]}" list by the following fields:\n'
            + "\n".join(
                [
                    f" - {field_txt[field]} ({dir_txt[dir]})"
                    for field, dir in zip(sort_fields, sort_dirs)
                ]
            ),
        }
        for sort_fields, sort_dirs in all_configs
    ]

    return all_configs

def generate_task_configs(task_class, n_configs, min_complexity=1, max_complexity=3):
    name = task_class.__name__
    task_name = re.sub("([a-z])([A-Z])", r"\1_\2", name).lower()
    
    seed = 1000

    task = task_class(seed=seed)
    task.min_sort_len = min_complexity
    task.max_sort_len = max_complexity
    with sync_playwright() as p:
        browser = p.chromium.launch()
        context = browser.new_context()  # Set the timeout here
        context.set_default_timeout(5000)
        page = context.new_page()
        task.setup(page=page)
        task._wait_for_ready(page)
        # task.cheat(page=page)
        for n_fields in range(min_complexity, max_complexity+1):
            all_configs = generate_all_configs_fixed_n_field(task=task, page=page, n_fields_to_sort=n_fields)
            if len(all_configs) >= n_configs: #randomly sample n_configs
                all_configs = random.sample(all_configs, n_configs)

            with open(f"tasks/{task_name}_configs_{n_fields}_fields_{len(all_configs)}_samples.json", "w") as f:
                json.dump(all_configs, f, indent=4, sort_keys=True)
            print(f"Generated {len(all_configs)} configs for {task_name} with {n_fields} fields")

    task.teardown()


if __name__ == "__main__":
    # pdb.set_trace()
    random.seed(42)

    for task in SORT_TASKS: # Only generate configs for the first task
        generate_task_configs(task, n_configs=1000)


