import json
import re

def load_from_file(filename):
    """
    Загружает данные из файла в формате JSON.
    """
    with open(filename, "r") as f:
        data = json.load(f)
    return data


def normalize_hostname(vcenter_name):
    """
    Нормализует имя хоста из VCenter для сравнения с именами в Zabbix.
    Например, преобразует 'VW-SWX002-a.miller' в 'SWX002'.
    """
    # Используем регулярное выражение для извлечения базового имени
    match = re.search(r"VW-(\w+)-", vcenter_name)
    if match:
        return match.group(1)  # Возвращаем часть, соответствующую шаблону
    return vcenter_name  # Если шаблон не найден, возвращаем исходное имя


def find_disabled_hosts_in_vmware_enabled_in_zabbix(vcenter_vms, zabbix_hosts):
    """
    Находит хосты, которые выключены в VCenter, но включены в Zabbix.
    """
    disabled_hosts = []

    for vm in vcenter_vms:
        vm_name = vm["host"]  # Имя хоста из VCenter
        vm_status = vm["status"]  # Состояние питания хоста в VCenter
        vm_ip = vm["ip"]  # IP-адрес хоста из VCenter

        # Применяем нормализацию имени для сравнения
        normalized_name = normalize_hostname(vm_name)

        # Проверяем, есть ли хост с таким именем в Zabbix
        if normalized_name in [host["host"] for host in zabbix_hosts]:
            # Находим хост в Zabbix по имени
            zabbix_host = next((host for host in zabbix_hosts if host["host"] == normalized_name), None)
            if zabbix_host and zabbix_host["status"] == "enabled" and vm_status == "poweredOff":
                disabled_hosts.append({
                    "host": vm_name,
                    "normalized_name": normalized_name,
                    "ip": vm_ip,
                    "vmware_status": vm_status,
                    "zabbix_status": zabbix_host["status"]
                })

    return disabled_hosts


def save_to_file(data, filename):
    """
    Сохраняет данные в файл в формате JSON.
    """
    with open(filename, "w") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
    print(f"Данные успешно сохранены в файл: {filename}")


if __name__ == "__main__":
    # Загружаем данные из файлов
    vcenter_vms = load_from_file("vcenter_vms.json")
    zabbix_hosts = load_from_file("zabbix_hosts.json")

    # Находим хосты, которые выключены в VCenter, но включены в Zabbix
    disabled_hosts = find_disabled_hosts_in_vmware_enabled_in_zabbix(vcenter_vms, zabbix_hosts)

    # Выводим результат в консоль
    print("Хосты, которые выключены в VCenter, но включены в Zabbix:")
    print(json.dumps(disabled_hosts, indent=4, ensure_ascii=False))

    # Сохраняем результат в файл
    save_to_file(disabled_hosts, "vmware_hosts_disabled.json")