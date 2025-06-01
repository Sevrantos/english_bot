def class_range(class_number):
    if class_number < 5:
        return 1, 4
    if class_number < 10:
        return 5, 9

    return 10, 11