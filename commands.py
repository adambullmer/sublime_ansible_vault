from functools import partial
import logging
import subprocess

import sublime
import sublime_plugin


log = logging.getLogger(__name__)

ANSIBLE_COMMAND_TEMPLATE = 'ansible-vault {vault_password} {command} "{vault_file}"'


def get_setting(key, default=None):
    settings = sublime.load_settings('AnsibleVault.sublime-settings')
    os_specific_settings = {}

    os_name = sublime.platform()
    if os_name == 'osx':
        os_specific_settings = sublime.load_settings('AnsibleVault (OSX).sublime-settings')
    elif os_name == 'windows':
        os_specific_settings = sublime.load_settings('AnsibleVault (Windows).sublime-settings')
    else:
        os_specific_settings = sublime.load_settings('AnsibleVault (Linux).sublime-settings')

    return os_specific_settings.get(key, settings.get(key, default))


class AnsibleVaultBase:
    open_new_tab = False
    command = None
    project_settings = None
    password = None
    vault_file_path = None

    def prompt_vault_password(self, vault_file_path):
        bound_vault_command = partial(self.run_vault_command, vault_file_path)
        self.view.window().show_input_panel('Vault Password', '', bound_vault_command, self.on_change, self.on_cancel)

    def on_change(self, password):
        pass

    def on_cancel(self):
        pass

    def ansible_vault(self, vault_file_path):
        # Use a password if one is present
        password = get_setting('password')
        if password != '':
            self.run_vault_command(vault_file_path, password)
            return

        # Use a password file is one is present
        password_file = get_setting('password_file')
        if password_file != '':
            self.run_vault_command(vault_file_path, password_file, password_from_file=True)
            return

        # No configured password, fallback to a prompt
        self.prompt_vault_password(vault_file_path)

    def run_vault_command(self, vault_file_path, password, password_from_file=False):
        vault_password_flag = '--ask-vault-pass'
        password_input = password

        if password_from_file is True:
            vault_password_flag = '--vault-password-file "{}"'.format(password)
            password_input = ''

        proc = subprocess.Popen([
            ANSIBLE_COMMAND_TEMPLATE.format(
                vault_password=vault_password_flag,
                command=self.command,
                vault_file=vault_file_path,
            )],
            stdout=subprocess.PIPE,
            stdin=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=True
        )

        output, error = proc.communicate(input=bytearray(password_input, 'utf-8'))
        output = output.decode('utf-8')

        if self.open_new_tab is True:
            self.view.run_command('ansible_vault_output', {'output': output, 'title': vault_file_path})


class AnsibleVaultOutputCommand(sublime_plugin.TextCommand):
    def run(self, edit, output=None, title=None):
        output_view = self.view.window().new_file()
        output_view.set_name(title)
        output_view.insert(edit, 0, output)
        output_view.set_read_only(True)


class AnsibleVaultViewCommand(AnsibleVaultBase, sublime_plugin.TextCommand):
    command = 'view'
    open_new_tab = True

    def run(self, edit):
        vault_file = self.view.file_name()
        self.ansible_vault(vault_file)


class AnsibleVaultDecryptCommand(AnsibleVaultBase, sublime_plugin.TextCommand):
    command = 'decrypt'

    def run(self, edit):
        vault_file = self.view.file_name()
        self.ansible_vault(vault_file)


class AnsibleVaultEncryptCommand(AnsibleVaultBase, sublime_plugin.TextCommand):
    command = 'encrypt'

    def run(self, edit):
        vault_file = self.view.file_name()
        self.ansible_vault(vault_file)
