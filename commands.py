from functools import partial
from subprocess import Popen, PIPE

import sublime
import sublime_plugin


ANSIBLE_COMMAND_TEMPLATE = '{ansible_path}ansible-vault {command} {extra_flags} {vault_password} "{vault_file}"'
GETPASS_WARNING = "Warning: Password input may be echoed.\nVault password:"


class AnsibleVaultBaseCommand(sublime_plugin.TextCommand):
    open_new_tab = False
    command = None
    password = None
    vault_file_path = None
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

    @property
    def ansible_path(self):
        return self.get_setting('ansible_path', '')

    def run(self, edit):
        self.vault_file_path = self.view.file_name()
        self.ansible_vault()

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

    def prompt_vault_password(self):
        bound_vault_command = partial(self.run_vault_command)
        self.view.window().show_input_panel('Vault Password', '', bound_vault_command, self.on_change, self.on_cancel)

    def on_change(self, password):
        pass

    def on_cancel(self):
        pass

    def ansible_vault(self):
        # Use a password file is one is present
        if self.password_file == '' and self.password == '':
            # No configured password, fallback to a prompt
            return self.prompt_vault_password()

        return self.run_vault_command()

    def run_vault_command(self, password=None):
        vault_password_flag = '--ask-vault-pass'
        password_input = None

        if self.password_file != '':
            vault_password_flag = '--vault-password-file "%s"' % self.password_file
        elif self.password != '':
            password_input = self.password
        else:
            password_input = password

        command = ANSIBLE_COMMAND_TEMPLATE.format(
            ansible_path=self.ansible_path,
            vault_password=vault_password_flag,
            command=self.command,
            vault_file=self.vault_file_path,
            extra_flags=self.extra_flags,
        )
        output = self.exec_command(command, password_input)
        if output is False:
            return

        self.view.run_command('ansible_vault_output', {
            'output': output,
            'title': self.vault_file_path,
            'new_file': self.open_new_tab,
        })

    def exec_command(self, command, input_=None):
        with Popen([command], stdin=PIPE, stdout=PIPE, stderr=PIPE, shell=True, universal_newlines=True) as proc:
            output, error = proc.communicate(input='%s\n' % input_)

        if self.error_handler(error) is True:
            return False

        return output

    def error_handler(self, error):
        error = error.strip()
        if not error:
            return False

        self.debug_log(error)

        # Trimming getpass() warning
        getpass_position = error.find(GETPASS_WARNING)
        if getpass_position > -1:
            getpass_position += len(GETPASS_WARNING)
            error = error[getpass_position:]

        if not error.strip():
            return False

        sublime.error_message(error)
        return True


class AnsibleVaultOutputCommand(sublime_plugin.TextCommand):
    """Command to output the result of the decryption."""

    def run(self, edit, output=None, title=None, new_file=False):
        if new_file is True:
            self.read_only_view(edit, output, title)
        else:
            self.same_view(edit, output)

    def same_view(self, edit, output):
        region = sublime.Region(0, self.view.size())
        self.view.replace(edit, region, output)

    def read_only_view(self, edit, output, title):
        output_view = self.view.window().new_file()
        output_view.set_name(title)
        output_view.insert(edit, 0, output)
        output_view.set_syntax_file('Packages/YAML/YAML.sublime-syntax')
        output_view.set_read_only(True)

    def error_handler(self):
        pass


class AnsibleVaultViewCommand(AnsibleVaultBaseCommand):
    command = 'view'
    open_new_tab = True


class AnsibleVaultDecryptCommand(AnsibleVaultBaseCommand):
    command = 'decrypt'
    extra_flags = '--output=-'


class AnsibleVaultEncryptCommand(AnsibleVaultBaseCommand):
    command = 'encrypt'
    extra_flags = '--output=-'
