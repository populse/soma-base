def dict_to_table(data_dict, shape_dict):
    """Transform a dictionary into a table shape
    (list of list, each sublist having the same size)

    The first line will be the header (name of columns).

    shape_dict will help setting names to columns.

    For instance::

        data_dict = {
            0: {'areas': {0: 23483.013671875,
                          2: 325.46331787109375,
                          7: 1300.6187744140625},
                'lengths': {0: 2225.728,
                            2: 80.755554,
                            7: 323.5833,
                            8: 103.076324}},
            1: {'areas': {2: 350.5135}}
        }
        shape_dict = {'timestep': {'areas': {'parcel': 'area'},
                                   'lengths': {'parcel': 'length'}}}
        dict_to_table(data_dict, shape_dict)

    will output::

        [['timestep', 'parcel', 'area', 'length'],
         [0, 0, 23483.013671875, 2225.728],
         [0, 2, 325.46331787109375, 80.755554],
         [0, 7, 1300.6187744140625, 323.5833],
         [0, 8, None, 103.076324],
         [1, 2, 350.5135, None]]

    At each level of the data dict, some additional, fixed, attributes, may
    be specified in an optional "fixed_attributes" sub-dict. Ex::

        data_dict = {
            0: {'areas': {0: 23483.013671875,
                          2: 325.46331787109375,
                          7: 1300.6187744140625},
                'lengths': {0: 2225.728,
                            2: 80.755554,
                            7: 323.5833,
                            8: 103.076324}},
            1: {'areas': {2: 350.5135}},
            'fixed_attributes': {'subject': 'maman'},
        }

    will output (with the same shape_dict)::

        [['subject', 'timestep', 'parcel', 'area', 'length'],
         ['maman', 0, 0, 23483.013671875, 2225.728],
         ['maman', 0, 2, 325.46331787109375, 80.755554],
         ['maman', 0, 7, 1300.6187744140625, 323.5833],
         ['maman', 0, 8, None, 103.076324],
         ['maman', 1, 2, 350.5135, None]]
    """

    todo = [(data_dict, shape_dict, {})]
    line_items = []
    while todo:
        data, shape, keys = todo.pop(0)
        if isinstance(data, dict):
            if "fixed_attributes" in data:
                keys.update(data["fixed_attributes"])
                data = dict(data)
                del data["fixed_attributes"]
            if len(shape) == 1:
                key, sshape = next(iter(shape.items()))
                for k, v in data.items():
                    keys = dict(keys)
                    keys[key] = k
                    todo.append((v, sshape, keys))
            else:
                for key, sshape in shape.items():
                    if key in data:
                        todo.append((data[key], sshape, keys))
        else:
            line = dict(keys)
            line[shape] = data  # shape is normally just a string now
            line_items.append(line)

    if len(line_items) == 0:
        return []

    hdr = list(line_items[0].keys())
    keys = {k: i for i, k in enumerate(hdr)}
    for line in line_items:
        for k, v in line.items():
            if k not in hdr:
                keys[k] = len(hdr)
                hdr.append(k)
    lines = []
    for line_item in line_items:
        l0 = [line_item.get(k) for k in hdr]
        found = False
        for line in lines:
            eq = True
            for e, v in zip(line, l0):
                if e is not None and v is not None and e != v:
                    eq = False
                    break
            if eq:  # all values present in both are the same
                # merge lines
                found = True
                for i, v in enumerate(l0):
                    if v is not None:
                        line[i] = v
                break
        if not found:
            lines.append(l0)

    return [hdr] + lines
