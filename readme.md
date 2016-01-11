# Knallender — Renewable ISO 8601 Calendar

Python script to create ISO 8601 compatible calendar sheets. Each row is one week, each page contains 10 weeks. Number of weeks, paper and cell sizes can all be configured.

Creates one PDF with 10 weeks starting with the current week:

```sh
python3 .
```

Uses a different week to start with:

```sh
python3 . <year> <week>
```

Creates 6 pages (more than a year):

```sh
python3 . --pages 6
```
