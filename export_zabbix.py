import json
import logging
import os
from pyzabbix import ZabbixAPI
from config import ZABBIX_URL, ZABBIX_USER, ZABBIX_PASSWORD

# Настройка логирования
log_dir = "/var/log/zabbix"
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, "zabbix_scripts_zabbix_export_hosts.log")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)


def get_hosts_from_zabbix():
    """
    Получает список хостов из Zabbix.
    Экспортирует данные в формате: hostname, status (enabled/disabled), ip.
    """
    try:
        zapi = ZabbixAPI(ZABBIX_URL)
        zapi.login(ZABBIX_USER, ZABBIX_PASSWORD)
        logging.info("Успешное подключение к Zabbix API.")

        hosts = zapi.host.get(output=["name", "status"], selectInterfaces=["ip"])
        zabbix_hosts = []

        for host in hosts:
            hostname = host["name"]
            host_status = "enabled" if host["status"] == "0" else "disabled"
            interfaces = host.get("interfaces", [])
            ip_addresses = [interface["ip"] for interface in interfaces if "ip" in interface]

            zabbix_hosts.append({
                "host": hostname,
                "status": host_status,
                "ip": ip_addresses[0] if ip_addresses else None
            })

        logging.info(f"Получено {len(zabbix_hosts)} хостов из Zabbix.")
        return zabbix_hosts

    except Exception as e:
        logging.error(f"Ошибка при получении хостов из Zabbix: {e}")
        raise


def save_to_file(data, filename):
    """
    Сохраняет данные в файл в формате JSON.
    """
    try:
        with open(filename, "w") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        logging.info(f"Данные успешно сохранены в файл: {filename}")
    except Exception as e:
        logging.error(f"Ошибка при сохранении в файл {filename}: {e}")
        raise


if __name__ == "__main__":
    try:
        zabbix_hosts = get_hosts_from_zabbix()
        save_to_file(zabbix_hosts, "zabbix_hosts.json")
    except Exception as e:
        logging.critical(f"Скрипт завершился с ошибкой: {e}")
