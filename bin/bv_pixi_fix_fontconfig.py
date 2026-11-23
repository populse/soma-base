#!/usr/bin/env python

import os
import os.path as osp
import sys

pixi_root = os.environ.get('PIXI_PROJECT_ROOT')
if not pixi_root:
    print('no PIXI_PROJECT_ROOT')
    sys.exit(0)

pixi_toml = osp.join(pixi_root, 'pixi.toml')
activate = osp.join(pixi_root, 'activate.sh')
activ_contents = []
pixitoml_contents = []

if osp.exists(activate):
    with open(activate) as f:
        for line in f.readlines():
            if 'fix fontconfig cache issue' in line.lower():
                print('already done.')
                # sys.exit(0)
            activ_contents.append(line)

if activ_contents:
    activ_contents.append('\n')

activ_contents.append(
'''# Fix fontconfig cache issue by disabling it

if [ -d "$SOMA_ROOT/fontconfig_local" -a -w "$SOMA_ROOT/fontconfig_local" ]; then
    FONTCONFIG_LOCAL="$SOMA_ROOT/fontconfig_local"
else
    if [ ! -d "$SOMA_ROOT/fontconfig_local" -a -w "$SOMA_ROOT" ];
 then
        mkdir "$SOMA_ROOT/fontconfig_local"
        FONTCONFIG_LOCAL="$SOMA_ROOT/fontconfig_local"
    fi
fi
if [ -z "$FONTCONFIG_LOCAL" ]; then
    CLEAN_FONTCONFIG_CACHE=1
    if [ -z "$TMPDIR" ]; then
        TMPDIR=/tmp
    fi
    mkdir -p "$TMPDIR/soma_pixi"
    FONTCONFIG_LOCAL=$(mktemp -d -p "" soma_pixi/fontconfig_XXXXXXX)
    chmod a+rwx "$FONTCONFIG_LOCAL"
fi

if [ ! -e "$FONTCONFIG_LOCAL/conf/fontconfig" ]; then
    mkdir -p "$FONTCONFIG_LOCAL/conf/fontconfig"
    mkdir -p "$FONTCONFIG_LOCAL/fontconfig_cache"
    if [ -f /etc/fonts/fonts.conf ]; then
        sed "s/^.*<cachedir.*$//" /etc/fonts/fonts.conf > "$FONTCONFIG_LOCAL/conf/fontconfig/fonts.conf"
        sed -i "/^.*<\\!-- Font cache directory list.*$/a\\\t<cachedir>$FONTCONFIG_LOCAL\\/fontconfig_cache<\\/cachedir>" "$FONTCONFIG_LOCAL/conf/fontconfig/fonts.conf"
    else
        # this does not work actually if /etc/fonts/fonts.conf exists
        cat << EOF > "$FONTCONFIG_LOCAL/conf/fontconfig/fonts.conf"
<?xml version="1.0"?>
<!DOCTYPE fontconfig SYSTEM "urn:fontconfig:fonts.dtd">
<fontconfig>
    <cachedir>$FONTCONFIG_LOCAL/fontconfig_cache</cachedir>
    <include ignore_missing="yes">/etc/fonts/fonts.conf</include>
</fontconfig>
EOF
    fi
fi
export FONTCONFIG_FILE="$FONTCONFIG_LOCAL/conf/fontconfig/fonts.conf"

# unfortunately we cannot clean $FONTCONFIG_LOCAL at pixi exit.
'''
)

# print('activate.sh:')
# print(''.join(activ_contents))
# print('\n\n----\n\n')

with open(activate, 'w') as f:
    print(''.join(activ_contents), file=f)

with open(pixi_toml) as f:
    activ = None
    scripts = None
    scripts_content = []
    for line in f.readlines():
        pixitoml_contents.append(line)
        if line.strip() == '[activation]':
            activ = len(pixitoml_contents) - 1
            print('activ')
        elif activ is not None:
            if scripts is None and line.strip().startswith('scripts ='):
                scripts = len(pixitoml_contents) - 1
                print('scripts:', scripts)
            if scripts:
                scripts_content.append(line)
            if scripts and ']' in line:
                print('end scripts')
                endscripts = len(pixitoml_contents) - 1
                scripts_content[0] = scripts_content[0].split('=', 1)[1]
                scripts_l = ''.join(line.strip() for line in scripts_content)
                scripts_content = eval(scripts_l)
                print('scripts:', repr(scripts_content))
                if 'activate.sh' in scripts_content:
                    print('already done')
                    # sys.exit(0)
                else:
                    scripts_content.append('activate.sh')
                print('scripts:', scripts_content)
                pixitoml_contents = pixitoml_contents[:scripts]
                scripts = 'scripts = '
                if len(scripts_content) == 1:
                    scripts += f'["{scripts_content[0]}"]\n'
                    pixitoml_contents.append(scripts)
                else:
                    pixitoml_contents.append('scripts = [\n')
                    for s in scripts_content:
                        pixitoml_contents.append(f'    "{s}"\n')
                    pixitoml_contents.append(']')

# print('pixi.toml:')
# print(''.join(pixitoml_contents))

with open(pixi_toml, 'w') as f:
    print(''.join(pixitoml_contents), file=f)
