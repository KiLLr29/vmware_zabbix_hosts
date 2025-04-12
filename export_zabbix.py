import json
from pyzabbix import ZabbixAPI
from collections import defaultdict

# Импортируем настройки из файла config.py
from config import ZABBIX_URL, ZABBIX_USER, ZABBIX_PASSWORD


def get_hosts_from_zabbix():
    """
    Получает список хостов из Zabbix.
    """
    zapi = ZabbixAPI(ZABBIX_URL)
    zapi.login(ZABBIX_USER, ZABBIX_PASSWORD)

    # Получаем список хостов и их интерфейсов
    hosts = zapi.host.get(output=["host"], selectInterfaces=["ip"])
    zabbix_hosts = defaultdict(list)

    for host in hosts:
        hostname = host["host"]
        interfaces = host.get("interfaces", [])  # Используем .get() для безопасного доступа
        ip_addresses = [interface["ip"] for interface in interfaces if "ip" in interface]
        zabbix_hosts[hostname] = ip_addresses

    return zabbix_hosts


def save_to_file(data, filename):
    """
    Сохраняет данные в файл в формате JSON.
    """
    with open(filename, "w") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
    print(f"Данные успешно сохранены в файл: {filename}")


if __name__ == "__main__":
    # Получаем данные из Zabbix
    zabbix_hosts = get_hosts_from_zabbix()

    # Сохраняем данные в файл
    save_to_file(zabbix_hosts, "zabbix_hosts.json")