import appleIcon from '../assets/brands/apple.svg'
import asusIcon from '../assets/brands/asus.svg'
import acerIcon from '../assets/brands/acer.svg'
import boseIcon from '../assets/brands/bose.svg'
import brotherIcon from '../assets/brands/brother.svg'
import canonIcon from '../assets/brands/canon.svg'
import dahuaIcon from '../assets/brands/dahua.svg'
import dellIcon from '../assets/brands/dell.svg'
import epsonIcon from '../assets/brands/epson.svg'
import hikvisionIcon from '../assets/brands/hikvision.svg'
import honorIcon from '../assets/brands/honor.svg'
import hpIcon from '../assets/brands/hp.svg'
import huaweiIcon from '../assets/brands/huawei.svg'
import iqooIcon from '../assets/brands/iqoo.svg'
import mideaIcon from '../assets/brands/midea.svg'
import mijiaIcon from '../assets/brands/mijia.svg'
import motorolaIcon from '../assets/brands/motorola.svg'
import msiIcon from '../assets/brands/msi.svg'
import netgearIcon from '../assets/brands/netgear.svg'
import oneplusIcon from '../assets/brands/oneplus.svg'
import pocoIcon from '../assets/brands/poco.svg'
import qnapIcon from '../assets/brands/qnap.svg'
import realmeIcon from '../assets/brands/realme.svg'
import redmiIcon from '../assets/brands/redmi.svg'
import rokuIcon from '../assets/brands/roku.svg'
import samsungIcon from '../assets/brands/samsung.svg'
import sonosIcon from '../assets/brands/sonos.svg'
import synologyIcon from '../assets/brands/synology.svg'
import tendaIcon from '../assets/brands/tenda.svg'
import thinkpadIcon from '../assets/brands/thinkpad.svg'
import tplinkIcon from '../assets/brands/tplink.svg'
import vivoIcon from '../assets/brands/vivo.svg'
import xiaomiIcon from '../assets/brands/xiaomi.svg'
import cameraDeviceIcon from '../assets/lan-icons/camera.svg'
import desktopDeviceIcon from '../assets/lan-icons/desktop.svg'
import deviceIcon from '../assets/lan-icons/device.svg'
import iotDeviceIcon from '../assets/lan-icons/iot.svg'
import laptopDeviceIcon from '../assets/lan-icons/laptop.svg'
import nasDeviceIcon from '../assets/lan-icons/nas.svg'
import phoneDeviceIcon from '../assets/lan-icons/phone.svg'
import printerDeviceIcon from '../assets/lan-icons/printer.svg'
import speakerDeviceIcon from '../assets/lan-icons/speaker.svg'
import tabletDeviceIcon from '../assets/lan-icons/tablet.svg'
import tvDeviceIcon from '../assets/lan-icons/tv.svg'

export const LAN_ICON_GROUPS = [
  { key: 'general', label: '通用' },
  { key: 'phone', label: '手机' },
  { key: 'computer', label: '电脑' },
  { key: 'network', label: '网络' },
  { key: 'storage', label: '存储' },
  { key: 'printer', label: '打印' },
  { key: 'camera', label: '安防' },
  { key: 'media', label: '影音' },
  { key: 'home', label: '家电' },
]

