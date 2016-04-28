# sublime_ansible_vault
Ansible vault manipulation in Sublime Text

## Pre-requisites
- [ansible](http://docs.ansible.com/ansible/)

## Installation

### With Package Control:

1. Run the `Package Control: Install Package` command, find and install the Ansible Vault plugin.
1. Restart Sublime Text (if required)

### Manually:

1. Clone or download the git repo into your packages folder (in Sublime Text, find Browse Packages… menu item to open this folder)
1. Restart Sublime Text editor (if required)

## Usage

To peek into an encrypted vault, you can either, open your command
pallette and search for `Ansible Vault: View` or, you can use the menu:
`Tools` > `Ansible Vault` > `View`

Viewing will open a new, read only tab. But this will not modify the
original vault. If you want to modify a vault, you should `decrypt`
instead.

## Configuration
The following options are available:

| Option          | Description |
|-----------------|-------------|
| `password`      | Plain text ansible vault password. |
| `password_file` | Absolute path to your ansible vault [password file](http://docs.ansible.com/ansible/playbooks_vault.html#running-a-playbook-with-vault) |

If none of the password options are used, then you will be prompted for your password on each vault action.
