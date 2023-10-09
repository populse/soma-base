var uniqueIndex = 0;

function toInt(x) {
    if (/^-?\d+$/.test(x)) {
        return parseInt(x);
    }
    throw new SyntaxError('Not a valid integer')
}


function toFloat(x) {
    if (/^[-+]?(?:\d+\.?|\.\d)\d*(?:[Ee][-+]?\d+)?$/.test(x)) {
        return parseFloat(x);
    }
    throw new SyntaxError('Not a valid number')
}


async function update_controller_then_update_dom(element, value) {
    try {
        await backend.set_value(element.id, value);
        element.classList.remove("has_error");
    }
    catch ( error ) {
        element.classList.add("has_error");
        throw( error );
    }
}


async function update_controller_string(element) {
    await update_controller_then_update_dom(element, element.value);
}


async function update_controller_boolean(element) {
    await update_controller_then_update_dom(element, !!element.checked);
}


async function update_controller_array_string(element) {
    await update_controller_then_update_dom(element, element.value.trim().split(/\r?\n|\r|\n/g));
}


async function update_controller_array_integer(element) {
    const int_array = element.value.trim().split(/\s+/);
    await update_controller_then_update_dom(element, int_array);
}


async function update_controller_array_number(element) {
    const int_array = element.value.trim().split(/\s+/);
    await update_controller_then_update_dom(element, int_array);
}


function update_dom(element, value) {
    let function_name = 'update_dom_' + element.getAttribute('controller_type');
    return window[function_name](element, value);
}


function update_dom_string(element, value)
{
    element.value = value;
}


function update_dom_integer(element, value)
{
    element.value = value.toString();
}


function update_dom_number(element, value)
{
    element.value = value.toString();
}


function update_dom_boolean(element, value)
{
    element.checked = value;
}


function update_dom_enum(element, value)
{
    element.value = value;
}


function update_dom_file(element, value)
{
    element.value = value;
}


function update_dom_directory(element, value)
{
    element.value = value;
}


function update_dom_object(element, value) {
    const id = element.getAttribute("id");
    for (const i in value) {
        update_dom(document.getElementById(`${id}/${i}`), value[i]);
    }
}

function update_dom_array(element, value) {
    update_dom_object(element, value);
}


function update_dom_list_str(element, value)
{
    element.value = value.map(x => x.toString()).join("\n");
}


function update_dom_list_int(element, value)
{
    update_dom_list_str(element, value);
}


function update_dom_list_float(element, value)
{
    update_dom_list_str(element, value);
}


// function file_selector(item) {
//     backend.file_selector(function (path) {
//         let id = item.getAttribute("for");
//         backend.set_value(id, path, x => update_dom(id, x));

//     });
// }

// function directory_selector(item) {
//     backend.directory_selector(function (path) {
//         let id = item.getAttribute("for");
//         backend.set_value(id, path, x => update_dom(id, x));
//     });
// }

// async function get_value(path) {
//     const url = controller_url + "/get_value";
//     const response = await fetch(url, {
//         method: 'POST',
//         headers: {
//             'Content-Type': 'application/json'
//         },
//         "body": "[]"
//     });
//     if (!response.ok) { 
//         throw new Error(`HTTP error: ${response.status}`);
//     }        
//     return (await response.json()).result;
// }

function resolve_schema_type(type, schema) {
    while ('$ref' in type) {
        const ref_path = type['$ref'].substr(2).split('/');
        let ref = schema;
        for (const i of ref_path) {
            ref = ref[i];
        }
        type = ref
    }
    if ('allOf' in type) {
        let result = {}
        const parent_types = type['allOf']
        for (let parent_type of parent_types) {
            parent_type =resolve_schema_type(parent_type, schema);
            for (const k in parent_type) {
                const v = parent_type[k];
                if (k == 'properties') {
                    result.properties = result.properties || {};
                    result.properties = {
                        ...result.properties,
                        ...v,
                    }
                } else {
                    result[k] = v
                }
            }
            for (const k in type) {
                const v = type[k]
                if (k == 'allOf' || k[0] == '$') {
                    continue;
                }
                if (k == 'properties') {
                    result.properties = result.properties || {};
                    result.properties = {
                        ...result.properties,
                        ...v,
                    }
                } else {
                    result[k] = v;
                }
            }
        }
        type = result
    }
    return type
}

async function build_controller_element(controller_element) {
    const controller_schema = await backend.get_schema();
    const controller_value = await backend.get_value(null);
    const controller_type = resolve_schema_type(controller_schema, controller_schema);
    const elements = build_elements_object(null, null, controller_type, controller_value, controller_schema);
    for (const element of elements) {
        controller_element.appendChild(element);
    }
}


