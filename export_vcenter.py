import atexit
import json
from pyVim.connect import SmartConnect, Disconnect
from pyVmomi import vim
import ssl

# Импортируем настройки из файла config.py
from config import VCENTER_HOST, VCENTER_USER, VCENTER_PASSWORD


def get_vms_from_vcenter():
    """
    Получает список виртуальных машин и их IP-адресов из VCenter.
    Экспортирует только включенные хосты (poweredOn).
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
        vm_power_state = vm.runtime.powerState  # Состояние питания хоста
        vm_ip = None

        # Проверяем, что хост включен (poweredOn)
        if vm_power_state != "poweredOn":
            continue  # Пропускаем выключенные хосты

        # Получаем IP-адрес, если он доступен
        if vm.guest and vm.guest.ipAddress:
            vm_ip = vm.guest.ipAddress

        vms.append({"name": vm_name, "ip": vm_ip})

    return vms


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

    # Сохраняем данные в файл
    save_to_file(vcenter_vms, "vcenter_vms.json")