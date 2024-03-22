# Web development introduction course

## Examples

```
$ python3 activitygen.py --courseid=2"
```

This will create `activities.md`, `activities.html`, and `activities.sh`. The last one is a shell script for creating the activities in a Moodle instance using [`moosh activity-add`](https://moosh-online.com/commands/#activity-add).

```
$ moosh course-create --fullname "Web Development" --numsections 1 web
$ ./activities.sh
```

### Using an alias for `moosh`

```
$ python3 activitygen.py --courseid=2 --moosh="~/Workspace/tmuras/moosh/moosh.php -n -p ~/Workspace/moodle/moodle"
```
