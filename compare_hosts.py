import json
import re

def load_from_file(filename):
    """
    Загружает данные из файла в формате JSON.
    """
    with open(filename, "r") as f:
        data = json.load(f)
    return data


def find_missing_hosts(vcenter_vms, zabbix_hosts):
    """
    Сравнивает данные из VCenter и Zabbix и возвращает список хостов, которых нет в Zabbix.
    Применяет фильтрацию для исключения ненужных хостов из VCenter.
    """
    missing_hosts = []

    # Регулярные выражения для фильтрации
    exclude_patterns = [
        r"_REP$",  # Хосты, заканчивающиеся на "_REP"
        r"^temp-",  # Хосты, начинающиеся на "temp-"
    ]

    for vm in vcenter_vms:
        vm_name = vm["name"]
        vm_ip = vm["ip"]

        # Проверяем, соответствует ли имя хоста фильтру исключения
        if any(re.search(pattern, vm_name) for pattern in exclude_patterns):
            continue  # Пропускаем хост, если он соответствует фильтру

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
    # Загружаем данные из файлов
    vcenter_vms = load_from_file("vcenter_vms.json")
    zabbix_hosts = load_from_file("zabbix_hosts.json")

    # Находим хосты, которых нет в Zabbix
    missing_hosts = find_missing_hosts(vcenter_vms, zabbix_hosts)

    # Выводим результат
    print("Хосты, которых нет в Zabbix:")
    for host in missing_hosts:
        print(f"Имя: {host['name']}, IP: {host['ip']}")

    # Сохраняем результат сравнения в файл
    save_to_file(missing_hosts, "missing_hosts.json")