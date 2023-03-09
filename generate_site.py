#!/usr/bin/env python3

import importlib.util
import json
import logging
import os
import shutil
import sys

from jinja2 import FileSystemLoader, Environment

logging.basicConfig(stream=sys.stdout, level=logging.INFO)

LOG = logging.getLogger()
DEFAULT_CONFIG_PATH = "./yass_config.json"
DEFAULT_CONFIGS = {
    "data_dir": "./data",
    "global_template_parameters": {},
    "permanent_paths": ["CNAME", "static"],
    "site_dir": "./docs",
    "sitemap_file": "./sitemap.json",
    "static_dir": f"./docs/static",
    "static_url": "",
    "templates_dir": "./templates",
    "template_functions_file": None,
}

def read_json_file(filename):
    with open(filename) as f:
        return json.loads(f.read())


def render_and_write(yass_config, template_file, params, output_file):
    template_env = yass_config["template_env"]
    output = template_env.get_template(template_file).render(**params)

    with open(os.path.join(yass_config["site_dir"], output_file), "w") as f:
        f.write(output)


def generate_page_params(yass_config, level_path, level_data):
    params = {}
    if level_data.get("data_type"):
        with open(os.path.join(yass_config["data_dir"], level_path)) as f:
            params["data"] = f.read()
            if level_data.get("data_type") == "json":
                params["data"] = json.loads(params["data"])

    return params


def generate_level(yass_config, level_map, previous_level_path):
    print(level_map)
    level_name = level_map["route"]
    level_path = os.path.join(previous_level_path, level_name)
    output_file = os.path.join(level_path, "index.html")
    link = os.path.join("/", level_path)
    template = level_map.get("template", "template_contents.html")

    LOG.info(f"Generating: {previous_level_path} | {level_path} | {output_file} | {link} | {template}")

    if "children" in level_map:
        # generate children and get table of contents
        additional_params = {
            "contents": [
                generate_level(yass_config, child, level_path) for child in level_map["children"]
            ],
        }
    else:
        # single page
        additional_params = generate_page_params(yass_config, level_path, level_map)

    params = {
        "title": level_map["title"],
        "tab_title": level_map.get("tab_title", level_map["title"]),
        "previous_page": os.path.join("/", previous_level_path),
        "static_url": yass_config["static_url"],
        **yass_config["global_template_parameters"],
        **additional_params,
    }

    os.makedirs(os.path.join(yass_config["site_dir"], level_path), exist_ok=True)
    render_and_write(yass_config, template, params, output_file)

    return {
        "title": level_map["title"],
        "link": link,
    }


def generate_site(yass_config):
    return generate_level(yass_config, yass_config["sitemap"], previous_level_path="")


def generate_statics(yass_config):
    pass


def clear_directory(yass_config):
    site_dir = yass_config["site_dir"]
    permanent_paths = yass_config["permanent_paths"]
    paths = os.listdir(site_dir)
    for path in paths:
        if path in permanent_paths:
            continue
        path = os.path.join(site_dir, path)
        if os.path.isdir(path):
            shutil.rmtree(path)
        else:
            os.remove(path)


def create_template_env(yass_config):
    template_env = Environment(
        loader=FileSystemLoader(searchpath=yass_config["templates_dir"])
    )
    if yass_config["template_functions_file"]:
        spec = importlib.util.spec_from_file_location(
            "yass_custom",
            yass_config["template_functions_file"]
        )
        template_functions_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(template_functions_module)
        for (name, component) in template_functions_module.__dict__.items():
            if callable(component) and name.startswith('yass_'):
                template_env.globals[name[len('yass_'):]] = component
    return template_env


def main():
    yass_config_path = DEFAULT_CONFIG_PATH if len(sys.argv) == 1 else sys.argv[1]
    LOG.info(f"Using configuration from {yass_config_path}")
    yass_config = dict(DEFAULT_CONFIGS, **read_json_file(sys.argv[1]))
    LOG.info(f"Using configuration: {yass_config}")
    yass_config["sitemap"] = read_json_file(yass_config["sitemap_file"])
    yass_config["template_env"] = create_template_env(yass_config)

    LOG.info(f"Clearing target directory")
    clear_directory(yass_config)

    LOG.info("Starting generation ...")
    generate_site(yass_config)

    LOG.info("Generating statics if needed ...")
    generate_statics(yass_config)

    LOG.info("Generation complete")


if __name__ == "__main__":
    main()