export const LAN_DEVICE_ICONS = [
  { key: 'device', src: deviceIcon, label: '设备', type: 'image', group: 'general' },
  { key: 'phone', src: phoneDeviceIcon, label: '手机', type: 'image', group: 'general' },
  { key: 'tablet', src: tabletDeviceIcon, label: '平板', type: 'image', group: 'general' },
  { key: 'desktop', src: desktopDeviceIcon, label: '电脑', type: 'image', group: 'general' },
  { key: 'laptop', src: laptopDeviceIcon, label: '笔记本', type: 'image', group: 'general' },
  { key: 'tv', src: tvDeviceIcon, label: '电视盒', type: 'image', group: 'general' },
  { key: 'camera', src: cameraDeviceIcon, label: '摄像头', type: 'image', group: 'general' },
  { key: 'printer', src: printerDeviceIcon, label: '打印机', type: 'image', group: 'general' },
  { key: 'speaker', src: speakerDeviceIcon, label: '音箱', type: 'image', group: 'general' },
  { key: 'nas', src: nasDeviceIcon, label: '存储', type: 'image', group: 'general' },
  { key: 'iot', src: iotDeviceIcon, label: '智能家居', type: 'image', group: 'general' },
  { key: 'brand-apple', src: appleIcon, label: 'Apple', type: 'image', group: 'phone' },
  { key: 'brand-xiaomi', src: xiaomiIcon, label: '小米', type: 'image', group: 'phone' },
  { key: 'brand-redmi', src: redmiIcon, label: 'Redmi', type: 'image', group: 'phone' },
  { key: 'brand-poco', src: pocoIcon, label: 'POCO', type: 'image', group: 'phone' },
  { key: 'brand-mijia', src: mijiaIcon, label: '米家', type: 'image', group: 'home' },
  { key: 'brand-huawei', src: huaweiIcon, label: '华为', type: 'image', group: 'phone' },
  { key: 'brand-honor', src: honorIcon, label: '荣耀', type: 'image', group: 'phone' },
  { key: 'brand-samsung', src: samsungIcon, label: 'Samsung', type: 'image', group: 'phone' },
  { key: 'brand-realme', src: realmeIcon, label: 'realme', type: 'image', group: 'phone' },
  { key: 'brand-iqoo', src: iqooIcon, label: 'iQOO', type: 'image', group: 'phone' },
  { key: 'brand-motorola', src: motorolaIcon, label: 'Motorola', type: 'image', group: 'phone' },
  { key: 'brand-tplink', src: tplinkIcon, label: 'TP-Link', type: 'image', group: 'network' },
  { key: 'brand-tenda', src: tendaIcon, label: 'Tenda', type: 'image', group: 'network' },
  { key: 'brand-asus', src: asusIcon, label: '华硕', type: 'image', group: 'computer' },
  { key: 'brand-thinkpad', src: thinkpadIcon, label: 'ThinkPad', type: 'image', group: 'computer' },
  { key: 'brand-dell', src: dellIcon, label: 'Dell', type: 'image', group: 'computer' },
  { key: 'brand-hp', src: hpIcon, label: 'HP', type: 'image', group: 'computer' },
  { key: 'brand-acer', src: acerIcon, label: 'Acer', type: 'image', group: 'computer' },
  { key: 'brand-msi', src: msiIcon, label: 'MSI', type: 'image', group: 'computer' },
  { key: 'brand-netgear', src: netgearIcon, label: 'NETGEAR', type: 'image', group: 'network' },
  { key: 'brand-synology', src: synologyIcon, label: 'Synology', type: 'image', group: 'storage' },
  { key: 'brand-qnap', src: qnapIcon, label: 'QNAP', type: 'image', group: 'storage' },
  { key: 'brand-epson', src: epsonIcon, label: 'Epson', type: 'image', group: 'printer' },
  { key: 'brand-canon', src: canonIcon, label: 'Canon', type: 'image', group: 'printer' },
  { key: 'brand-brother', src: brotherIcon, label: 'Brother', type: 'image', group: 'printer' },
  { key: 'brand-hikvision', src: hikvisionIcon, label: 'Hikvision', type: 'image', group: 'camera' },
  { key: 'brand-dahua', src: dahuaIcon, label: 'Dahua', type: 'image', group: 'camera' },
  { key: 'brand-roku', src: rokuIcon, label: 'Roku', type: 'image', group: 'media' },
  { key: 'brand-sonos', src: sonosIcon, label: 'Sonos', type: 'image', group: 'media' },
  { key: 'brand-bose', src: boseIcon, label: 'Bose', type: 'image', group: 'media' },
  { key: 'brand-vivo', src: vivoIcon, label: 'vivo', type: 'image', group: 'phone' },
  { key: 'brand-oneplus', src: oneplusIcon, label: 'OnePlus', type: 'image', group: 'phone' },
  { key: 'brand-midea', src: mideaIcon, label: '美的', type: 'image', group: 'home' },
]

const lanIconMap = Object.fromEntries(LAN_DEVICE_ICONS.map(item => [item.key, item]))

export function getLanDeviceIcon(device) {
  return getLanDeviceIconInfo(device).icon || lanIconMap.device.icon
}

export function getLanDeviceDisplayName(device) {
  return device?.custom_name || device?.display_name || device?.hostname || device?.ip || '未知设备'
}

export function getLanDeviceIconInfo(device) {
  if (device?.custom_icon) {
    return { key: 'custom', src: device.custom_icon, label: '自定义', type: 'image' }
  }
  const key = typeof device === 'string' ? device : device?.icon || 'device'
  return lanIconMap[key] || lanIconMap.device
}

export function getLanDeviceIconLabel(key) {
  return lanIconMap[key]?.label || lanIconMap.device.label
}
