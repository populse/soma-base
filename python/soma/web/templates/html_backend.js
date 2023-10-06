class Backend {};
{%- for name, method in backend_methods.items() %}
Backend.prototype.{{name}} = async function ({% for p in method._params %}{{p}}, {% endfor %}) {
  const args = Object.values(arguments);
  const response = await fetch("{{base_url}}/backend/{{name}}", {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(args)
  });
  if (! response.ok) {
    throw new Error(`HTTP error: ${response.status}`);
  }

  const data = await response.json();
  if (data['error_type']) {
    throw new Error(`${data['error_message']}`);
  }{% if method._return %} else {
    return data['result'];
  }{% endif %}
}
{%- endfor %}

var backend = null;
window.addEventListener("load", (event) => {
  backend = new Backend();
  event.currentTarget.dispatchEvent(backend_ready);
});
