# hostlist-light

A lightweight Python module for expanding and collecting compact cluster
hostlist expressions such as `n[1-3],x[01-02]y[1-2]`.

## Usage

```python
from hostlist_light import hostlist

hostlist.expand_hostlist("n[1-3],m1")        # ['n1', 'n2', 'n3', 'm1']
hostlist.collect_hostlist(["n1", "n2", "n3"])  # 'n[1-3]'
hostlist.collect_hostlist(["x1y1", "x2y2", "x1y2", "x2y1"])  # 'x[1-2]y[1-2]'
hostlist.parse_slurm_tasks_per_node("2(x3),1")  # [2, 2, 2, 1]
```

## API

- `expand_hostlist(hostlist, allow_duplicates=False, sort=False)` – expand an expression into host names.
- `collect_hostlist(hosts, silently_discard_bad=False)` – compress host names into an expression. Names containing brackets raise `BadHostlist` unless `silently_discard_bad=True`.
- `numeric_sort_key(name)` – sort key for numeric-aware ordering.
- `parse_slurm_tasks_per_node(s)` – parse `SLURM_TASKS_PER_NODE` syntax into a list of task counts.
- `BadHostlist` – raised on invalid input.

## Development

```sh
python -m venv venv
venv/bin/pip install -r requirements-test.txt
venv/bin/python -m pytest
```

## License

BSD 2-Clause. See [LICENSE](LICENSE).
