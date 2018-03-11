from functools import partial
import logging
from subprocess import Popen, PIPE

import sublime
import sublime_plugin


log = logging.getLogger(__name__)

ANSIBLE_COMMAND_TEMPLATE = 'ansible-vault {command} {extra_flags} {vault_password} {vault_file}'
GETPASS_WARNING = "Warning: Password input may be echoed.\nVault password: "


class AnsibleVaultBase:
    open_new_tab = False
    command = None
    password = None
    vault_data = None
    extra_flags = ''

    @property
    def debug(self):
        return self.get_setting('debug', False)

    @property
    def password(self):
        return self.get_setting('password')

    @property
    def password_file(self):
        return self.get_setting('password_file')

    def debug_log(self, message):
        if self.debug:
            print('ANSIBLE VAULT: "%s"' % message)

    def get_setting(self, key, default=None):
        settings = sublime.load_settings('AnsibleVault.sublime-settings')
        os_specific_settings = {}

        os_name = sublime.platform()
        if os_name == 'osx':
            os_specific_settings = sublime.load_settings('AnsibleVault (OSX).sublime-settings')
        elif os_name == 'windows':
            os_specific_settings = sublime.load_settings('AnsibleVault (Windows).sublime-settings')
        else:
            os_specific_settings = sublime.load_settings('AnsibleVault (Linux).sublime-settings')

        project_settings = self.view.window().project_data() or {}
        project_settings = project_settings.get('AnsibleVault', {})

        if project_settings.get(key) is not None:
            return project_settings.get(key)
        elif os_specific_settings.get(key) is not None:
            return project_settings.get(key)

        return settings.get(key, default)

    def prompt_vault_password(self, edit, vault_data, region):
        bound_vault_command = partial(self.run_vault_command, edit, vault_data, region)
        self.view.window().show_input_panel('Vault Password', '', bound_vault_command, self.on_change, self.on_cancel)

    def on_change(self, password):
        pass

    def on_cancel(self):
        pass

    def ansible_vault(self, edit, vault_data, region, data_text=False):
        # Use a password file is one is present
        if self.password_file != '':
            return self.run_vault_command(edit, vault_data, region, self.password_file, data_text, password_from_file=True)

        # Back out if we're doing area selection as password file is the only one that works
        if data_text is True:
            sublime.error_message("Text selection is only supported with a vault pass file")
            return

        # Use a password if one is present
        if self.password != '':
            return self.run_vault_command(edit, vault_data, region, self.password, data_text)

        # No configured password, fallback to a prompt
        self.prompt_vault_password(edit, vault_data, region)

    def get_selection(self, edit, decrpyt = False):
        selections = self.view.sel()
        if len(selections[0]) < 1:
            region = sublime.Region(0, self.view.size())
            vault_file = '"{}"'.format(self.view.file_name())
            self.ansible_vault(edit, vault_file, region)
            return

        for region in selections:
            text = self.view.substr(region)
            if decrpyt:
                text = text.replace(" ", "")
                text = text.replace("   ", "")
            self.ansible_vault(edit, text, region, True)

    def run_vault_command(self, edit, vault_data, region, password, data_text=False, password_from_file=False):
        vault_password_flag = '--vault-password-file "%s"' % password
        vault_input = ''

        if password_from_file is False:
            vault_password_flag = '--ask-vault-pass'
            vault_input = password

        if data_text is True:
            vault_input = vault_data
            vault_data = ''

        command = ANSIBLE_COMMAND_TEMPLATE.format(
            vault_password=vault_password_flag,
            command=self.command,
            vault_file=vault_data,
            extra_flags=self.extra_flags,
        )
        with Popen([command], stdin=PIPE, stdout=PIPE, stderr=PIPE, shell=True, universal_newlines=True) as proc:
            output, error = proc.communicate(input=vault_input)

        if self.error_handler(error) is True:
            return

        if self.open_new_tab is True:
            self.view.run_command('ansible_vault_output', {'output': output, 'title': vault_data})
        else:
            self.view.replace(edit, region, output)

    def error_handler(self, error):
        error = error.strip()
        if not error:
            return False

        self.debug_log(error)

        # Trimming getpass() warning
        getpass_position = error.find(GETPASS_WARNING)
        if getpass_position > -1:
            getpass_position += len(GETPASS_WARNING)

        if not error[getpass_position:].strip():
            return False

        sublime.error_message(error[getpass_position:])
        return True


class AnsibleVaultOutputCommand(sublime_plugin.TextCommand):
    def run(self, edit, output=None, title=None):
        output_view = self.view.window().new_file()
        output_view.set_name(title)
        output_view.insert(edit, 0, output)
        output_view.set_syntax_file('Packages/YAML/YAML.sublime-syntax')
        output_view.set_read_only(True)


class AnsibleVaultViewCommand(AnsibleVaultBase, sublime_plugin.TextCommand):
    command = 'view'
    open_new_tab = True

    def run(self, edit):
        vault_file = self.view.file_name()
        self.ansible_vault(edit, vault_file)


class AnsibleVaultDecryptCommand(AnsibleVaultBase, sublime_plugin.TextCommand):
    command = 'decrypt'
    extra_flags = '--output=-'

    def run(self, edit):
        self.get_selection(edit, True)

class AnsibleVaultEncryptCommand(AnsibleVaultBase, sublime_plugin.TextCommand):
    command = 'encrypt'
    extra_flags = '--output=-'

    def run(self, edit):
        self.get_selection(edit)
