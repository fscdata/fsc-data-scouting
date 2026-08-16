# Developer To-Do List

## Short Term Projects

### Add logo and icon for branding

* Lightweight effort, easy HTML adjustments to templates. Logos available in Discord server.
* Make a favicon from minimal logo, adjust design of template to include logo on header of all pages.

### Bring more color to the website

* First year's focus was functionality, this year we want some more visual appeal.

### Additional graphs

* Specific graphs/data to be prioritized by Scouting Alliance members.
* Backend integration may get interesting based on multi-season transition of data fields, but this can still be started on.

### Include Statbotics EPA

* Code changes are in place, but full implementation is **on hold** due to Statbotics bug.
  * Server is returning 500 to all requests, not just for our application.
* Schema is in place in database.

## Medium Term Projects

## Long Term Projects

### Improve admin tools

Before and during events, there are a number of "background" processes which need to happen to prepare the system for upcoming matches. (Ensuring teams are entered, new events are entered, match participants are pulled from FIRST API...)

* Improve workflow of background operations for API queries
  * Webhooks?
  * Add error handling to avoid re-doing operations that might bork data
* Add documentation
* Determine how to arrange access for scouting leads during events
* Outline procedures and create documentation
  * how-to
  * responsibilities

### Overhaul schema to be dynamic and accomodate points from any season

* Big project, may require multiple developer involvement simultaneously.
* Not to be started until ~November 2026, after all 2026 season events are completed and data is accumulated.
* Take database archive before ANY work starts.
* Merge 2026-season-revision branch to develop and main.
* Begin new 2027-season branch from develop.
* Ref. `schema.md` outline of changes.