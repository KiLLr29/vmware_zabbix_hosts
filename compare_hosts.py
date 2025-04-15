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


def find_missing_hosts(vcenter_vms, zabbix_hosts):
    """
    Сравнивает данные из VCenter и Zabbix и возвращает список хостов, которых нет в Zabbix.
    Применяет фильтрацию и нормализацию имен для корректного сравнения.
    Исключает хосты со статусом poweredOff.
    """
    missing_hosts = []

    # Регулярные выражения для фильтрации
    exclude_patterns = [
        r"_REP$",  # Хосты, заканчивающиеся на "_REP"
        r"^temp-",  # Хосты, начинающиеся на "temp-"
    ]

    for vm in vcenter_vms:
        vm_name = vm["host"]  # Имя хоста из VCenter
        vm_ip = vm["ip"]      # IP-адрес хоста из VCenter
        vm_status = vm["status"]  # Состояние питания хоста

        # Исключаем выключенные хосты
        if vm_status == "poweredOff":
            print(f"Пропущен выключенный хост: {vm_name}")
            continue

        # Проверяем, соответствует ли имя хоста фильтру исключения
        if any(re.search(pattern, vm_name) for pattern in exclude_patterns):
            continue  # Пропускаем хост, если он соответствует фильтру

        # Применяем нормализацию имени для сравнения
        normalized_name = normalize_hostname(vm_name)

        # Проверяем, есть ли хост с таким именем или IP в Zabbix
        if normalized_name not in zabbix_hosts and (not vm_ip or vm_ip not in [ip for ips in zabbix_hosts.values() for ip in ips]):
            missing_hosts.append({
                "host": vm_name,
                "ip": vm_ip
            })

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

    # Выводим результат в формате JSON
    print("Хосты, которых нет в Zabbix:")
    print(json.dumps(missing_hosts, indent=4, ensure_ascii=False))

    # Сохраняем результат сравнения в файл
    save_to_file(missing_hosts, "missing_hosts.json")