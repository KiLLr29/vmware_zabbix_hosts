import json
import re
import logging
import os

# Создание директории для логов в локальной папке
log_dir = "/var/log/zabbix"
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, "zabbix_scripts_zabbix_vm_sync.log")

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler(log_file), logging.StreamHandler()]
)


def load_from_file(filename):
    try:
        with open(filename, "r") as f:
            data = json.load(f)
        logging.info(f"Файл успешно загружен: {filename}")
        return data
    except Exception as e:
        logging.error(f"Ошибка при загрузке файла {filename}: {e}")
        raise


def normalize_hostname(vcenter_name):
    match = re.search(r"VW-(\w+)-", vcenter_name)
    if match:
        normalized = match.group(1)
        logging.debug(f"Нормализовано имя '{vcenter_name}' → '{normalized}'")
        return normalized
    logging.debug(f"Имя без нормализации: {vcenter_name}")
    return vcenter_name


def find_mismatched_hosts(vcenter_vms, zabbix_hosts):
    mismatched_hosts = []
    zabbix_index = {host["host"]: host for host in zabbix_hosts}

    for vm in vcenter_vms:
        vm_name = vm.get("host")
        vm_status = vm.get("status")
        vm_ip = vm.get("ip") if "ip" in vm else None

        # Не исключаем из-за отсутствия IP!
        if not vm_name or not vm_status:
            continue  # Без логирования

        normalized_name = normalize_hostname(vm_name)

        if normalized_name in zabbix_index:
            zabbix_host = zabbix_index[normalized_name]
            z_status = zabbix_host.get("status")

            if (vm_status == "poweredOff" and z_status == "enabled") or \
               (vm_status == "poweredOn" and z_status == "disabled"):

                mismatched_hosts.append({
                    "host": normalized_name,
                    "ip": vm_ip if vm_ip else "нет IP",
                    "vmware_status": vm_status,
                    "zabbix_status": z_status
                })
    logging.info(f"Обнаружено {len(mismatched_hosts)} хостов с несоответствием статусов.")
    return mismatched_hosts


def save_to_file(data, filename):
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
        zabbix_hosts = load_from_file("zabbix_hosts.json")

        mismatched_hosts = find_mismatched_hosts(vcenter_vms, zabbix_hosts)

        print("Хосты с несоответствием статусов между VCenter и Zabbix:")
        print(json.dumps(mismatched_hosts, indent=4, ensure_ascii=False))

        save_to_file(mismatched_hosts, "mismatched_hosts.json")

    except Exception as e:
        logging.error(f"Произошла критическая ошибка выполнения: {e}")
