# Season-Agnostic Database Schema

> **Status: proposed 2027 season redesign, not yet implemented.**
> For the 2026 season, database still uses hardcoded per-season columns on
> `match_team_data` (see `database_model.py`). This document describes
> the target schema for making game-specific stats swappable every season
> without code/template rewrites, and how to query/render it once built.

## Background

Every FRC game has different scored actions (notes are scored one year, fuel is scored
the next). Hardcoding those as table columns means every kickoff requires new
migrations, new routes, and new templates. This schema separates two concerns:

* **What never changes season to season**:
  * team data structure (number, name)
  * events (date, location year)
  * match numbers
  * TBA/Statbotics
  * generic match-conduct flags (fouled, disabled, etc.).
* **What changes every season**: the specific scored fields a robot is evaluated on.

These season variables are described in a table (`game_field_schema`)
instead of hardcoded as data columns, and their values are stored in a
matching table (`match_team_field_values`) instead of a column per field.

## Table Structure

### `events` / `frc_teams` — unchanged

Same as today: `events` (event_id, code, name, date, year, active flag) and
`frc_teams` (team_id, team_name).

### `game_field_schema` — new

One row per scored field, per season. This is the source of truth that drives
the scouting form, table headers, and statistics aggregation.

| column | type | purpose |
|---|---|---|
| `field_id` | int, PK | |
| `event_year` | int | which season this field belongs to |
| `field_name` | string | key used to look up values; also the scouting form's field name |
| `label` | string | human-readable display text |
| `type` | string | `int` / `float` / `bool` / `string` — drives form widget, validation, and which typed column holds the value |
| `phase` | string | `auto` / `teleop` / `endgame` / `general` — for grouping in forms/tables |
| `agg` | string | `sum` / `avg` / `success_rate` / `none` — how raw records roll up into team stats |
| `display_order` | int | ordering within a phase |

Unique constraint on `(event_year, field_name)`.

**Example rows (2026 fuel game):**

```sql
INSERT INTO game_field_schema (event_year, field_name, label, type, phase, agg, display_order) VALUES
    (2026, 'auto_fuel_score', 'Auto Fuel Score', 'int', 'auto', 'sum', 1),
    (2026, 'teleop_fuel_score', 'Teleop Fuel Score', 'int', 'teleop', 'sum', 1),
    (2026, 'auto_climb_try', 'Auto Climb Attempted', 'bool', 'auto', 'success_rate', 2),
    (2026, 'auto_climbed', 'Auto Climb Succeeded', 'bool', 'auto', 'success_rate', 3),
    (2026, 'endgame_climb_level', 'Endgame Climb Level', 'int', 'endgame', 'avg', 1);
```

### `match_team_data` — trimmed to season-agnostic fields

| column | type | purpose |
|---|---|---|
| `record_id` | int, PK | |
| `event_id` | int, FK → `events.event_id` | |
| `match_number` | int | |
| `team_number` | int, FK → `frc_teams.team_id` | |
| `match_fouls` | int | |
| `match_tipped` | bool | |
| `match_broken` | bool | |
| `match_carded` | bool | |
| `match_disabled` | bool | |
| `match_absent` | bool | |
| `record_ip_address` | string | |
| `record_hidden` | bool | Admin-only field, hide bad data from display and stats calculations |

All game-specific fields (fuel score, climb, strategy flags, etc.) move out of this
table entirely.

### `match_team_field_values` — new (scouted data, EAV-style)

| column | type | purpose |
|---|---|---|
| `value_id` | int, PK | |
| `record_id` | int, FK → `match_team_data.record_id` | |
| `field_id` | int, FK → `game_field_schema.field_id` | |
| `value_int` | int, nullable | |
| `value_float` | float, nullable | |
| `value_bool` | bool, nullable | |
| `value_string` | string, nullable | |

Only one of the four `value_*` columns is populated per row, chosen by
`game_field_schema.type`. Unique constraint on `(record_id, field_id)`.

**Example row:** team 1234's auto fuel score of 6 in match 12 —

```sql
INSERT INTO match_team_field_values (record_id, field_id, value_int)
VALUES (501,
(SELECT field_id
FROM game_field_schema
WHERE event_year = 2026
AND field_name = 'auto_fuel_score'), 6);
```

