class Backend {};
{%- for name, method in backend_methods.items() %}
Backend.prototype.{{name}} = async function ({% for p in method._params %}{{p}},{% endfor %}) {
    const data = await qt_backend.{{name}}({% for p in method._params %}{{p}}, {% endfor %});
    if (data['error_type']) {
        throw new Error(`${data['error_message']}`);
    }{% if method._return %} else {
        return data['result'];
    }{% endif %}
}
{%- endfor %}

var backend = null;
var qt_backend = null;
window.addEventListener("load", (event) => {
    new QWebChannel(qt.webChannelTransport, function(channel) {
        qt_backend = channel.objects.backend;
        backend = new Backend();
        window.dispatchEvent(backend_ready);
    });
});
