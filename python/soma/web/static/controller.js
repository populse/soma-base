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


async function update_controller_list_str(element) {
    await update_controller_then_update_dom(element, element.value.split(/\r?\n|\r|\n/g));
}


async function update_controller_list_int(element) {
    try {
        var value = element.value.trim().split(/\s/).map(x => toInt(x));
    } catch (error) {
        element.classList.add("has_error");
        return;
    }
    await update_controller_then_update_dom(element, value);
}


async function update_controller_list_float(element) {
    try {
        var value = element.value.trim().split(/\s/).map(x => toFloat(x));
    } catch (error) {
        element.classList.add("has_error");
        return;
    }
    await update_controller_then_update_dom(element, value);
}

// function new_list_item(id) {
//     backend.new_list_item(id, function (result) {
//         const element = document.getElementById(id);
//         if (result.error_type) {
//             return undefined;
//         } else {
//             return result['result'];
//         }
//     });
// }

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


async function build_controller_element(controller_element) {
    const controller_type = await backend.get_type(null);
    const controller_value = await backend.get_value(null);
    let sortable = [];
    for (var i in controller_type.properties) {
        sortable.push([i, controller_type.properties[i]]);
    }
    sortable.sort((a, b) => a[1].brainvisa.order - b[1].brainvisa.order);
    for (const i in sortable) {
        const field_name = sortable[i][0];
        const elements = build_elements(field_name, field_name, sortable[i][1], controller_value[field_name])
        for (const element of elements) {
            controller_element.appendChild(element);
        }
    }
}

function build_elements(id, label, schema, value) {
    const builder = window[`build_elements_${schema.type}`];
    if (builder !== undefined) {
        return builder(id, label, schema, value);
    }
    return []
}

function build_elements_string(id, label, schema, value) {
    if (schema.brainvisa) {
        const builder = window[`build_elements_${schema.brainvisa.path_type}`];
        if (builder) {
            return builder(id, label, schema, value);
        }
    }
    if (schema.enum) {
        return build_elements_enum(id, label, schema, value);
    }
    const input = document.createElement('input');
    input.id = id;
    input.type = "text";
    input.setAttribute("controller_type", schema.type);
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

function build_elements_integer(id, label, schema, value) {
    return build_elements_string(id, label, schema, value);
}


function build_elements_number(id, label, schema, value) {
    return build_elements_string(id, label, schema, value);
}

function build_elements_boolean(id, label, schema, value) {
    const checkbox = document.createElement('input');
    checkbox.id = id;
    checkbox.type = "checkbox";
    checkbox.setAttribute("controller_type", schema.type);
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

function build_elements_enum(id, label, schema, value) {
    const select = document.createElement('select');
    select.id = id;
    select.setAttribute("controller_type", "enum");
    select.addEventListener('change', async event => await update_controller_string(event.target));
    for (const i of schema.enum) {
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

function build_elements_file(id, label, schema, value) {
    const div = document.createElement('div');
    div.classList.add("button_and_element");
    
    const button = document.createElement('button');
    button.setAttribute('for', id);
    button.textContent = '📁';
    // const handler = window[`${schema.brainvisa.path_type}_selector`];
    // button.addEventListener('click', event => handler(event.target));
    div.appendChild(button);
    
    const input = document.createElement('input');
    input.id = id;
    input.type = "text";
    input.setAttribute("controller_type", schema.brainvisa.path_type);
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

function build_elements_directory(id, label, schema, value) {
    return build_elements_file(id, label, schema, value);
}


function build_elements_array(id, label, schema, value) {
    const builder = window[`build_elements_list_${schema.items.type}`];
    if (builder) {
        return builder(id, label, schema, value);
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
                for (const element of build_elements(new_id, `[${index}]`, schema.items, new_value)) {
                    fieldset.appendChild(element);
                }
            }
        });
        new_item.innerText = '⊕'
        legend.appendChild(new_item);
        const clear = document.createElement('button');
        clear.addEventListener('click', async event => await update_controller_then_update_dom(event.target.parentElement.parentElement, []));
        clear.innerText = '⊖'
        legend.appendChild(clear);
        fieldset.appendChild(legend);
    }
    for (const index in value) {
        for (const element of build_elements(`${id}/${index}`, `[${index}]`, schema.items, value[index])) {
            fieldset.appendChild(element);            
        }
    }
    return [fieldset];
}



window.addEventListener("backend_ready", async (event) => {
    const controller_elements = document.querySelectorAll("form.controller");
    controller_elements.forEach(function (controller_element) {
         build_controller_element(controller_element);
    });
});