### `calculated_data` — trimmed

Keeps the columns that are never season-specific: `record_id`, `team_number`,
`event_id`, `event_opr`, `event_dpr`, `event_ccwm`, `event_epa`, `tba_rank`,
`last_updated`. Season-specific derived stats (e.g. average climb level) move to:

### `calculated_field_values` — new

Same shape as `match_team_field_values`, but `calc_record_id` points at
`calculated_data.record_id` instead of `match_team_data.record_id`. Populated by
`cron/calculate_report_data.py` using each field's `agg` rule.

### `match_data` — unchanged, out of scope

The alliance-level table (`red_1_auto_climb`, etc.) has the same
hardcoded-per-season-column issue but is fed from an external API rather than the
scouting form; not addressed by this schema change.

## Dynamic Season Schema

Two queries are required to collect data. Since neither hardcodes field names,
the same SQL runs for any year that has rows in `game_field_schema`.

**1. Headers** (drives table/form column order):

```sql
SELECT field_id, field_name, label, type, phase, agg, display_order
FROM game_field_schema
WHERE event_year = :event_year
ORDER BY
    CASE phase WHEN 'auto' THEN 1 WHEN 'teleop' THEN 2 WHEN 'endgame' THEN 3 ELSE 4 END,
    display_order;
```

**2. Raw values for a match**, long-format (one row per team per field):

```sql
SELECT
    mtd.record_id,
    mtd.team_number,
    t.team_name,
    gfs.field_name,
    gfs.type,
    v.value_int, v.value_float, v.value_bool, v.value_string
FROM match_team_data mtd
JOIN frc_teams t ON t.team_id = mtd.team_number
LEFT JOIN match_team_field_values v ON v.record_id = mtd.record_id
LEFT JOIN game_field_schema gfs ON gfs.field_id = v.field_id
WHERE mtd.event_id = :event_id
  AND mtd.match_number = :match_number
ORDER BY mtd.team_number, gfs.display_order;
```

SQL can't pivot an unknown number of fields into named columns, so the long-format
result is pivoted into a per-team dictionary in Python before it reaches the template.

```python
from collections import defaultdict

teams = defaultdict(lambda: {"team_name": None, "fields": {}})
for row in db.session.execute(raw_query, {"event_id": event_id, "match_number": match_number}):
    team = teams[row.team_number]
    team["team_name"] = row.team_name
    value = {"int": row.value_int, "float": row.value_float,
             "bool": row.value_bool, "string": row.value_string}[row.type]
    team["fields"][row.field_name] = value
```

## Rendering in Jinja

The template loops over `field_headers` for both the header row and each body row,
instead of hardcoding a `<th>`/`<td>` per field. The same template file works
unchanged across seasons — only the data passed in changes.

```html
<table class="sortable">
    <tr>
        <th>Team Number</th>
        <th>Team Name</th>
        <th>TBA OPR</th>
        <th>TBA DPR</th>
        <th>TBA CCWM</th>
        <th>Statbotics EPA</th>
        {% for field in field_headers %}
        <th>{{ field.label }}</th>
        {% endfor %}
    </tr>

    {% for team in team_rows %}
    <tr>
        <td><a href="/report/team?number={{ team.team_number }}">{{ team.team_number }}</a></td>
        <td>{{ team.team_name }}</td>
        <td>{{ team.opr }}</td>
        <td>{{ team.dpr }}</td>
        <td>{{ team.ccwm }}</td>
        <td>{{ team.epa }}</td>
        {% for field in field_headers %}
        <td>{{ team.fields.get(field.field_name, 'N/A') }}</td>
        {% endfor %}
    </tr>
    {% endfor %}
</table>
```

Value formatting (rounding floats, rendering booleans as "Yes"/"No") should happen in
Python when building `team_rows`, not in the template, so it lives in one place
instead of being duplicated across every page that renders a stats table.

## Migration Plan

Additive migration first:
* add the new tables
* populate `game_field_schema` for 2026 from today's hardcoded fields
* backfill `match_team_field_values` from the existing columns
* verify the backfill matches the source columns exactly.

Once confirmed, second phase of migration: 
* drop the old columns from `match_team_data` and `calculated_data`

This two-step approach keeps the original data recoverable until
functionality and accuracy is confirmed by Scouting Alliance.
