function update_controller_text(item) {
    backend.set_value(item.id, item.value);
}

function update_controller_bool(item) {
    if (item.checked)
        backend.set_value(item.id, true);
    else
        backend.set_value(item.id, false);
}
