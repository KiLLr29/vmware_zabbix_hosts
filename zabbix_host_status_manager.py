import logging
import json
from pyzabbix import ZabbixAPI

# Импортируем настройки из файла config.py
from config import ZABBIX_URL, ZABBIX_USER, ZABBIX_PASSWORD

# Настройка логирования
log_file = "/var/log/zabbix/zabbix_script_status_manager.log"
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


def connect_to_zabbix():
    """
    Подключается к Zabbix API и возвращает объект API.
    """
    try:
        zapi = ZabbixAPI(ZABBIX_URL)
        zapi.login(ZABBIX_USER, ZABBIX_PASSWORD)
        return zapi
    except Exception as e:
        logging.error(f"Ошибка при подключении к Zabbix API: {e}")
        raise


def determine_status(vmware_status):
    """
    Определяет статус Zabbix в зависимости от статуса VMware.
    """
    if vmware_status == "poweredOff":
        return 1
    elif vmware_status == "poweredOn":
        return 0
    else:
        logging.warning(f"Неизвестный статус VMware: {vmware_status}")
        return None


def change_host_status(zapi, host_name, status):
    """
    Меняет статус хоста в Zabbix.
    :param zapi: Объект Zabbix API.
    :param host_name: Имя хоста в Zabbix.
    :param status: Новый статус (0 - enabled, 1 - disabled).
    """
    try:
        # Получаем ID хоста по имени
        hosts = zapi.host.get(filter={"host": host_name}, output=["hostid", "status"])
        if not hosts:
            logging.error(f"Хост '{host_name}' не найден в Zabbix.")
            return

        host_info = hosts[0]
        host_id = host_info["hostid"]

        # Проверка — если статус не меняется, пропускаем
        if int(host_info["status"]) == status:
            logging.info(f"Хост '{host_name}' уже имеет статус {'enabled' if status == 0 else 'disabled'} — пропуск.")
            return

        # Меняем статус хоста
        zapi.host.update(hostid=host_id, status=status)
        new_status = "enabled" if status == 0 else "disabled"
        logging.info(f"Статус хоста '{host_name}' изменен на {new_status}")
    except Exception as e:
        logging.error(f"Ошибка при изменении статуса хоста '{host_name}': {e}")


if __name__ == "__main__":
    try:
        zapi = connect_to_zabbix()
        mismatched_hosts = load_hosts_from_file("mismatched_hosts.json")

        for host in mismatched_hosts:
            if "host" not in host or "vmware_status" not in host:
                logging.warning(f"Пропущен объект с неверной структурой: {host}")
                continue

            host_name = host["host"]
            vmware_status = host["vmware_status"]
            new_status = determine_status(vmware_status)

            if new_status is None:
                continue

            change_host_status(zapi, host_name, new_status)

    except Exception as e:
        logging.error(f"Произошла ошибка: {e}")
