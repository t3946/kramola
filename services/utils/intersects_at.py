def intersects_at(
    first: tuple[int, int],
    second: tuple[int, int],
) -> tuple[int, int] | None:
    start1, end1 = first
    start2, end2 = second
    
    if start1 > end2 or end1 < start2:
        return None

    return (
        max(start1, start2),
        min(end1, end2)
    )

def _test():
    tests = [
        {
            "data": [(1, 10), (0, 2)],
            "result": (1, 2),
        },
        {
            "data": [(1, 10), (9, 11)],
            "result": (9, 10),
        },
        {
            "data": [(1, 10), (0, 11)],
            "result": (1, 10),
        },
        {
            "data": [(1, 10), (3, 5)],
            "result": (3, 5),
        },
        {
            "data": [(1, 10), (11, 12)],
            "result": None,
        },
        {
            "data": [(1, 10), (0, 0)],
            "result": None,
        },
    ]

    is_correct = True

    for test in tests:
        result = intersects_at(test["data"][0], test["data"][1])

        if test["result"] != result:
            print("Wrong test answer:")
            print(test)
            print(f"Result: {result}")
            is_correct = False
            break

    if is_correct:
        print("All right!")