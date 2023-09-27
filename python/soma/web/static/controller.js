function update_controller_text(item) {
    backend.set_value(item.id, item.value);
}

function update_controller_bool(item) {
    if (item.checked)
        backend.set_value(item.id, true);
    else
        backend.set_value(item.id, false);
}

function update_controller_list_str(item) {
    let value = item.value.split(/\r?\n|\r|\n/g)
    backend.set_value(item.id, value);
}

function update_controller_list_int(item) {
    let value = item.value.trim().split(/\s/).map(x => parseInt(x));
    backend.set_value(item.id, value);
}

function update_controller_list_float(item) {
    let value = item.value.trim().split(/\s/).map(x => parseFloat(x));
    backend.set_value(item.id, value);
}
