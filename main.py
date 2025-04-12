import atexit
import json
from pyVim.connect import SmartConnect, Disconnect
from pyVmomi import vim
import ssl
from pyzabbix import ZabbixAPI
from collections import defaultdict

# Импортируем настройки из файла config.py
from config import VCENTER_HOST, VCENTER_USER, VCENTER_PASSWORD, ZABBIX_URL, ZABBIX_USER, ZABBIX_PASSWORD


def get_vms_from_vcenter():
    """
    Получает список виртуальных машин и их IP-адресов из VCenter.
    """
    # Создаем контекст SSL для игнорирования ошибок сертификатов
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE

    try:
        # Подключаемся к VCenter
        si = SmartConnect(
            host=VCENTER_HOST,
            user=VCENTER_USER,
            pwd=VCENTER_PASSWORD,
            sslContext=context
        )
        atexit.register(Disconnect, si)
    except Exception as e:
        print(f"Не удалось подключиться к VCenter. Ошибка: {e}")
        return []

    # Получаем корневой объект
    content = si.RetrieveContent()
    container = content.viewManager.CreateContainerView(
        content.rootFolder, [vim.VirtualMachine], True
    )

    vms = []
    for vm in container.view:
        vm_name = vm.name
        vm_ip = None
        if vm.guest and vm.guest.ipAddress:
            vm_ip = vm.guest.ipAddress
        vms.append({"name": vm_name, "ip": vm_ip})

    return vms


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


def find_missing_hosts(vcenter_vms, zabbix_hosts):
    """
    Сравнивает данные из VCenter и Zabbix и возвращает список хостов, которых нет в Zabbix.
    """
    missing_hosts = []

    for vm in vcenter_vms:
        vm_name = vm["name"]
        vm_ip = vm["ip"]

        # Проверяем, есть ли хост с таким именем или IP в Zabbix
        if vm_name not in zabbix_hosts and (not vm_ip or vm_ip not in [ip for ips in zabbix_hosts.values() for ip in ips]):
            missing_hosts.append(vm)

    return missing_hosts


def save_to_file(data, filename):
    """
    Сохраняет данные в файл в формате JSON.
    """
    with open(filename, "w") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
    print(f"Данные успешно сохранены в файл: {filename}")


if __name__ == "__main__":
    # Получаем данные из VCenter
    vcenter_vms = get_vms_from_vcenter()
    save_to_file(vcenter_vms, "vcenter_vms.json")

    # Получаем данные из Zabbix
    zabbix_hosts = get_hosts_from_zabbix()
    save_to_file(zabbix_hosts, "zabbix_hosts.json")

    # Находим хосты, которых нет в Zabbix
    missing_hosts = find_missing_hosts(vcenter_vms, zabbix_hosts)

    # Выводим результат
    print("Хосты, которых нет в Zabbix:")
    for host in missing_hosts:
        print(f"Имя: {host['name']}, IP: {host['ip']}")

    # Сохраняем результат сравнения в файл
    save_to_file(missing_hosts, "missing_hosts.json")