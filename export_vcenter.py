import atexit
import json
import ssl
import logging
import os
from pyVim.connect import SmartConnect, Disconnect
from pyVmomi import vim

# Импорт настроек из config.py
from config import VCENTER_HOST, VCENTER_USER, VCENTER_PASSWORD

# Настройка логирования
log_dir = "/var/log/zabbix"
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, "zabbix_scripts_vcenter_vm_export.log")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)


def get_vms_from_vcenter():
    """
    Получает список виртуальных машин и их параметров из VCenter.
    Экспортирует данные в формате: host, status (poweredOn/poweredOff), ip.
    """
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE

    try:
        si = SmartConnect(
            host=VCENTER_HOST,
            user=VCENTER_USER,
            pwd=VCENTER_PASSWORD,
            sslContext=context
        )
        atexit.register(Disconnect, si)
        logging.info(f"Успешное подключение к VCenter: {VCENTER_HOST}")
    except Exception as e:
        logging.error(f"Не удалось подключиться к VCenter: {e}")
        return []

    vms = []
    try:
        content = si.RetrieveContent()
        container = content.viewManager.CreateContainerView(
            content.rootFolder, [vim.VirtualMachine], True
        )

        for vm in container.view:
            try:
                vm_name = vm.name
                vm_power_state = vm.runtime.powerState
                vm_ip = vm.guest.ipAddress if vm.guest and vm.guest.ipAddress else None

                vms.append({
                    "host": vm_name,
                    "status": vm_power_state,
                    "ip": vm_ip
                })

                logging.debug(f"VM: {vm_name}, status: {vm_power_state}, ip: {vm_ip}")
            except Exception as vm_err:
                logging.warning(f"Ошибка при обработке VM: {vm_err}")

        logging.info(f"Успешно получено {len(vms)} виртуальных машин.")
        return vms

    except Exception as e:
        logging.error(f"Ошибка при извлечении данных о VM: {e}")
        return []


def save_to_file(data, filename):
    """
    Сохраняет данные в файл в формате JSON.
    """
    try:
        with open(filename, "w") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        logging.info(f"Данные успешно сохранены в файл: {filename}")
    except Exception as e:
        logging.error(f"Ошибка при сохранении данных в файл: {e}")
        raise


if __name__ == "__main__":
    try:
        vcenter_vms = get_vms_from_vcenter()
        save_to_file(vcenter_vms, "vcenter_vms.json")
    except Exception as e:
        logging.critical(f"Критическая ошибка выполнения: {e}")
