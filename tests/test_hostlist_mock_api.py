"""Hostlist light tests for the mock API."""
import pytest

from hostlist_light import hostlist


def test_expand_hostlist_basic_range():
    """Test basic hostlist expansion with a simple range."""
    result = hostlist.expand_hostlist("n[001-003]")
    print(f"result: {result}")
    assert result == ["n001", "n002", "n003"]


def test_expand_hostlist_multiple_parts_withexpand_rangelist_padding():
    """Test hostlist expansion with multiple parts and rangelist padding."""
    assert hostlist.expand_hostlist("n[9-10],d[01-02]") == [
        "n9",
        "n10",
        "d01",
        "d02",
    ]


def test_expand_hostlist_deduplicates_by_default():
    """Test that hostlist expansion deduplicates results by default."""
    assert hostlist.expand_hostlist("n1,n1,n2") == ["n1", "n2"]


def test_expand_hostlist_allow_duplicates_true():
    """Test that hostlist expansion allows duplicates when specified."""
    assert hostlist.expand_hostlist("n1,n1,n2", allow_duplicates=True) == ["n1", "n1", "n2"]


def test_expand_hostlist_sort_flag():
    """Test that hostlist expansion sorts results when specified."""
    assert hostlist.expand_hostlist("n2,n10,n1", sort=True) == ["n1", "n2", "n10"]


def test_expand_hostlist_unbalanced_brackets_raises():
    """Test that unbalanced brackets in hostlist expansion raise an exception."""
    with pytest.raises(hostlist.BadHostlist):
        hostlist.expand_hostlist("n[1-3")


def test_expand_hostlist_nested_brackets_raises():
    """Test that nested brackets in hostlist expansion raise an exception."""
    with pytest.raises(hostlist.BadHostlist):
        hostlist.expand_hostlist("n[[1-2]]")


def test_expand_part_empty_string():
    """Test that expanding an empty string returns a list with an empty string."""
    assert hostlist.expand_part("") == [""]


def test_expand_part_cartesian_product():
    """Test that expanding a part with multiple ranges produces the Cartesian product."""
    assert hostlist.expand_part("x[1-2]y[1-2]") == ["x1y1", "x1y2", "x2y1", "x2y2"]


def test_expand_rangelist_combines_ranges():
    """Test that expanding a rangelist combines multiple ranges correctly."""
    assert hostlist.expand_rangelist("n", "1-2,4") == ["n1", "n2", "n4"]


def test_expand_range_single_number():
    """Test that expanding a single number returns the correct result."""
    assert hostlist.expand_range("n", "14") == ["n14"]


def test_expand_range_interval_with_width():
    """Test that expanding a range with leading zeros returns the correct results."""
    assert hostlist.expand_range("n", "01-03") == ["n01", "n02", "n03"]


def test_expand_range_bad_syntax_raises():
    """Test that expanding a range with bad syntax raises an exception."""
    with pytest.raises(hostlist.BadHostlist):
        hostlist.expand_range("n", "a-b")


def test_expand_range_start_greater_than_stop_raises():
    """Test that expanding a range where the start is greater than the stop raises an exception."""
    with pytest.raises(hostlist.BadHostlist):
        hostlist.expand_range("n", "5-2")


def test_remove_duplicates_keeps_order():
    """Test that removing duplicates keeps the order of first occurrences."""
    assert hostlist.remove_duplicates(["n2", "n1", "n2", "n1", "n3"]) == ["n2", "n1", "n3"]


def test_collect_hostlist_simple_range():
    """Test that collecting a simple range produces the correct hostlist."""
    assert hostlist.collect_hostlist(["n1", "n2", "n3"]) == "n[1-3]"


def test_collect_hostlist_removes_duplicates_and_ignores_blank_lines():
    """Test that collecting a hostlist removes duplicates and ignores blank lines."""
    assert hostlist.collect_hostlist([" n1 ", "", "n1", "n2", "   "]) == "n[1-2]"


def test_collect_hostlist_forbidden_characters_raises():
    """Test that collecting a hostlist with forbidden characters raises an exception."""
    with pytest.raises(hostlist.BadHostlist):
        hostlist.collect_hostlist(["n[1]"])


def test_collect_hostlist_forbidden_characters_can_be_discarded():
    """Test that collecting a hostlist with forbidden characters can discard them when specified."""
    assert hostlist.collect_hostlist(["n1", "n[2]", "n2"], silently_discard_bad=True) == "n[1-2]"


def test_collect_hostlist_multidimensional_grouping():
    """Test that collecting a hostlist with multidimensional grouping produces the correct result."""
    hosts = ["x1y1", "x2y2", "x1y2", "x2y1"]
    assert hostlist.collect_hostlist(hosts) == "x[1-2]y[1-2]"


def test_collect_hostlist_1_single_pass_collects_rightmost_numeric_part():
    """Test that collect_hostlist_1 collects the rightmost numeric part correctly."""
    left_right = [("n1", ""), ("n2", "")]
    result, looping = hostlist.collect_hostlist_1(left_right)
    assert result == [("n", "[1-2]")]
    assert looping is True


def test_format_range_single_value():
    """Test that format_range formats a single value correctly."""
    assert hostlist.format_range(7, 7, 2) == "07"


def test_format_range_span():
    """Test that format_range formats a span of values correctly."""
    assert hostlist.format_range(3, 12, 2) == "03-12"


def test_numeric_sort_key_supports_mixed_prefixes_and_leading_numeric_tokens():
    """Test that numeric_sort_key supports mixed prefixes and leading numeric tokens."""
    values = ["x10y", "x9z8", "9z8"]
    assert sorted(values, key=hostlist.numeric_sort_key) == ["9z8", "x9z8", "x10y"]


def test_parse_slurm_tasks_per_node_basic():
    """Test that parsing SLURM tasks per node works correctly for a basic case."""
    assert hostlist.parse_slurm_tasks_per_node("2(x3),1") == [2, 2, 2, 1]


def test_parse_slurm_tasks_per_node_without_repetition():
    """Test that parsing SLURM tasks per node without repetition works correctly."""
    assert hostlist.parse_slurm_tasks_per_node("4,2,1") == [4, 2, 1]


def test_parse_slurm_tasks_per_node_bad_syntax_raises():
    """Test that parsing SLURM tasks per node with bad syntax raises an exception."""
    with pytest.raises(hostlist.BadHostlist):
        hostlist.parse_slurm_tasks_per_node("2(x),1")


def test_parse_slurm_tasks_per_node_too_large_repetition_raises():
    """Test that parsing SLURM tasks per node with a repetition that is too large raises an exception."""
    with pytest.raises(hostlist.BadHostlist):
        hostlist.parse_slurm_tasks_per_node(f"1(x{hostlist.MAX_SIZE + 1})")
