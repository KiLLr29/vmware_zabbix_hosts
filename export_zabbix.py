import json
from pyzabbix import ZabbixAPI
from collections import defaultdict

# Импортируем настройки из файла config.py
from config import ZABBIX_URL, ZABBIX_USER, ZABBIX_PASSWORD


def get_hosts_from_zabbix():
    """
    Получает список хостов из Zabbix.
    Экспортирует данные в формате: host, status (enabled/disabled), ip.
    """
    zapi = ZabbixAPI(ZABBIX_URL)
    zapi.login(ZABBIX_USER, ZABBIX_PASSWORD)

    # Получаем список хостов и их интерфейсов
    hosts = zapi.host.get(output=["host", "status"], selectInterfaces=["ip"])
    zabbix_hosts = []

    for host in hosts:
        hostname = host["host"]
        host_status = "enabled" if host["status"] == "0" else "disabled"
        interfaces = host.get("interfaces", [])  # Используем .get() для безопасного доступа
        ip_addresses = [interface["ip"] for interface in interfaces if "ip" in interface]

        # Формируем объект с данными хоста
        zabbix_hosts.append({
            "host": hostname,
            "status": host_status,
            "ip": ip_addresses[0] if ip_addresses else None  # Берем первый IP, если он есть
        })

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