function build_elements_object(id, label, type, value, schema) {
    let result = [];
    if (id) {
        var fieldset = document.createElement('fieldset');
        fieldset.id = id;
        fieldset.setAttribute("controller_type", "object");
        fieldset.classList.add('controller');
        if (id && (id.match(/\//g) || []).length > 1) {
            fieldset.classList.add('collapsed');
        }
        if (label) {
            const legend = document.createElement('legend');
            const l = document.createElement('label');
            l.setAttribute('for', id);
            l.addEventListener('click', event => event.target.parentElement.parentElement.classList.toggle('collapsed'));
            l.textContent = label;
            legend.appendChild(l);
            fieldset.appendChild(legend);
            if (type.brainvisa && type.brainvisa.value_items) {
                const new_item = document.createElement('button');
                new_item.addEventListener('click', async function (event) {
                    fieldset.classList.remove('collapsed');
                    async function validate_new_object_item(tmp_id, fieldset) {
                        const input = document.getElementById(tmp_id);
                        const key = await backend.new_named_item(fieldset.id, input.value);
                        if (key !== undefined) {
                            input.nextElementSibling.remove();
                            input.remove();
                            const new_id = `${fieldset.id}/${key}`;
                            type.properties = (await backend.get_type(id)).properties
                            const new_value = await backend.get_value(new_id);
                            for (const element of build_elements(new_id, key, type.brainvisa.value_items, new_value, schema)) {
                                fieldset.appendChild(element);
                            }
                        }
                    }
                    
                    
                    function cancel_new_object_item(tmp_id) {
                        const input = document.getElementById(tmp_id);
                        input.nextElementSibling.remove();
                        input.remove();
                    }
                                        const input = document.createElement('input');
                    input.id = "id" + uniqueIndex++;
                    input.classList.add('label');
                    input.setAttribute('for', id);
                    input.value = 'new_item';
                    input.addEventListener('keydown', function (event) {
                        if (event.key == 'Enter') {
                            validate_new_object_item(input.id, fieldset);
                        } else if (event.key == 'Escape') {
                            cancel_new_object_item(input.id, fieldset);
                        }
                    });
                    fieldset.appendChild(input);
                    input.select();
                    input.focus();
                    input.scrollIntoView({block: 'nearest', inline: 'nearest'});
                    const div = document.createElement('div');
                    fieldset.appendChild(div);
                    const ok = document.createElement('button');
                    ok.setAttribute('for', input.id);
                    ok.textContent = '✓';
                    ok.addEventListener('click', event => validate_new_object_item(input.id, fieldset));
                    div.appendChild(ok);
                    const cancel = document.createElement('button');
                    cancel.setAttribute('for', input.id);
                    cancel.textContent = '✗';
                    cancel.addEventListener('click', event => cancel_new_object_item(input.id, fieldset));
                    div.appendChild(cancel);
                });
                new_item.innerText = '+'
                legend.appendChild(new_item);
            }
        }
        result.push(fieldset);
    }
    let sortable = [];
    for (var i in type.properties) {
        sortable.push([i, type.properties[i]]);
    }
    sortable.sort((a, b) => a[1].brainvisa.order - b[1].brainvisa.order);
    for (const i in sortable) {
        const field_name = sortable[i][0];
        const elements = build_elements((id ? `${id}/${field_name}` : field_name), field_name, sortable[i][1], value[field_name], schema);
        for (const element of elements) {
            if (id) {
                fieldset.appendChild(element);
            } else {
                result.push(element);
            }
        }
    }
    return result;
}


function build_elements(id, label, type, value, schema) {
    type = resolve_schema_type(type, schema);
    const builder = window[`build_elements_${type.type}`];
    if (builder !== undefined) {
        return builder(id, label, type, value, schema);
    }
    return []
}

function build_elements_string(id, label, type, value, schema) {
    if (type.brainvisa) {
        const builder = window[`build_elements_${type.brainvisa.path_type}`];
        if (builder) {
            return builder(id, label, type, value, schema);
        }
    }
    if (type.enum) {
        return build_elements_enum(id, label, type, value, schema);
    }
    const input = document.createElement('input');
    input.id = id;
    input.type = "text";
    input.setAttribute("controller_type", type.type);
    input.addEventListener('change', async event => await update_controller_string(event.target));
    if (value !== undefined) {
        input.value = value.toString();
    }
    if (label) {
        const l = document.createElement('label');
        l.setAttribute('for', id);
        l.textContent = label;
        return [l, input];
    } else {
        return [input];
    }
}

function build_elements_integer(id, label, type, value, schema) {
    return build_elements_string(id, label, type, value, schema);
}


function build_elements_number(id, label, type, value, schema) {
    return build_elements_string(id, label, type, value, schema);
}

function build_elements_boolean(id, label, type, value, schema) {
    const checkbox = document.createElement('input');
    checkbox.id = id;
    checkbox.type = "checkbox";
    checkbox.setAttribute("controller_type", type.type);
    checkbox.addEventListener('change', async event => await update_controller_boolean(event.target));
    if (value) {
        checkbox.checked = true;
    }
    if (label) {
        const l = document.createElement('label');
        l.setAttribute('for', id);
        l.textContent = label;
        return [l, checkbox];
    } else {
        return [checkbox];
    }
}

function build_elements_enum(id, label, type, value, schema) {
    const select = document.createElement('select');
    select.id = id;
    select.setAttribute("controller_type", "enum");
    select.addEventListener('change', async event => await update_controller_string(event.target));
    for (const i of type.enum) {
        const option = document.createElement('option');
        option.value = i;
        option.textContent = i;
        if (i == value) {
            option.selected = true;
        }
        select.appendChild(option);
    }
    if (label) {
        const l = document.createElement('label');
        l.setAttribute('for', id);
        l.textContent = label;
        return [l, select];
    } else {
        return [select];
    }
}

function build_elements_file(id, label, type, value, schema) {
    const div = document.createElement('div');
    div.classList.add("button_and_element");
    
    const button = document.createElement('button');
    button.setAttribute('for', id);
    button.textContent = '📁';
    // const handler = window[`${type.brainvisa.path_type}_selector`];
    // button.addEventListener('click', event => handler(event.target));
    div.appendChild(button);
    
    const input = document.createElement('input');
    input.id = id;
    input.type = "text";
    input.setAttribute("controller_type", type.brainvisa.path_type);
    input.addEventListener('change', async event => await update_controller_string(event.target));
    if (value) {
        input.value = value;
    }
    div.appendChild(input);
    
    if (label) {
        const l = document.createElement('label');
        l.setAttribute('for', id);
        l.textContent = label;
        return [l, div];
    } else {
        return [input];
    }
}

function build_elements_directory(id, label, type, value, schema) {
    return build_elements_file(id, label, type, value, schema);
}


function build_elements_array(id, label, type, value, schema) {
    const builder = window[`build_elements_array_${type.items.type}`];
    if (builder) {
        return builder(id, label, type, value, schema);
    }
    const fieldset = document.createElement('fieldset');
    fieldset.id = id;
    fieldset.setAttribute("controller_type", "array");
    fieldset.classList.add('controller');
    if ((id.match(/\//g) || []).length > 1) {
        fieldset.classList.add('collapsed');
    }
    if (label) {
        const legend = document.createElement('legend');
        const l = document.createElement('label');
        l.setAttribute('for', id);
        l.addEventListener('click', event => event.target.parentElement.parentElement.classList.toggle('collapsed'));
        l.textContent = label;
        legend.appendChild(l);
        const new_item = document.createElement('button');
        new_item.addEventListener('click', async function (event) {
            const index = await backend.new_list_item(event.target.parentElement.parentElement.id);
            if (index !== undefined) {
                const new_id = `${id}/${index}`;
                const new_value = await backend.get_value(new_id);
                for (const element of build_elements(new_id, `[${index}]`, type.items, new_value, schema)) {
                    fieldset.appendChild(element);
                }
            }
        });
        new_item.innerText = '+'
        legend.appendChild(new_item);
        const clear = document.createElement('button');
        clear.addEventListener('click', async event => await update_controller_then_update_dom(event.target.parentElement.parentElement, []));
        clear.innerText = '⊖'
        legend.appendChild(clear);
        fieldset.appendChild(legend);
    }
    for (const index in value) {
        for (const element of build_elements(`${id}/${index}`, `[${index}]`, type.items, value[index], schema)) {
            fieldset.appendChild(element);            
        }
    }
    return [fieldset];
}


function build_elements_array_string(id, label, type, value, schema) {
    const textarea = document.createElement('textarea');
    textarea.id = id;
    textarea.setAttribute("controller_type", `array_${type.type}`);
    textarea.addEventListener('change', async event => await update_controller_array_string(event.target));
    const rows = Math.min(20, Math.max(5,value.length));
    textarea.setAttribute('rows', rows);
    if (value !== undefined) {
        textarea.textContent = value.join('\n');
    }
    if (label) {
        const l = document.createElement('label');
        l.setAttribute('for', id);
        l.textContent = label;
        return [l, textarea];
    } else {
        return [textarea];
    }
}


function build_elements_array_integer(id, label, type, value, schema) {
    const textarea = document.createElement('textarea');
    textarea.id = id;
    textarea.setAttribute("controller_type", `array_${type.type}`);
    textarea.addEventListener('change', async event => await update_controller_array_integer(event.target));
    if (value !== undefined) {
        textarea.textContent = value.join(' ');
    }
    if (label) {
        const l = document.createElement('label');
        l.setAttribute('for', id);
        l.textContent = label;
        return [l, textarea];
    } else {
        return [textarea];
    }
}

function build_elements_array_number(id, label, type, value, schema) {
    return build_elements_array_integer(id, label, type, value, schema);
}


window.addEventListener("backend_ready", async (event) => {
    const controller_elements = document.querySelectorAll("form.controller");
    controller_elements.forEach(function (controller_element) {
        if (navigator.userAgent.search('QtWebEngine') >= 0) {
            controller_element.classList.add('QtWebEngine');
        }
        build_controller_element(controller_element);
    });
});
