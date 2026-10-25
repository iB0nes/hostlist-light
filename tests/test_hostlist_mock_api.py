import pytest

import hostlist_light.hostlist as hostlist


def test_expand_hostlist_basic_range():
    result = hostlist.expand_hostlist("n[001-003]")
    print(f"result: {result}")
    assert result == ["n001", "n002", "n003"]


def test_expand_hostlist_multiple_parts_withexpand_rangelist_padding():
    assert hostlist.expand_hostlist("n[9-10],d[01-02]") == [
        "n9",
        "n10",
        "d01",
        "d02",
    ]


def test_expand_hostlist_deduplicates_by_default():
    assert hostlist.expand_hostlist("n1,n1,n2") == ["n1", "n2"]


def test_expand_hostlist_allow_duplicates_true():
    assert hostlist.expand_hostlist("n1,n1,n2", allow_duplicates=True) == ["n1", "n1", "n2"]


def test_expand_hostlist_sort_flag():
    assert hostlist.expand_hostlist("n2,n10,n1", sort=True) == ["n1", "n2", "n10"]


def test_expand_hostlist_unbalanced_brackets_raises():
    with pytest.raises(hostlist.BadHostlist):
        hostlist.expand_hostlist("n[1-3")


def test_expand_hostlist_nested_brackets_raises():
    with pytest.raises(hostlist.BadHostlist):
        hostlist.expand_hostlist("n[[1-2]]")


def test_expand_part_empty_string():
    assert hostlist.expand_part("") == [""]


def test_expand_part_cartesian_product():
    assert hostlist.expand_part("x[1-2]y[1-2]") == ["x1y1", "x1y2", "x2y1", "x2y2"]


def test_expand_rangelist_combines_ranges():
    assert hostlist.expand_rangelist("n", "1-2,4") == ["n1", "n2", "n4"]


def test_expand_range_single_number():
    assert hostlist.expand_range("n", "14") == ["n14"]


def test_expand_range_interval_with_width():
    assert hostlist.expand_range("n", "01-03") == ["n01", "n02", "n03"]


def test_expand_range_bad_syntax_raises():
    with pytest.raises(hostlist.BadHostlist):
        hostlist.expand_range("n", "a-b")


def test_expand_range_start_greater_than_stop_raises():
    with pytest.raises(hostlist.BadHostlist):
        hostlist.expand_range("n", "5-2")


def test_remove_duplicates_keeps_order():
    assert hostlist.remove_duplicates(["n2", "n1", "n2", "n1", "n3"]) == ["n2", "n1", "n3"]


def test_collect_hostlist_simple_range():
    assert hostlist.collect_hostlist(["n1", "n2", "n3"]) == "n[1-3]"


def test_collect_hostlist_removes_duplicates_and_ignores_blank_lines():
    assert hostlist.collect_hostlist([" n1 ", "", "n1", "n2", "   "]) == "n[1-2]"


def test_collect_hostlist_forbidden_characters_raises():
    with pytest.raises(hostlist.BadHostlist):
        hostlist.collect_hostlist(["n[1]"])


def test_collect_hostlist_forbidden_characters_can_be_discarded():
    assert hostlist.collect_hostlist(["n1", "n[2]", "n2"], silently_discard_bad=True) == "n[1-2]"


def test_collect_hostlist_multidimensional_grouping():
    hosts = ["x1y1", "x2y2", "x1y2", "x2y1"]
    assert hostlist.collect_hostlist(hosts) == "x[1-2]y[1-2]"


def test_collect_hostlist_1_single_pass_collects_rightmost_numeric_part():
    left_right = [("n1", ""), ("n2", "")]
    result, looping = hostlist.collect_hostlist_1(left_right)
    assert result == [("n", "[1-2]")]
    assert looping is True


def test_format_range_single_value():
    assert hostlist.format_range(7, 7, 2) == "07"


def test_format_range_span():
    assert hostlist.format_range(3, 12, 2) == "03-12"


def test_numeric_sort_key_supports_mixed_prefixes_and_leading_numeric_tokens():
    values = ["x10y", "x9z8", "9z8"]
    assert sorted(values, key=hostlist.numeric_sort_key) == ["9z8", "x9z8", "x10y"]


def test_parse_slurm_tasks_per_node_basic():
    assert hostlist.parse_slurm_tasks_per_node("2(x3),1") == [2, 2, 2, 1]


def test_parse_slurm_tasks_per_node_without_repetition():
    assert hostlist.parse_slurm_tasks_per_node("4,2,1") == [4, 2, 1]


def test_parse_slurm_tasks_per_node_bad_syntax_raises():
    with pytest.raises(hostlist.BadHostlist):
        hostlist.parse_slurm_tasks_per_node("2(x),1")


def test_parse_slurm_tasks_per_node_too_large_repetition_raises():
    with pytest.raises(hostlist.BadHostlist):
        hostlist.parse_slurm_tasks_per_node(f"1(x{hostlist.MAX_SIZE + 1})")
