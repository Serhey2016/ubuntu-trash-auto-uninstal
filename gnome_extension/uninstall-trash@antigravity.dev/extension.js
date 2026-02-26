import GObject from 'gi://GObject';
import St from 'gi://St';
import GLib from 'gi://GLib';
import Gio from 'gi://Gio';
import Shell from 'gi://Shell';

import Clutter from 'gi://Clutter';

import * as Main from 'resource:///org/gnome/shell/ui/main.js';
import * as PanelMenu from 'resource:///org/gnome/shell/ui/panelMenu.js';
import * as DND from 'resource:///org/gnome/shell/ui/dnd.js';

import { Extension } from 'resource:///org/gnome/shell/extensions/extension.js';

const UninstallDropTarget = GObject.registerClass(
    class UninstallDropTarget extends PanelMenu.Button {
        _init(extensionPath) {
            super._init(0.0, "Uninstall Trash");
            this._scriptPath = GLib.build_filenamev([extensionPath, 'uninstall_trash.py']);

            this._icon = new St.Icon({
                icon_name: 'user-trash-symbolic',
                style_class: 'system-status-icon',
            });
            this.add_child(this._icon);
            this._delegate = this; // Needed for DND

            // Open Trash on Click
            this.connect('button-press-event', (actor, event) => {
                if (event.get_button() === 1) { // Left click
                    try {
                        Gio.AppInfo.launch_default_for_uri("trash:///", null);
                    } catch (e) {
                        console.error(e);
                    }
                    return Clutter.EVENT_STOP;
                }
                return Clutter.EVENT_PROPAGATE;
            });
        }

        handleDragOver(source, _actor, _x, _y, _time) {
            this._icon.icon_name = 'user-trash-full-symbolic';
            return DND.DragMotionResult.COPY_DROP;
        }

        handleDragOut() {
            this._icon.icon_name = 'user-trash-symbolic';
        }

        acceptDrop(source, _actor, _x, _y, _time) {
            this._icon.icon_name = 'user-trash-symbolic';

            console.warn(`acceptDrop called with source: ${source}`);
            if (source) {
                let keys = [];
                for (let k in source) { keys.push(k); }
                console.warn(`source keys: ${keys.join(', ')}`);

                if (source.app) {
                    let id = source.app.get_id();
                    try {
                        Gio.Subprocess.new(
                            ['/usr/bin/python3', this._scriptPath, id],
                            Gio.SubprocessFlags.NONE
                        );
                    } catch (e) {
                        console.error(`Uninstall Trash Error: ${e}`);
                    }
                    return false;
                } else {
                    // It's a file or something else
                    console.warn(`Nautilus or external drop detected. URIs:`);
                    if (source.get_uris) console.warn(source.get_uris().join(', '));
                    if (source.uris) console.warn(source.uris.join(', '));

                    // Actually delete the file using Gio
                    // We will implement actual deletion once we know the format
                }
            }
            return false; // Return false to bypass problematic GNOME Shell drop animation
        }
    });

export default class UninstallTrashExtension extends Extension {
    enable() {
        this._indicator = new UninstallDropTarget(this.path);
        // this.uuid is automatically populated by the Extension base class
        Main.panel.addToStatusArea(this.uuid, this._indicator);
    }

    disable() {
        if (this._indicator) {
            this._indicator.destroy();
            this._indicator = null;
        }
    }
}
