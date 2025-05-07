import json
import re
import os
import logging

# Настройка логирования
log_dir = "./logs"
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, "zabbix_missing_hosts.log")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)


def load_from_file(filename):
    """
    Загружает данные из файла в формате JSON.
    """
    try:
        with open(filename, "r") as f:
            data = json.load(f)
        logging.info(f"Файл успешно загружен: {filename}")
        return data
    except Exception as e:
        logging.error(f"Ошибка при загрузке файла {filename}: {e}")
        raise


def normalize_hostname(vcenter_name):
    """
    Нормализует имя хоста из VCenter для сравнения с именами в Zabbix.
    Например, преобразует 'VW-SWX002-a.miller' в 'SWX002'.
    """
    match = re.search(r"VW-(\w+)-", vcenter_name)
    if match:
        normalized = match.group(1)
        logging.debug(f"Нормализовано имя '{vcenter_name}' → '{normalized}'")
        return normalized
    logging.debug(f"Имя без нормализации: {vcenter_name}")
    return vcenter_name


def find_missing_hosts(vcenter_vms, zabbix_hosts_dict):
    """
    Сравнивает данные из VCenter и Zabbix и возвращает список хостов, которых нет в Zabbix.
    Исключает poweredOff и фильтруемые по имени.
    """
    missing_hosts = []

    exclude_patterns = [
        r"_REP$", r"^temp-", r"^Temp"
    ]

    all_zabbix_ips = {ip for ip_list in zabbix_hosts_dict.values() for ip in ip_list}
    known_hosts = set(zabbix_hosts_dict.keys())

    for vm in vcenter_vms:
        vm_name = vm.get("host")
        vm_ip = vm.get("ip")
        vm_status = vm.get("status")

        if not vm_name or not vm_status:
            logging.warning(f"Пропущена VM из-за неполных данных: {vm}")
            continue

        if vm_status == "poweredOff":
            logging.info(f"Пропущен выключенный хост: {vm_name}")
            continue

        if any(re.search(pattern, vm_name) for pattern in exclude_patterns):
            logging.info(f"Хост исключён по шаблону: {vm_name}")
            continue

        normalized_name = normalize_hostname(vm_name)

        if normalized_name not in known_hosts and (not vm_ip or vm_ip not in all_zabbix_ips):
            missing_hosts.append({
                "host": vm_name,
                "ip": vm_ip
            })
            logging.info(f"Найден отсутствующий хост: {vm_name} ({vm_ip})")

    logging.info(f"Всего отсутствующих хостов: {len(missing_hosts)}")
    return missing_hosts


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
        vcenter_vms = load_from_file("vcenter_vms.json")
        zabbix_hosts_list = load_from_file("zabbix_hosts.json")

        # Преобразуем список Zabbix-хостов в словарь: host → [ip]
        zabbix_hosts = {
            host["host"]: [host["ip"]] if host.get("ip") else []
            for host in zabbix_hosts_list if "host" in host
        }

        missing_hosts = find_missing_hosts(vcenter_vms, zabbix_hosts)

        print("Хосты, которых нет в Zabbix:")
        print(json.dumps(missing_hosts, indent=4, ensure_ascii=False))

        save_to_file(missing_hosts, "missing_hosts.json")

    except Exception as e:
        logging.critical(f"Скрипт завершился с ошибкой: {e}")
