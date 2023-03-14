from prometheus_client import Gauge, Info
from prometheus_client import REGISTRY

registry = REGISTRY

#hpilo_ip_address = Info('hpilo_ip_address', 'HP iLO IP address', ["product_name", "server_name"])
#hpilo_firmware_version = Info('hpilo_firmware_version', 'HP iLO firmware version', ["product_name", "server_name"])

axis_temp_gauge = Gauge('axis_temp', 'Axis Communications camera temperature reading', ["product_name", "node", "sensor_name"])
axis_heater_status = Gauge('axis_heater_status', 'Axis Communications camera heater status: 0=stopped, 1=running, 2=failed', ["product_name", "node", "heater_id"])
axis_heater_timer = Gauge('axis_heater_timer', 'Axis Communications camera heater time until stop', ["product_name", "node", "heater_id"])

infos = {
#    'hpilo_ip_address': hpilo_ip_address,
#    'hpilo_firmware_version': hpilo_firmware_version,
}

gauges = {
    'axis_temp_gauge': axis_temp_gauge,
    'axis_heater_status': axis_heater_status,
    'axis_heater_timer': axis_heater_timer,
}
