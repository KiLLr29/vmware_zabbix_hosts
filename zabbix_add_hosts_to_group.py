import logging
import json
import re
from pyzabbix import ZabbixAPI

# Импортируем настройки из файла config.py
from config import ZABBIX_URL, ZABBIX_USER, ZABBIX_PASSWORD

# Настройка логирования
log_file = "/var/log/zabbix/zabbix_scripts_add_hosts_to_group.log"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler(log_file), logging.StreamHandler()]
)

def load_hosts_from_file(filename):
    """
    Загружает список хостов из JSON-файла.
    """
    try:
        with open(filename, "r") as f:
            return json.load(f)
    except Exception as e:
        logging.error(f"Ошибка при чтении файла {filename}: {e}")
        raise


def normalize_hostname(vcenter_name):
    """
    Нормализует имя хоста из VCenter для сравнения с именами в Zabbix.
    Например, преобразует 'VW-SWX002-a.miller' в 'SWX002'.
    """
    match = re.search(r"VW-(\w+)-", vcenter_name)
    if match:
        return match.group(1)  # Возвращаем часть, соответствующую шаблону
    return vcenter_name  # Если шаблон не найден, возвращаем исходное имя


def connect_to_zabbix():
    """
    Подключается к Zabbix API и возвращает объект API.
    """
    try:
        zapi = ZabbixAPI(ZABBIX_URL)
        zapi.login(ZABBIX_USER, ZABBIX_PASSWORD)
        logging.info("Успешно подключено к Zabbix API")
        return zapi
    except Exception as e:
        logging.error(f"Ошибка при подключении к Zabbix API: {e}")
        raise


def get_hostgroup_id(zapi, group_name):
    """
    Получает ID группы хостов по её имени.
    Если группа не существует, возвращает None.
    """
    groups = zapi.hostgroup.get(filter={"name": group_name}, output=["groupid"])
    if groups:
        return groups[0]["groupid"]
    return None


def add_hosts_to_group(zapi, hosts, group_id):
    """
    Добавляет хосты в указанную группу, сохраняя их текущие группы.
    Пропускает хосты со статусом poweredOff.
    :param zapi: Объект Zabbix API.
    :param hosts: Список хостов (имена и статусы).
    :param group_id: ID группы хостов.
    """
    for host in hosts:
        host_name = host["host"]
        vm_status = host["status"]

        # Пропускаем хосты со статусом poweredOff
        if vm_status == "poweredOff":
            logging.info(f"Хост '{host_name}' выключен в VCenter. Пропускаем.")
            continue

        # Нормализуем имя хоста
        normalized_name = normalize_hostname(host_name)

        # Проверяем, существует ли хост в Zabbix
        zabbix_hosts = zapi.host.get(filter={"host": normalized_name}, selectGroups=["groupid"], output=["hostid"])
        if not zabbix_hosts:
            logging.warning(f"Хост '{normalized_name}' не найден в Zabbix. Пропускаем.")
            continue

        host_id = zabbix_hosts[0]["hostid"]
        current_groups = [group["groupid"] for group in zabbix_hosts[0]["groups"]]

        # Проверяем, состоит ли хост уже в группе 'vcenter_hosts'
        if group_id in current_groups:
            logging.info(f"Хост '{normalized_name}' уже состоит в группе 'vcenter_hosts'. Пропускаем.")
            continue

        # Добавляем группу 'vcenter_hosts' к текущим группам
        updated_groups = list(set(current_groups + [group_id]))

        # Обновляем группы хоста
        zapi.host.update(hostid=host_id, groups=[{"groupid": gid} for gid in updated_groups])
        logging.info(f"Группа 'vcenter_hosts' добавлена к хосту '{normalized_name}'")


if __name__ == "__main__":
    try:
        # Подключаемся к Zabbix
        zapi = connect_to_zabbix()

        # Получаем ID группы 'vcenter_hosts'
        group_name = "vcenter_hosts"
        group_id = get_hostgroup_id(zapi, group_name)
        if not group_id:
            logging.error(f"Группа '{group_name}' не найдена в Zabbix. Создайте её вручную.")
            raise ValueError(f"Группа '{group_name}' не существует.")

        # Загружаем список хостов из JSON-файла
        vcenter_vms = load_hosts_from_file("vcenter_vms.json")

        # Добавляем хосты в группу
        add_hosts_to_group(zapi, vcenter_vms, group_id)

    except Exception as e:
        logging.error(f"Произошла ошибка: {e}")