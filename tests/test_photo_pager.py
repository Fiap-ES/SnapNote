from ui.photo_pager import SLOTS, rotate_slot, swipe_destination

WIDTH = 360


def test_rotating_forward_brings_the_right_slide_to_the_center() -> None:
    assert [rotate_slot(slot, 1) for slot in SLOTS] == [1, -1, 0]


def test_rotating_backward_brings_the_left_slide_to_the_center() -> None:
    assert [rotate_slot(slot, -1) for slot in SLOTS] == [0, 1, -1]


def test_rotation_is_a_cycle_of_three() -> None:
    for slot in SLOTS:
        rotated = slot
        for _step in range(3):
            rotated = rotate_slot(rotated, 1)
        assert rotated == slot
        assert rotate_slot(rotate_slot(slot, 1), -1) == slot


def test_dragging_past_the_threshold_moves_to_the_neighbour() -> None:
    assert swipe_destination(-WIDTH * 0.3, WIDTH, 2, 6) == 3
    assert swipe_destination(WIDTH * 0.3, WIDTH, 2, 6) == 1


def test_short_drag_stays_on_the_same_photo() -> None:
    assert swipe_destination(-WIDTH * 0.1, WIDTH, 2, 6) == 2
    assert swipe_destination(WIDTH * 0.1, WIDTH, 2, 6) == 2
    assert swipe_destination(0, WIDTH, 2, 6) == 2


def test_edges_have_no_neighbour_to_move_to() -> None:
    assert swipe_destination(WIDTH * 0.9, WIDTH, 0, 6) == 0
    assert swipe_destination(-WIDTH * 0.9, WIDTH, 5, 6) == 5
    assert swipe_destination(-WIDTH * 0.9, WIDTH, 0, 1) == 0
