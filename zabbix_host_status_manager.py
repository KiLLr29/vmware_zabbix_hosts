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


def change_host_status(zapi, host_name, status):
    """
    Меняет статус хоста в Zabbix.
    :param zapi: Объект Zabbix API.
    :param host_name: Имя хоста в Zabbix.
    :param status: Новый статус (0 - enabled, 1 - disabled).
    """
    try:
        # Получаем ID хоста по имени
        hosts = zapi.host.get(filter={"host": host_name}, output=["hostid"])
        if not hosts:
            logging.error(f"Хост '{host_name}' не найден в Zabbix.")
            return

        host_id = hosts[0]["hostid"]

        # Меняем статус хоста
        zapi.host.update(hostid=host_id, status=status)
        new_status = "enabled" if status == "0" else "disabled"
        logging.info(f"Статус хоста '{host_name}' изменен на {new_status}")
    except Exception as e:
        logging.error(f"Ошибка при изменении статуса хоста '{host_name}': {e}")


if __name__ == "__main__":
    # Пример использования
    try:
        # Подключаемся к Zabbix
        zapi = connect_to_zabbix()

        # Загружаем список хостов из JSON-файла
        mismatched_hosts = load_hosts_from_file("mismatched_hosts.json")

        for host in mismatched_hosts:
            host_name = host["host"]
            vmware_status = host["vmware_status"]

            # Определяем новый статус для Zabbix
            if vmware_status == "poweredOff":
                new_status = "1"  # Выключить хост в Zabbix
            elif vmware_status == "poweredOn":
                new_status = "0"  # Включить хост в Zabbix

            # Меняем статус хоста
            change_host_status(zapi, host_name, new_status)

    except Exception as e:
        logging.error(f"Произошла ошибка: {e}")