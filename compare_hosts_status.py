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


def find_mismatched_hosts(vcenter_vms, zabbix_hosts):
    """
    Находит хосты с несоответствием статусов между VCenter и Zabbix.
    """
    mismatched_hosts = []  # Единый список для всех хостов с несоответствием

    for vm in vcenter_vms:
        vm_name = vm["host"]  # Полное имя хоста из VCenter
        vm_status = vm["status"]  # Состояние питания хоста в VCenter
        vm_ip = vm["ip"]  # IP-адрес хоста из VCenter

        # Применяем нормализацию имени для сравнения
        normalized_name = normalize_hostname(vm_name)

        # Проверяем, есть ли хост с таким именем в Zabbix
        if normalized_name in [host["host"] for host in zabbix_hosts]:
            # Находим хост в Zabbix по имени
            zabbix_host = next((host for host in zabbix_hosts if host["host"] == normalized_name), None)
            if zabbix_host:
                # Проверяем несоответствие статусов
                if (vm_status == "poweredOff" and zabbix_host["status"] == "enabled") or \
                   (vm_status == "poweredOn" and zabbix_host["status"] == "disabled"):
                    mismatched_hosts.append({
                        "host": normalized_name,  # Имя хоста из Zabbix
                        "ip": vm_ip,
                        "vmware_status": vm_status,  # Статус хоста в VCenter
                        "zabbix_status": zabbix_host["status"]  # Статус хоста в Zabbix
                    })

    return mismatched_hosts


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

    # Находим хосты с несоответствием статусов
    mismatched_hosts = find_mismatched_hosts(vcenter_vms, zabbix_hosts)

    # Выводим результат в консоль
    print("Хосты с несоответствием статусов между VCenter и Zabbix:")
    print(json.dumps(mismatched_hosts, indent=4, ensure_ascii=False))

    # Сохраняем результат в файл
    save_to_file(mismatched_hosts, "mismatched_hosts.json")