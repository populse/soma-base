'use strict';

var QtWebEngine = (navigator.userAgent.search('QtWebEngine') >= 0);
var uniqueIndex = 0;
var WebBackend;
const backend_ready = new Event('backend_ready');

if (QtWebEngine) {
    const script = document.createElement('script');
    script.type = 'text/javascript';
    script.src = 'qrc:///qtwebchannel/qwebchannel.js';
    document.head.appendChild(script);

    WebBackend = class {
        web_channel;
        backend;

        constructor(backend_url) {

            window.addEventListener("load", (event) => {
                this.web_channel = new QWebChannel(qt.webChannelTransport,
                    async (channel) => {
                        this.backend = this.web_channel.objects.backend;
                        window.dispatchEvent(backend_ready);
                        const controller_elements = document.querySelectorAll(".controller");
                        controller_elements.forEach(async (controller_element) => {
                            controller_element.classList.add('QtWebEngine');
                            const dom_controller = new DomController(controller_element);
                            dom_controller.build_dom();
                    });
                });
            });
        }

        async  call(name, path, ...params) {
            let named_path;
            if (path === undefined) {
                named_path = name;
            } else {
                named_path = `${name}/${path}`;
            }
            const data = await this.backend.call(named_path, params);
            if (data._json_error_type) {
                throw new Error(`${data._json_error_message}`);
            } else {
                return data._json_result;
            }
        }
    }
} else {
    WebBackend = class {
        backend_url;

        constructor(backend_url) {
            this.backend_url = backend_url;
            window.addEventListener("load", async (event) => {
                window.dispatchEvent(backend_ready);
                const controller_elements = document.querySelectorAll(".controller");
                controller_elements.forEach((controller_element) => {
                    this.dom_controller = new DomController(controller_element);
                    this.dom_controller.build_dom();
                });
            });

        }

        async call(name, path, ...params) {
            let named_path;
            if (path === undefined) {
                named_path = name;
            } else {
                named_path = `${name}/${path}`;
            }
            const response = await fetch(`${this.backend_url}/${named_path}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(params)
            });
            if (! response.ok) {
                throw new Error(`HTTP error: ${response.status}`);
            }

            const data = await response.json();
            if (data._json_error_type) {
                throw new Error(`${data._json_error_message}`);
            } else {
                return data._json_result;
            }
        }
    }
}

class DomController {
    resolve_schema_type(type) {
        if (type == null || type == undefined)
            return type;
        while ('$ref' in type) {
            const ref_path = type['$ref'].substr(2).split('/');
            let ref = this.schema;
            for (const i of ref_path) {
                ref = ref[i];
            }
            type = ref
        }
        if ('allOf' in type) {
            let result = {}
            const parent_types = type['allOf']
            for (let parent_type of parent_types) {
                parent_type = this.resolve_schema_type(parent_type);
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


    constructor (controller_element) {
        this.controller_element = controller_element;
        this.controller_name = controller_element.getAttribute('name');
        if ( ! this.controller_name ) {
            this.controller_name = 'controller';
        }
    }

    async backend_call(name, path, ...params) {
        let p;
        if (path === undefined) {
            p = this.controller_name;
        } else {
            p = `${this.controller_name}/${path}`;
        }
        return await web_backend.call(name, p, ...params);
    }

    async build_dom() {
        const view = await this.backend_call('get_view');
        this.schema = view.schema;
        this.status = view.status;
        if (this.controller_element.hasAttribute('read_only')) {
            await this.set_status(`${this.controller_name}/read_only`, true);
        }
        const elements = this.build_elements(null, null, false, this.schema, view.value);
        for (const element of elements) {
            this.controller_element.appendChild(element);
        }
    }


    get_status(id) {
        let splitted = id.split('/');
        splitted[splitted.length-1] = '_' + splitted[splitted.length-1];
        return this.status[splitted.join('/')];
    }


    async set_status(path, value) {
        const p = await this.backend_call('set_status', `${controller_name}/${id}`, value);
        let splitted = p.split('/');
        splitted.remove(0);
        path = splitted.join('/');
        this.status[path] = value;
    }


    is_read_only(id) {
        if (this.status._read_only) {
            return true;
        }
        const result = !! this.get_status(`${id}/readonly`);
    }


    static create_delete_button(parent, id) {
        const button = document.createElement('button');
        button.type = 'button';
        button.innerText = '✗';
        button.classList.add('delete');
        button.setAttribute('for', id);
        parent.appendChild(button);
        return button;
    }


    build_elements(id, label, deletable, type, value) {
        type = this.resolve_schema_type(type);
        if (type != undefined && type != null)
        {
            const builder = this[`build_elements_${type.type}`];
            if (builder !== undefined) {
                let result = builder.bind(this)(id, label, deletable, type, value);
                if (result.length == 2) {
                    const splitter = document.createElement('div');
                    splitter.classList.add('grid-splitter');
                    function start_splitter(event) {
                        splitter.reference_client_x = event.clientX;
                        splitter.reference_width = splitter.previousElementSibling.getBoundingClientRect().width;
                        document.addEventListener('mousemove', change_splitter);
                        document.addEventListener('mouseup', stop_splitter);
                    }
                    function stop_splitter(event) {
                        document.removeEventListener('mousemove', change_splitter);
                        document.removeEventListener('mouseup', stop_splitter);
                    }
                    function change_splitter(event) {
                        const width = splitter.reference_width + event.clientX - splitter.reference_client_x;
                        splitter.parentElement.style['grid-template-columns'] = `${width}px 0.3em 1fr`;
                    }
                    splitter.addEventListener('mousedown', start_splitter);
                    result.splice(1, 0, splitter);
                }
                return result;
            }
        }
        return []
    }


    build_elements_object(id, label, deletable, type, value) {
        let result = [];
        if (label) {
            var fieldset = document.createElement('fieldset');
            fieldset.id = id;
            fieldset.setAttribute("controller_type", "object");
            fieldset.classList.add('controller');
            if (id && (id.match(/\//g) || []).length > 2) {
                fieldset.classList.add('collapsed');
            }
            const legend = document.createElement('legend');
            fieldset.appendChild(legend);
            if (label) {
                const l = document.createElement('label');
                l.setAttribute('for', id);
                l.addEventListener('click', async event => {
                    const fieldset = event.target.parentElement.parentElement;
                    fieldset.classList.toggle('collapsed');
                    await this.backend_call('set_status', `${id}/_collapsed`, fieldset.classList.contains('collapsed'));
                });
                l.textContent = label;
                legend.appendChild(l);
                if (type.brainvisa && type.brainvisa.value_items && !this.is_read_only(id)) {
                    const new_item = document.createElement('button');
                    new_item.type = 'button';
                    new_item.addEventListener('click', async (event) => {
                        if (fieldset.classList.contains('collapsed')) {
                            fieldset.classList.remove('collapsed');
                            await this.backend_call('set_status', `${id}/_collapsed`, false);
                        }
                        const validate_new_object_item = async (tmp_id, fieldset) => {
                            const input = document.getElementById(tmp_id);
                            const key = await this.backend_call('new_named_item', fieldset.id, input.value);
                            if (key !== undefined) {
                                input.nextElementSibling.remove();
                                input.remove();
                                const new_id = `${fieldset.id}/${key}`;
                                type.properties = (await this.backend_call('get_type', id)).properties
                                const new_value = await this.backend_call('get_value', new_id);
                                const deletable = ! this.is_read_only(id);
                                for (const element of this.build_elements(new_id, key, deletable, type.brainvisa.value_items,  new_value)) {
                                    fieldset.appendChild(element);
                                }
                            }
                        }


                        const cancel_new_object_item = (tmp_id) => {
                            const input = document.getElementById(tmp_id);
                            input.nextElementSibling.remove();
                            input.remove();
                        }
                        const input = document.createElement('input');
                        input.id = "id" + uniqueIndex++;
                        input.classList.add('label');
                        input.setAttribute('for', id);
                        input.value = 'new_item';
                        input.addEventListener('keydown', (event) => {
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
                        ok.type == 'button';
                        ok.setAttribute('for', input.id);
                        ok.textContent = '✓';
                        ok.addEventListener('click', event => validate_new_object_item(input.id, fieldset));
                        div.appendChild(ok);
                        const cancel = document.createElement('button');
                        cancel.type = 'button';
                        cancel.setAttribute('for', input.id);
                        cancel.textContent = '✗';
                        cancel.addEventListener('click', event => cancel_new_object_item(input.id, fieldset));
                        div.appendChild(cancel);
                    });
                    new_item.innerText = '+';
                    legend.appendChild(new_item);
                }
            }
            if (deletable) var delete_button = this.constructor.create_delete_button(legend, id);
            result.push(fieldset);
        }
        let sortable = [];
        for (var i in type.properties) {
            sortable.push([i, type.properties[i]]);
        }
        sortable.sort((a, b) => a[1].brainvisa.order - b[1].brainvisa.order);
        for (const i in sortable) {
            const field_name = sortable[i][0];
            const field_type = sortable[i][1];
            const field_deletable = !this.is_read_only(id) && !field_type.brainvisa.class_field;
            if (value != undefined) {
                const elements = this.build_elements((id ? `${id}/${field_name}` : field_name), field_name, field_deletable, field_type, value[field_name]);
                for (const element of elements) {
                    if (label) {
                        fieldset.appendChild(element);
                    } else {
                        result.push(element);
                    }
                }
            }
        }
        if (deletable) {
            delete_button.addEventListener('click', async () => {
                const deleted = await this.backend_call('remove_item', id);
                if (deleted) {
                    for (const element of result) {
                        element.remove();
                    }
                }
            });
        }
        return result;
    }


    build_elements_string(id, label, deletable, type, value) {
        if (type.brainvisa) {
            const builder = this[`build_elements_${type.brainvisa.path_type}`];
            if (builder) {
                return builder.bind(this)(id, label, deletable, type, value);
            }
        }
        if (type.enum && !this.is_read_only(id)) {
            return this.build_elements_enum(id, label, deletable, type, value);
        }
        const input = document.createElement('input');
        input.id = id;
        input.type = "text";
        input.setAttribute("controller_type", type.type);
        if (this.is_read_only(id)) {
            input.setAttribute('readonly', "");
        }
        input.addEventListener('change', async event =>
            await this.update_controller_then_update_dom(event.target, event.target.value));
        if (value !== undefined && value != null) {
            input.value = value.toString();
        }
        if (label) {
            const l = document.createElement('label');
            l.setAttribute('for', id);
            l.textContent = label;
            if (deletable) {
                const delete_button = this.constructor.create_delete_button(l, id);
                delete_button.addEventListener('click', async () => {
                    const deleted = await this.backend_call('remove_item', id);
                    if (deleted) {
                        l.remove();
                        input.remove();
                    }
                });
            }
            return [l, input];
        } else {
            return [input];
        }
    }

    build_elements_integer(id, label, deletable, type, value) {
        return this.build_elements_string(id, label, deletable, type, value);
    }


    build_elements_number(id, label, deletable, type, value) {
        return this.build_elements_string(id, label, deletable, type, value);
    }

    build_elements_boolean(id, label, deletable, type, value) {
        const checkbox = document.createElement('input');
        checkbox.id = id;
        checkbox.type = "checkbox";
        checkbox.setAttribute("controller_type", type.type);
        if (this.is_read_only(id)) {
            checkbox.onclick = () => false;
        }
        checkbox.addEventListener('change', async event =>
            await this.update_controller_then_update_dom(event.target, !!event.target.checked));
        if (value) {
            checkbox.checked = true;
        }
        if (label) {
            const l = document.createElement('label');
            l.setAttribute('for', id);
            l.textContent = label;
            if (deletable) {
                const delete_button = this.constructor.create_delete_button(l, id);
                delete_button.addEventListener('click', async () => {
                    const deleted = await this.backend_call('remove_item', id);
                    if (deleted) {
                        l.remove();
                        checkbox.remove();
                    }
                });
            }
            return [l, checkbox];
        } else {
            return [checkbox];
        }
    }

    build_elements_enum(id, label, deletable, type, value) {
        const select = document.createElement('select');
        select.id = id;
        select.setAttribute("controller_type", "enum");
        select.addEventListener('change', async event =>
            await this.update_controller_then_update_dom(event.target, event.target.value));
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
            if (deletable) {
                const delete_button = this.constructor.create_delete_button(l, id);
                delete_button.addEventListener('click', async () => {
                    const deleted = await this.backend_call('remove_item', id);
                    if (deleted) {
                        l.remove();
                        select.remove();
                    }
                });
            }
            return [l, select];
        } else {
            return [select];
        }
    }

    build_elements_file(id, label, deletable, type, value) {
        let div;
        if (! this.is_read_only(id) && QtWebEngine) {
            div = document.createElement('div');
            div.classList.add("button_and_element");
            const button = document.createElement('button');
            button.setAttribute('for', id);
            button.type = 'button';
            button.textContent = '📁';
            button.addEventListener('click', async (event) => {
                const path = await (web_backend.call(`${type.brainvisa.path_type}_selector`));
                const input = document.getElementById(event.target.getAttribute('for'));
                await this.update_controller_then_update_dom(input, path);
                const check = await this.backend_call('get_value', input.id)
                input.value = path;
            });
            div.appendChild(button);
        }

        const input = document.createElement('input');
        input.id = id;
        input.type = "text";
        input.setAttribute("controller_type", type.brainvisa.path_type);
        if (this.is_read_only(id)) {
            input.setAttribute('readonly', "");
        }
        input.addEventListener('change', async event =>
            await this.update_controller_then_update_dom(event.target, event.target.value));
        if (value !== undefined) {
            input.value = value;
        }
        if (div) div.appendChild(input);

        if (label) {
            const l = document.createElement('label');
            l.setAttribute('for', id);
            l.textContent = label;
            if (deletable) {
                const delete_button = this.constructor.create_delete_button(l, id);
                delete_button.addEventListener('click', async () => {
                    const deleted = await this.backend_call('remove_item', id);
                    if (deleted) {
                        l.remove();
                        if (div) {
                            div.remove();
                        } else {
                            input.remove();
                        }
                    }
                });
            }
            return [l, (div ? div : input)];
        } else {
            return [input];
        }
    }

    build_elements_directory(id, label, deletable, type, value) {
        return this.build_elements_file(id, label, deletable, type, value);
    }


    build_elements_array(id, label, deletable, type, value) {
        if (type.items != undefined) {
            const builder = this[`build_elements_array_${type.items.type}`];
            if (builder) {
                const result = builder.bind(this)(id, label, deletable, type, value);
                if (result !== undefined) {
                    return result;
                }
            }
        }
        const fieldset = document.createElement('fieldset');
        fieldset.id = id;
        fieldset.setAttribute("controller_type", "array");
        fieldset.classList.add('controller');
        if ((id.match(/\//g) || []).length > 2) {
            fieldset.classList.add('collapsed');
        }
        if (label) {
            const legend = document.createElement('legend');
            const l = document.createElement('label');
            l.setAttribute('for', id);
            l.addEventListener('click', async event => {
                const fieldset = event.target.parentElement.parentElement;
                fieldset.classList.toggle('collapsed');
                await this.backend_call('set_status', `${id}/_collapsed`, fieldset.classList.contains('collapsed'));
            });
            l.textContent = label;
            legend.appendChild(l);
            if (!this.is_read_only(id)) {
                const new_item = document.createElement('button');
                new_item.type = 'button';
                new_item.addEventListener('click', async (event) => {
                    const index = await this.backend_call('new_list_item', event.target.parentElement.parentElement.id);
                    if (index !== undefined) {
                        const new_id = `${id}/${index}`;
                        const new_value = await this.backend_call('get_value', new_id);
                        const deletable = ! this.is_read_only(id);
                        for (const element of this.build_elements(new_id, `[${index}]`, deletable, type.items, new_value)) {
                            fieldset.appendChild(element);
                        }
                    }
                });
                new_item.innerText = '+';
                legend.appendChild(new_item);
            }
            if (deletable) {
                const delete_button = this.constructor.create_delete_button(legend, id);
                delete_button.addEventListener('click', async () => {
                    const deleted = await this.backend_call('remove_item', id);
                    if (deleted) {
                        fieldset.remove();
                    }
                });
            }
            fieldset.appendChild(legend);
        }
        for (const index in value) {
            const deletable = ! this.is_read_only(id);
            for (const element of this.build_elements(`${id}/${index}`, `[${index}]`, deletable, type.items, value[index])) {
                fieldset.appendChild(element);
            }
        }
        return [fieldset];
    }


    build_elements_array_string(id, label, deletable, type, value) {
        if (type.items.enum ||
            (QtWebEngine && type.brainvisa.path_type)) {
            return undefined;
        }
        const textarea = document.createElement('textarea');
        textarea.id = id;
        textarea.setAttribute("controller_type", `array_${type.type}`);
        if (this.is_read_only(id)) {
            textarea.setAttribute('readonly', "");
        }
        textarea.addEventListener('change', async event =>
            await this.update_controller_then_update_dom(
                event.target,
                event.target.value.trim().split(/\r?\n|\r|\n/g)));
        var vl = 0;
        if (value != null && value != undefined)
            vl = value.length;
        const rows = Math.min(20, Math.max(5, vl));
        textarea.setAttribute('rows', rows);
        if (value !== undefined && value != null) {
            textarea.textContent = value.join('\n');
        }
        if (label) {
            const l = document.createElement('label');
            l.setAttribute('for', id);
            l.textContent = label;
            if (deletable) {
                const delete_button = this.constructor.create_delete_button(l, id);
                delete_button.addEventListener('click', async () => {
                    const deleted = await this.backend_call('remove_item', id);
                    if (deleted) {
                        l.remove();
                        textarea.remove();
                    }
                });
            }
            return [l, textarea];
        } else {
            return [textarea];
        }
    }


    build_elements_array_integer(id, label, deletable, type, value) {
        const textarea = document.createElement('textarea');
        textarea.id = id;
        textarea.setAttribute("controller_type", `array_${type.type}`);
        if (this.is_read_only(id)) {
            textarea.setAttribute('readonly', "");
        }
        textarea.addEventListener('change', async event =>
            await this.update_controller_then_update_dom(
                event.target,
                event.target.value.trim().split(/\s+/)));
        if (value !== undefined) {
            textarea.textContent = value.join(' ');
        }
        if (label) {
            const l = document.createElement('label');
            l.setAttribute('for', id);
            l.textContent = label;
            if (deletable) {
                const delete_button = this.constructor.create_delete_button(l, id);
                delete_button.addEventListener('click', async () => {
                    const deleted = await this.backend_call('remove_item', id);
                    if (deleted) {
                        l.remove();
                        textarea.remove();
                    }
                });
            }
            return [l, textarea];
        } else {
            return [textarea];
        }
    }

    build_elements_array_number(id, label, deletable, type, value) {
        return this.build_elements_array_integer(id, label, deletable, type, value);
    }

    async update_controller_then_update_dom(element, value) {
        try {
            await this.backend_call('set_value', element.id, value);
            element.classList.remove("has_error");
        }
        catch ( error ) {
            element.classList.add("has_error");
            throw( error );
        }
    }
}
