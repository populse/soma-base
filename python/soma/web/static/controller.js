function toInt(x) {
    if (/^-?\d+$/.test(x)) {
        return parseInt(x);
    }
    throw new SyntaxError('No a valid integer')
}


function toFloat(x) {
    if (/^[-+]?(?:\d+\.?|\.\d)\d*(?:[Ee][-+]?\d+)?$/.test(x)) {
        return parseFloat(x);
    }
    throw new SyntaxError('No a valid number')
}


function update_controller_str(item) {
    backend.set_value(item.id, item.value, x => update_dom_str(item, x));
}

function update_dom_str(item, result)
{
    if (result['error']) {
        item.classList.add("has_error");
    } else {
        item.classList.remove("has_error");
        item.value = result['value'];
    }
}

function update_controller_bool(item) {
    if (item.checked)
        backend.set_value(item.id, true, x => none);
    else
        backend.set_value(item.id, false, x => none);
}

function update_controller_list_str(item) {
    let value = item.value.split(/\r?\n|\r|\n/g)
    backend.set_value(item.id, value, x => update_dom_list_str(item, x));
}

function update_dom_list_str(item, result)
{
    if (result['error']) {
        item.classList.add("has_error");
    } else {
        item.classList.remove("has_error");
        item.value = result['value'].map(x => x.toString()).join("\n");
    }
}


function update_controller_list_int(item) {
    try {
        var value = item.value.trim().split(/\s/).map(x => toInt(x));
    } catch (error) {
        item.classList.add("has_error");
        return;
    }
    backend.set_value(item.id, value, x => update_dom_list_str(item, x));
}

function update_controller_list_float(item) {
    try {
        var value = item.value.trim().split(/\s/).map(x => toFloat(x));
    } catch (error) {
        item.classList.add("has_error");
        return;
    }
    backend.set_value(item.id, value, x => update_dom_list_str(item, x));
}
