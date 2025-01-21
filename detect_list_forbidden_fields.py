

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
from browsergym.core.env import BrowserEnv

import os
os.environ['SNOW_INSTANCE_URL'] = 'https://dev210336.service-now.com'
os.environ['SNOW_INSTANCE_UNAME'] = 'admin'
os.environ['SNOW_INSTANCE_PWD'] = 'NRWn^1%0wjZd'

SORT_TASKS = [
    task for task in __TASKS__ if re.compile(r"^Sort\w+ListTask$").match(task.__name__)
]


def detect_task_forbidden_fields(task_class):
    name = task_class.__name__
    task_name = re.sub("([a-z])([A-Z])", r"\1_\2", name).lower()
    
    seed = 1000

    task = task_class(seed=seed)
    task.min_sort_len = 1
    task.max_sort_len = 1

    with sync_playwright() as p:
        browser = p.chromium.launch()
        context = browser.new_context()  # Set the timeout here
        context.set_default_timeout(5000)
        page = context.new_page()
        task.setup(page=page)
        task._wait_for_ready(page)
        # task.cheat(page=page)
        list_info = task._extract_list_info(page)
    task.teardown()

    # Get available fields
    available_fields = list(list_info["columns"].keys())
    # ... remove forbidden fields
    available_fields = [f for f in available_fields if f not in task.forbidden_fields]

    field_txt = {k: x["label"] for k, x in list_info["columns"].items()}

    additional_forbidden_fields = []
    for field in tqdm(available_fields, desc=f"Detecting forbidden fields for {task_name}", ncols=150):
        fixed_config = {
            "sort_fields": [field],
            "sort_dirs": ["asc"],
            "goal": f'Sort the "{list_info["title"]}" list by the following fields:\n'
            + "\n".join(
                [
                    f" - {field_txt[field]} (ascending))"
                ]
            ),
        }

        # print(fixed_config)
    
        env = BrowserEnv(task_entrypoint=task_class, task_kwargs = {'fixed_config': fixed_config}, headless=True, slow_mo=1000, timeout=10000)

        env.reset()
        env.context.set_default_timeout(10000)

        try:
            env.task.cheat(env.page, env.chat.messages)
        except Exception as e:
            print(f"Error cheating on task {task_name} with seed {seed}: {str(e)}")
            additional_forbidden_fields.append(field)

        env.close()
    print(task_class, additional_forbidden_fields)


if __name__ == "__main__":
    # pdb.set_trace()
    random.seed(42)

    for task in SORT_TASKS[2:]: # Only generate configs for the first task
        detect_task_forbidden_fields(task)


