# FIRST South Carolina Data Scouting
FIRST SC Scouting Alliance data collection and sharing website

## Purpose

This project creates a website that is publicly accessible during FIRST Robotics Competition (FRC) matches to collect scouting data. Additional subpages provide endpoints for downloading data, viewing simple analyses, and documentation and help pages to introduce rookie teams to scouting and data analysis.

## Install

This is a Python Flask application which can be deployed locally (for testing) or on a web-accessible server.

### Application Structure

The FIRST SC Scouting Alliance website is written using Python Flask library and leverages Jinja templates to create dynamic, on-demand web pages to keep up with regularly changing scouting data.

- [main.py](main.py): creates the app, configures the DB, registers blueprints, and defines the `init-db` CLI command.
- [extensions.py](extensions.py): shared `basic_auth` and `migrate` instances. Import them from here to avoid circular imports.
- [database_model.py](database_model.py): defines the schema  (tables and fields) of the scouting database.
- [routes/](routes/): one blueprint per area of the website.
  - `main_routes.py`: `/` home page and `/confirmed`.
  - `scout_routes.py` (`/scout`): routing page, robot scouting data input, and data insert functions.
  - `report_routes.py` (`/report`): event and team stats, matplotlib graphs, raw data view, CSV export.
  - `pick_routes.py` (`/pick-list`): pick-list table. The picked list lives client-side in `localStorage` ([static/js/picklist.js](static/js/picklist.js)).
  - `info_routes.py` (`/info`): static help pages.
  - `admin_routes.py` (`/admin`): Covers team and event maintenance, data editing, the QA page (duplicate and missing reports), and FIRST API imports.
- [cron/](cron/): standalone scripts. Each builds its own minimal Flask app for DB access.
- [templates/](templates/): Jinja templates, organized by blueprint folder, extending `base.html`

## FAQ

#### Why aren't you scouting [data]?

The Scouting Alliance is founded with the goal of meeting the needs of the majority of teams. More uncommon questions can bloat data and add complexity for scouting volunteers to track, and so we focus on the basic quantitative information that can reduce the scouting workload for everyone.

#### Why isn't this in [other language]?

Great question. Python was chosen for ease of teaching to new students, availability of analytical libraries, and lightweight web applications. We're happy to consider replatforming in other languages but consider whether you have time to recode the entire project.